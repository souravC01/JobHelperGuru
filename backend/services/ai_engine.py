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
from backend.services.heuristic_parser import HeuristicParser


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
        if not self.api_key:
            return None
        try:
            return OpenAI(base_url=self.api_base_url, api_key=self.api_key, timeout=30.0)
        except Exception:
            return None

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
                # Strip markdown codeblocks if model included them
                raw_content = re.sub(r"^```json\s*", "", raw_content)
                raw_content = re.sub(r"^```\s*", "", raw_content)
                raw_content = re.sub(r"\s*```$", "", raw_content)
                data = json.loads(raw_content)
                return JobAnalysisResult(**data)
            except Exception as e:
                # Log and fallback to heuristic
                print(f"[AIEngine] LLM analysis failed: {e}. Falling back to heuristic.")

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
                raw_content = re.sub(r"^```json\s*", "", raw_content)
                raw_content = re.sub(r"^```\s*", "", raw_content)
                raw_content = re.sub(r"\s*```$", "", raw_content)
                ai_evals = json.loads(raw_content)

                eval_map = {item["resume_id"]: item for item in ai_evals}
                for r in resumes:
                    ev = eval_map.get(r.id, {})
                    ranked_list.append(
                        RankedResume(
                            resume_id=r.id,
                            resume_name=r.name,
                            match_score=ev.get("match_score", 50),
                            matched_keywords=ev.get("matched_keywords", []),
                            missing_keywords=ev.get("missing_keywords", []),
                            fit_summary=ev.get("fit_summary", ""),
                            is_best_fit=False,
                        )
                    )
            except Exception as e:
                print(f"[AIEngine] LLM resume ranking failed: {e}. Falling back to heuristic.")
                ranked_list = []

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
                    )
                )

        # Sort descending by match score
        ranked_list.sort(key=lambda x: x.match_score, reverse=True)
        if ranked_list:
            ranked_list[0].is_best_fit = True

        return ranked_list

    # --- 3. Bulletskill.md Optimizer ---
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

        # Parse candidate resume bullets from evidence
        parsed_bullets = []
        raw_evidence = "\n".join(request.evidence_context)
        current_sec = "Projects / Experience"
        for line in raw_evidence.splitlines():
            sline = line.strip()
            if not sline:
                continue
            if any(h in sline.lower() for h in ["project", "experience", "work history", "employment", "role"]) and len(sline) < 60 and not sline.startswith(("-", "•", "*")):
                current_sec = sline.strip("#:- ")
                continue
            if sline.startswith(("-", "•", "*", "–")) or (len(sline) > 30 and sline[0].isupper() and sline.endswith(".")):
                clean_b = re.sub(r"^[-•*–\d\.]+\s*", "", sline).strip()
                if len(clean_b) > 15:
                    parsed_bullets.append({"section": current_sec, "bullet": clean_b})

        client = self._get_client()
        if client:
            try:
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
- IDENTIFY WHICH SPECIFIC PROJECT OR WORK EXPERIENCE ENTRY from the candidate's resume should be modified, which specific existing bullet point should be replaced/upgraded, and explain the strategic rationale.
Return strict JSON with this exact schema:
{{
  "status": "rewritten",
  "target_keyword": "{primary_kw}",
  "claim_status": "{claim_status.value}",
  "target_project_name": "Exact or identified project/role name from resume (e.g. 'Project: Distributed Order Processing' or 'Role: Software Engineer')",
  "original_bullet_to_replace": "The exact or closest existing bullet point in that project/role that should be replaced or augmented with these skills. If no existing bullet fits, output 'Add as a new bullet point under this project.'",
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
                user_msg = f"""
Target Job Title: {request.target_job_title}
Section Type: {request.section_type}
Target Keywords: {primary_kw}
Existing Bullet (if user pre-selected one): {request.existing_bullet or 'Auto-detect best project bullet to replace from Candidate Resume'}
Candidate Resume Context & Bullets:
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
                raw_content = re.sub(r"^```json\s*", "", raw_content)
                raw_content = re.sub(r"^```\s*", "", raw_content)
                raw_content = re.sub(r"\s*```$", "", raw_content)
                data = json.loads(raw_content)
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
                    target_project_name=data.get("target_project_name") or (parsed_bullets[0]["section"] if parsed_bullets else "Primary Technical Project"),
                    original_bullet_to_replace=data.get("original_bullet_to_replace") or (parsed_bullets[0]["bullet"] if parsed_bullets else "Add as a new bullet point to your technical project."),
                    replacement_rationale=data.get("replacement_rationale") or f"Upgrading this bullet incorporates {primary_kw} where core architecture is evaluated.",
                    available_resume_bullets=parsed_bullets,
                )
            except Exception as e:
                print(f"[AIEngine] LLM bullet optimization failed: {e}. Using offline BulletSkill engine.")

        # Offline template generation following Bulletskill.md
        kw = primary_kw
        if request.section_type == "project":
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

        # Fallback placement
        fallback_proj = parsed_bullets[0]["section"] if parsed_bullets else f"Recommended {request.section_type.title()}: Core Systems & Applications"
        fallback_bullet = request.existing_bullet if request.existing_bullet else (parsed_bullets[0]["bullet"] if parsed_bullets else "Add as a new bullet point to this project.")
        fallback_rationale = f"Upgrading this {fallback_proj} bullet provides the strongest contextual placement for {kw} to satisfy employer ATS requirements."

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
            available_resume_bullets=parsed_bullets,
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
                raw = re.sub(r"^```json\s*", "", raw)
                raw = re.sub(r"^```\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
                data = json.loads(raw)
                return OutreachResponse(**data)
            except Exception as e:
                print(f"[AIEngine] LLM outreach failed: {e}. Using offline pitch.")

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
