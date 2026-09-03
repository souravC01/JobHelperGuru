import json
import re
from typing import List, Optional, Dict, Any
from openai import OpenAI

from backend.models import (
    JobAnalysisResult,
    Resume,
    RankedResume,
    ResumeMatchResult,
    ClaimStatus,
    BulletAlternative,
    BulletOptimizationRequest,
    BulletOptimizationResponse,
    OutreachResponse,
)
from backend.services.heuristic_parser import HeuristicParser, filter_skills


def extract_json_from_llm_response(text: str) -> Any:
    """Robustly extracts JSON from an LLM response, stripping reasoning tags (<think>...</think>) and code fences."""
    # 1. Remove <think>...</think> reasoning tags
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL).strip()

    # 2. Extract ```json ... ``` markdown codeblocks
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 3. Extract outermost JSON object or array
    brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(1).strip())
        except Exception:
            pass

    # 4. Fallback directly to json.loads
    clean_text = re.sub(r"^```json\s*", "", text)
    clean_text = re.sub(r"^```\s*", "", clean_text)
    clean_text = re.sub(r"\s*```$", "", clean_text)
    return json.loads(clean_text)


class AIEngine:
    def __init__(
        self,
        api_base_url: str = "https://integrate.api.nvidia.com/v1",
        api_key: Optional[str] = None,
        model_name: str = "nvidia/nemotron-4-340b-instruct",
    ):
        self.api_base_url = api_base_url or "https://integrate.api.nvidia.com/v1"
        self.api_key = api_key if (api_key and api_key.strip()) else None
        self.model_name = model_name or "nvidia/nemotron-4-340b-instruct"
        self.heuristic = HeuristicParser()

    def _get_client(self) -> Optional[OpenAI]:
        if not self.api_key or not self.api_key.strip() or self.model_name in ["offline-heuristic", "offline"]:
            return None
        try:
            return OpenAI(base_url=self.api_base_url, api_key=self.api_key, timeout=30.0)
        except Exception as e:
            raise RuntimeError(f"Could not initialize AI Client for {self.model_name}: {str(e)}") from e

    # --- 1. Job Analysis ---
    def analyze_job(self, text: str, source_url: str = "") -> JobAnalysisResult:
        client = self._get_client()
        if client:
            try:
                system_prompt = """
You are an expert ATS and technical recruiter parser.
Extract all key details from the following job description and return strict, valid JSON with this exact schema:
{
  "company": "Company Name",
  "title": "Exact Role Title",
  "location": "City, State or Remote/Hybrid",
  "work_mode": "Remote" | "Hybrid" | "Onsite" | "Unknown",
  "salary_range": "e.g. $120k - $150k or Not specified",
  "experience_level": "Entry" | "Mid" | "Senior" | "Lead",
  "required_skills": ["Must have skills"],
  "preferred_skills": ["Nice to have skills"],
  "tech_stack": ["Languages, frameworks, clouds, databases"],
  "soft_skills": ["Communication, mentorship, etc"],
  "ats_keywords": ["Top 15-20 crucial ATS resume keywords"],
  "summary": "2-3 sentence executive summary of the role"
}
Do not wrap in markdown quotes. Return only raw JSON.
"""
                resp = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Source URL: {source_url}\n\nJob Description:\n{text[:6000]}"},
                    ],
                    temperature=0.1,
                )
                raw_content = resp.choices[0].message.content.strip()
                data = extract_json_from_llm_response(raw_content)
                # Sanitize skills from non-skills (e.g. New Grad, Degree, etc.)
                data["required_skills"] = filter_skills(data.get("required_skills", []))
                data["preferred_skills"] = filter_skills(data.get("preferred_skills", []))
                data["tech_stack"] = filter_skills(data.get("tech_stack", []))
                data["ats_keywords"] = filter_skills(data.get("ats_keywords", []))

                is_ng = bool(re.search(r"\b(new grad|new graduate|recent grad|recent graduate|university graduate|class of (?:20\d{2})|fresh graduate)\b", text, re.I))
                data["is_new_grad_role"] = data.get("is_new_grad_role", is_ng)
                if data["is_new_grad_role"]:
                    data["new_grad_criteria"] = "Graduating in the next 4 months or graduated within the last 6 months"

                return JobAnalysisResult(**data)
            except Exception as e:
                # Do NOT automatically fallback when user explicitly configured an API key!
                raise RuntimeError(f"AI API Provider Failed ({self.model_name}): {str(e)}") from e

        # Heuristic fallback
        return self.heuristic.analyze_job_text(text)

    # --- 2. Multi-Resume Fit Ranking ---
    def rank_resumes(self, resumes: List[Resume], job: JobAnalysisResult) -> List[RankedResume]:
        if not resumes:
            return []

        client = self._get_client()
        ranked_list: List[RankedResume] = []

        if client and len(resumes) > 0:
            try:
                system_prompt = """
You are an expert technical recruiter and ATS matcher.
Given a target job and multiple candidate resumes, evaluate each resume's fit.
Score each resume from 0 to 100 based on required skills and ATS keywords.
Identify matched keywords, missing keywords, and provide a 2-sentence rationale for the fit score.
CRITICAL: Do NOT list 'New Grad', 'Recent Graduate', 'Degree', or career stages as missing keywords. Focus only on technical tools, frameworks, and architecture.
Return strict JSON:
[
  {
    "resume_id": "id",
    "match_score": 85,
    "matched_keywords": ["Python", "AWS"],
    "missing_keywords": ["Kafka"],
    "fit_summary": "Strong backend alignment..."
  }
]
"""
                resumes_payload = [
                    {"resume_id": r.id, "resume_name": r.name, "content": r.content[:3000]}
                    for r in resumes
                ]
                job_payload = {
                    "title": job.title,
                    "company": job.company,
                    "required_skills": job.required_skills,
                    "ats_keywords": job.ats_keywords[:15],
                    "tech_stack": job.tech_stack[:15],
                }
                resp = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Target Job:\n{json.dumps(job_payload)}\n\nResumes:\n{json.dumps(resumes_payload)}"},
                    ],
                    temperature=0.2,
                )
                raw_content = resp.choices[0].message.content.strip()
                ai_evals = extract_json_from_llm_response(raw_content)

                eval_map = {item["resume_id"]: item for item in ai_evals}
                for r in resumes:
                    ev = eval_map.get(r.id, {})
                    eligibility = self.heuristic.check_new_grad_eligibility(r.content)
                    matched_kws = filter_skills(ev.get("matched_keywords", []))
                    missing_kws = filter_skills(ev.get("missing_keywords", []))

                    ranked_list.append(
                        RankedResume(
                            resume_id=r.id,
                            resume_name=r.name,
                            match_score=ev.get("match_score", 50),
                            matched_keywords=matched_kws,
                            missing_keywords=missing_kws,
                            fit_summary=ev.get("fit_summary", ""),
                            is_best_fit=False,
                            is_new_grad_role=job.is_new_grad_role,
                            new_grad_eligible=eligibility["eligible"] if job.is_new_grad_role else None,
                            graduation_status=eligibility["status"],
                            graduation_date=eligibility["grad_date"],
                        )
                    )
            except Exception as e:
                raise RuntimeError(f"AI API Provider Failed ({self.model_name}): {str(e)}") from e

        if not ranked_list:
            # Heuristic ranking
            for r in resumes:
                m = self.heuristic.match_resume(r.content, job)
                ranked_list.append(
                    RankedResume(
                        resume_id=r.id,
                        resume_name=r.name,
                        match_score=m.match_score,
                        matched_keywords=m.matched_keywords,
                        missing_keywords=m.missing_keywords,
                        fit_summary=m.fit_summary,
                        is_best_fit=False,
                        is_new_grad_role=m.is_new_grad_role,
                        new_grad_eligible=m.new_grad_eligible,
                        graduation_status=m.graduation_status,
                        graduation_date=m.graduation_date,
                    )
                )

        # Sort descending by match score
        ranked_list.sort(key=lambda x: x.match_score, reverse=True)
        if ranked_list:
            ranked_list[0].is_best_fit = True

        return ranked_list

    # --- 3. Bulletskill.md Optimizer ---
    @staticmethod
    def _parse_classified_bullets(raw_text: str) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Intelligently parses resume text into (project_bullets, work_bullets).
        Handles unicode bullets (●, •, ◦, etc.), multi-line wrapped text, and classifies
        projects vs work history sections even without explicit 'Projects' headers.
        """
        normalized = re.sub(r'[\u25cf\u25cb\u25e6\u2043\u2219\u25aa\u25ab\u2022\u2023\u25b6\u25ba\u2192]', '• ', raw_text)
        
        sections = []
        curr_sec_name = 'General Experience'
        current_bullets = []
        current_bullet_text = []

        lines = [l.strip() for l in normalized.splitlines() if l.strip()]
        for line in lines:
            is_bullet_start = bool(re.match(r'^(?:[•*–]|-(?=\s)|\d+\.)\s*', line))
            
            is_known_header = any(h in line.lower() for h in ['education & certificates', 'education', 'work history', 'professional experience', 'experience', 'projects', 'skills', 'certif']) and len(line) < 60 and not is_bullet_start
            has_tech_stack_or_dash = ((' - ' in line or ' – ' in line or ' | ' in line) and any(t in line.lower() for t in ['java', 'python', 'react', 'spring', 'docker', 'cloud', 'sql', 'aws', 'c++', 'javascript', 'simulator', 'platform', 'app', 'developer', 'engineer', 'analyst'])) and len(line) < 140 and not is_bullet_start
            has_job_pattern = (bool(re.search(r'\b(at|@)\b.*(?:19|20)\d{2}', line, re.IGNORECASE)) or bool(re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?:19|20)\d{2}', line))) and not is_bullet_start
            
            is_title = (is_known_header or has_tech_stack_or_dash or has_job_pattern) and not is_bullet_start
            if is_title:
                if current_bullet_text:
                    current_bullets.append(' '.join(current_bullet_text))
                    current_bullet_text = []
                if current_bullets:
                    sections.append((curr_sec_name, current_bullets))
                    current_bullets = []
                curr_sec_name = line
            elif is_bullet_start:
                if current_bullet_text:
                    current_bullets.append(' '.join(current_bullet_text))
                    current_bullet_text = []
                clean_b = re.sub(r'^(?:[•*–]|-(?=\s)|\d+\.)\s*', '', line).strip()
                current_bullet_text.append(clean_b)
            else:
                if current_bullet_text:
                    current_bullet_text.append(line)
                elif len(line) < 80:
                    curr_sec_name = line

        if current_bullet_text:
            current_bullets.append(' '.join(current_bullet_text))
        if current_bullets:
            sections.append((curr_sec_name, current_bullets))

        project_bullets = []
        work_bullets = []

        for s_name, b_list in sections:
            low_name = s_name.lower().strip()
            # Skip education section
            if low_name in ['education', 'education & certificates', 'academic background', 'education and coursework', 'certificates']:
                continue
                
            is_work = (
                bool(re.search(r'\b(at|@)\b', low_name)) or
                any(w in low_name for w in ['co-op', 'intern', 'employment', 'experience', 'company', 'developer at', 'analyst at', 'engineer at']) or
                bool(re.search(r'(?:19|20)\d{2}', s_name))
            )
            is_project = (
                any(p in low_name for p in ['project', 'simulator', 'platform', 'marketplace', 'app', 'system', 'tool', 'portal']) or
                (not is_work and any(tech in low_name for tech in ['java', 'python', 'react', 'spring', 'docker', 'cloud', 'sql', 'aws', 'api']))
            )

            for b in b_list:
                item = {'section': s_name, 'bullet': b}
                if is_project and not is_work:
                    project_bullets.append(item)
                elif is_work:
                    work_bullets.append(item)
                else:
                    if any(p in b.lower() for p in ['project', 'built', 'created', 'designed']):
                        project_bullets.append(item)
                    else:
                        work_bullets.append(item)

        return project_bullets, work_bullets

    def optimize_bullet(self, request: BulletOptimizationRequest) -> BulletOptimizationResponse:
        """
        Implements Bulletskill.md framework:
        What / Keyword + HOW it was used + RESULT and/or REASON
        Claim status taxonomy:
        - VERIFIED: User evidence supports the claim
        - UNVERIFIED_SKILL: Missing job keyword suggested with assumption & confirmation gate
        - UNVERIFIED_METRIC: Metric placeholder like [X%], never fake numbers
        Produces 3 alternatives for the same selected bullet:
        - Candidate A (ATS-focused)
        - Candidate B (Concise)
        - Candidate C (Technical/result-focused)
        """
        # Determine claim verification status from evidence context
        evidence_blob = " ".join(request.evidence_context).lower()
        existing_blob = request.existing_bullet.lower()
        # 1. Collect keywords
        keywords = [k.strip() for k in request.target_keywords if k and k.strip()]
        if not keywords and request.target_keyword and request.target_keyword.strip():
            keywords = [request.target_keyword.strip()]
        if not keywords:
            keywords = ["Key Technology"]

        primary_kw = ", ".join(keywords)

        # Check evidence for verification
        evidence_blob = " ".join(request.evidence_context).lower()
        existing_blob = request.existing_bullet.lower() if request.existing_bullet else ""

        unverified_kws = []
        for kw in keywords:
            if not (
                re.search(rf"\b{re.escape(kw.lower())}\b", evidence_blob)
                or re.search(rf"\b{re.escape(kw.lower())}\b", existing_blob)
            ):
                unverified_kws.append(kw)

        is_verified = len(unverified_kws) == 0
        claim_status = ClaimStatus.VERIFIED if is_verified else ClaimStatus.UNVERIFIED_SKILL
        requires_confirmation = not is_verified
        warning = None
        assumption = None

        if not is_verified:
            missing_str = ", ".join(unverified_kws)
            warning = f"Confirm that you actually utilized {missing_str} before adding this bullet to your resume."
            assumption = f"The candidate utilized {missing_str} in this {request.section_type}."

        # Separate candidate resume bullets into Projects vs Work History using smart classifier
        raw_evidence = "\n".join(request.evidence_context)
        project_bullets, work_bullets = self._parse_classified_bullets(raw_evidence)

        is_project = (request.section_type == "project")
        target_section_bullets = project_bullets if is_project else work_bullets

        client = self._get_client()
        if client:
            try:
                section_instructions = (
                    "CRITICAL REQUIREMENT: The user specifically requested a PROJECT bullet point.\n"
                    "You MUST ONLY select an existing PROJECT from the Candidate's Projects section to modify/replace.\n"
                    "DO NOT select a job, employment, or work history bullet point!\n"
                    "If the candidate's resume does not list any projects, set target_project_name='Recommended New Project: Cloud Architecture Project' and original_bullet_to_replace='Add as a new bullet point under your Projects section.'"
                    if is_project
                    else
                    "CRITICAL REQUIREMENT: The user specifically requested a WORK HISTORY bullet point.\n"
                    "You MUST ONLY select a professional employment or role entry from the Candidate's Work Experience to modify/replace.\n"
                    "DO NOT select a personal or academic project!"
                )

                system_prompt = f"""
You are the BulletSkill optimizer strictly following Resume Guide 2.0.
Core Framework: WHAT/Keywords + HOW it was used + RESULT and/or REASON.
Rules:
- Write in past tense.
- One sentence only, no more than 1 period per bullet.
- Target ~3 lines maximum.
- Section type is "{request.section_type}". If "project", frame as a technical engineering project highlighting how these technologies work together. If "work_history", frame as production employment achievements.
- Incorporate ALL requested target keywords naturally: {primary_kw}
- Do NOT fabricate fake numbers (use placeholders like [X%], [N users] if metric is suggested).
- {section_instructions}
Return strict JSON with this exact schema:
{{
  "status": "rewritten",
  "target_keyword": "{primary_kw}",
  "claim_status": "{claim_status.value}",
  "target_project_name": "Exact or identified { 'project' if is_project else 'job role/company' } name from resume",
  "original_bullet_to_replace": "The exact existing bullet point in that { 'project' if is_project else 'job role' } that should be replaced or augmented with these skills. If no existing bullet fits, output 'Add as a new bullet point under this section.'",
  "replacement_rationale": "1-2 sentence explanation of why replacing/enhancing this specific bullet point maximizes the candidate's ATS match and technical impact.",
  "alternatives": [
    {{
      "variant_name": "Candidate A (ATS-focused)",
      "bullet": "...",
      "what": "{primary_kw}",
      "how": "...",
      "result_or_reason": "...",
      "claim_status": "{claim_status.value}",
      "requires_confirmation": {str(requires_confirmation).lower()},
      "assumption": "{assumption or ''}"
    }},
    {{
      "variant_name": "Candidate B (Concise)",
      "bullet": "...",
      "what": "{primary_kw}",
      "how": "...",
      "result_or_reason": "...",
      "claim_status": "{claim_status.value}",
      "requires_confirmation": {str(requires_confirmation).lower()},
      "assumption": "{assumption or ''}"
    }},
    {{
      "variant_name": "Candidate C (Technical/result-focused)",
      "bullet": "...",
      "what": "{primary_kw}",
      "how": "...",
      "result_or_reason": "...",
      "claim_status": "{claim_status.value}",
      "requires_confirmation": {str(requires_confirmation).lower()},
      "assumption": "{assumption or ''}"
    }}
  ],
  "validation": {{
    "past_tense": true,
    "one_sentence": true,
    "one_period_max": true,
    "what_how_result_present": true,
    "keyword_stuffing": false
  }}
}}
"""
                bullets_context_str = json.dumps(target_section_bullets if target_section_bullets else [{"section": "None", "bullet": "No existing section found"}])
                user_msg = f"""
Target Job Title: {request.target_job_title}
Section Type: {request.section_type}
Target Keywords: {primary_kw}
Existing Bullet (if user pre-selected one): {request.existing_bullet or 'Auto-detect best bullet to replace from Candidate ' + ('Projects' if is_project else 'Work History')}
Candidate { 'Projects' if is_project else 'Work History' } Bullets:
{bullets_context_str}
Candidate Full Resume Context:
{raw_evidence[:2500]}
Claim Status: {claim_status.value}
"""
                resp = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.3,
                )
                raw_content = resp.choices[0].message.content.strip()
                data = extract_json_from_llm_response(raw_content)

                def_proj = target_section_bullets[0]["section"] if target_section_bullets else (f"Recommended New {'Project' if is_project else 'Role'}: {request.target_job_title}")
                def_bullet = target_section_bullets[0]["bullet"] if target_section_bullets else f"Add as a new bullet point under your {'Projects' if is_project else 'Work History'} section."

                return BulletOptimizationResponse(
                    status="rewritten" if is_verified else "suggested",
                    target_keyword=primary_kw,
                    target_keywords=keywords,
                    claim_status=claim_status,
                    selected_bullet_index=0,
                    alternatives=[BulletAlternative(**alt) for alt in data.get("alternatives", [])],
                    requires_confirmation=requires_confirmation,
                    warning=warning,
                    validation=data.get("validation", {}),
                    target_project_name=data.get("target_project_name") or def_proj,
                    original_bullet_to_replace=data.get("original_bullet_to_replace") or def_bullet,
                    replacement_rationale=data.get("replacement_rationale") or f"Upgrading this bullet incorporates {primary_kw} where core architecture is evaluated.",
                    available_resume_bullets=target_section_bullets,
                )
            except Exception as e:
                raise RuntimeError(f"AI API Provider Failed ({self.model_name}): {str(e)}") from e

        # Offline template generation following Bulletskill.md
        kw = primary_kw
        if is_project:
            alt_a = BulletAlternative(
                variant_name="Candidate A (ATS-focused)",
                bullet=f"Developed an engineering project integrating {kw} with modular service architecture to streamline system workflows and elevate data processing throughput.",
                what=kw,
                how=f"Developed an engineering project integrating {kw} with modular service architecture",
                result_or_reason="Streamline system workflows and elevate data processing throughput",
                claim_status=claim_status,
                requires_confirmation=requires_confirmation,
                assumption=assumption,
            )

            alt_b = BulletAlternative(
                variant_name="Candidate B (Concise)",
                bullet=f"Built a technical application utilizing {kw} to automate core operations, eliminating latency and reducing deployment turnaround.",
                what=kw,
                how=f"Built a technical application utilizing {kw} to automate operations",
                result_or_reason="Eliminating latency and reducing turnaround",
                claim_status=claim_status,
                requires_confirmation=requires_confirmation,
                assumption=assumption,
            )

            alt_c = BulletAlternative(
                variant_name="Candidate C (Technical/result-focused)",
                bullet=f"Architected an end-to-end service pipeline powered by {kw}, reducing execution latency by [X%] and achieving 99.9% pipeline reliability.",
                what=kw,
                how=f"Architected an end-to-end service pipeline powered by {kw}",
                result_or_reason="Reducing execution latency by [X%] and achieving 99.9% reliability",
                claim_status=ClaimStatus.UNVERIFIED_METRIC if is_verified else claim_status,
                requires_confirmation=True,
                assumption="Requires user to supply supported metric for [X%]",
            )

            if project_bullets:
                fallback_proj = project_bullets[0]["section"]
                fallback_bullet = request.existing_bullet if request.existing_bullet else project_bullets[0]["bullet"]
                fallback_rationale = f"Upgrading this project bullet directly incorporates {kw} into your technical projects portfolio."
            else:
                fallback_proj = f"Recommended Project: {request.target_job_title} Application"
                fallback_bullet = request.existing_bullet if request.existing_bullet else "Add as a new bullet point under your Projects section."
                fallback_rationale = f"Your resume does not currently contain a Projects section. Adding a technical project showcasing {kw} provides verifiable engineering evidence."
        else:
            # work_history
            alt_a = BulletAlternative(
                variant_name="Candidate A (ATS-focused)",
                bullet=f"Spearheaded technical adoption of {kw} across distributed microservices, standardizing development workflows and improving code maintainability.",
                what=kw,
                how=f"Spearheaded adoption of {kw} across distributed microservices",
                result_or_reason="Standardizing workflows and improving code maintainability",
                claim_status=claim_status,
                requires_confirmation=requires_confirmation,
                assumption=assumption,
            )

            alt_b = BulletAlternative(
                variant_name="Candidate B (Concise)",
                bullet=f"Employed {kw} within core production systems to optimize query execution and resolve processing bottlenecks.",
                what=kw,
                how=f"Employed {kw} within core production systems",
                result_or_reason="Optimize query execution and resolve bottlenecks",
                claim_status=claim_status,
                requires_confirmation=requires_confirmation,
                assumption=assumption,
            )

            alt_c = BulletAlternative(
                variant_name="Candidate C (Technical/result-focused)",
                bullet=f"Engineered and deployed scalable production services utilizing {kw}, driving an [X%] increase in system throughput across high-volume workloads.",
                what=kw,
                how=f"Engineered and deployed production services utilizing {kw}",
                result_or_reason="Driving an [X%] increase in system throughput",
                claim_status=ClaimStatus.UNVERIFIED_METRIC if is_verified else claim_status,
                requires_confirmation=True,
                assumption="Requires user to supply supported metric for [X%]",
            )

            if work_bullets:
                fallback_proj = work_bullets[0]["section"]
                fallback_bullet = request.existing_bullet if request.existing_bullet else work_bullets[0]["bullet"]
                fallback_rationale = f"Upgrading this {fallback_proj} bullet incorporates {kw} into your professional employment history."
            else:
                fallback_proj = "Professional Work Experience"
                fallback_bullet = request.existing_bullet if request.existing_bullet else "Add as a new bullet point to your current employment."
                fallback_rationale = f"Incorporating {kw} demonstrates on-the-job production impact."

        return BulletOptimizationResponse(
            status="rewritten" if is_verified else "suggested",
            target_keyword=kw,
            target_keywords=keywords,
            claim_status=claim_status,
            selected_bullet_index=0,
            alternatives=[alt_a, alt_b, alt_c],
            requires_confirmation=requires_confirmation,
            warning=warning,
            validation={
                "past_tense": True,
                "one_sentence": True,
                "one_period_max": True,
                "what_how_result_present": True,
                "keyword_stuffing": False,
            },
            target_project_name=fallback_proj,
            original_bullet_to_replace=fallback_bullet,
            replacement_rationale=fallback_rationale,
            available_resume_bullets=target_section_bullets,
        )

    # --- 4. Tailored Outreach Generator ---
    def generate_outreach(self, job: JobAnalysisResult, resume: Resume) -> OutreachResponse:
        client = self._get_client()
        if client:
            try:
                system_prompt = """
You are an expert career coach. Write a tailored, punchy, 3-paragraph cover letter pitch and a concise LinkedIn connection note based on the candidate's matched skills and the target job.
Return strict JSON:
{
  "subject_line": "Subject line for application email",
  "cover_letter_pitch": "3 high-impact paragraphs connecting skills to role",
  "connection_note": "A concise 300-character LinkedIn note for recruiters"
}
"""
                resp = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Company: {job.company}\nRole: {job.title}\nJob Skills: {', '.join(job.required_skills)}\n\nCandidate Resume:\n{resume.content[:2500]}"},
                    ],
                    temperature=0.4,
                )
                raw = resp.choices[0].message.content.strip()
                data = extract_json_from_llm_response(raw)
                return OutreachResponse(**data)
            except Exception as e:
                raise RuntimeError(f"AI API Provider Failed ({self.model_name}): {str(e)}") from e

        # Offline fallback pitch
        subject = f"Application: {job.title} — {resume.name}"
        skills_str = ", ".join(job.required_skills[:3]) if job.required_skills else "software engineering"
        pitch = (
            f"Dear Hiring Team at {job.company},\n\n"
            f"I am writing to express my strong interest in the {job.title} position. With hands-on experience in {skills_str}, "
            f"I have built scalable solutions and driven technical delivery across similar domain challenges.\n\n"
            f"Throughout my background, I have prioritized clean architecture, automated testing, and high-performance system design. "
            f"I am eager to bring this momentum to {job.company} to help accelerate your current engineering roadmap.\n\n"
            f"Thank you for your time and consideration. I welcome the opportunity to discuss how my experience aligns with your team's goals.\n\n"
            f"Sincerely,\nCandidate"
        )
        note = f"Hi! I noticed the {job.title} opening at {job.company} and would love to connect. I bring strong experience in {skills_str} and look forward to sharing ideas!"

        return OutreachResponse(
            subject_line=subject,
            cover_letter_pitch=pitch,
            connection_note=note,
        )
