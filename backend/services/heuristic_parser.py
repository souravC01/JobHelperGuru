import re
from collections import Counter
from datetime import datetime
from typing import List, Set, Tuple, Optional, Dict, Any

from backend.models import JobAnalysisResult, ResumeMatchResult

# Curated high-value technical and soft skills taxonomy
SKILL_TAXONOMY = {
    # Programming Languages
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Golang", "C++", "C#", "Rust", "Ruby",
    "PHP", "Swift", "Kotlin", "Scala", "SQL", "HTML", "CSS", "Bash", "Shell", "R",
    # Frameworks & Libraries
    "React", "Next.js", "Vue", "Angular", "Svelte", "Node.js", "Express", "FastAPI", "Flask",
    "Django", "Spring Boot", "Spring", "ASP.NET", ".NET", "Ruby on Rails", "Tailwind CSS",
    # Databases & Storage
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB",
    "SQLite", "Oracle", "Snowflake", "BigQuery", "Neo4j",
    # Cloud & Infrastructure
    "AWS", "Amazon Web Services", "Azure", "Google Cloud", "GCP", "Docker", "Kubernetes",
    "Terraform", "Ansible", "Linux", "Serverless", "Cloudflare",
    # DevOps & CI/CD
    "CI/CD", "GitHub Actions", "GitLab CI", "Jenkins", "CircleCI", "ArgoCD", "Prometheus", "Grafana",
    # Architecture & Concepts
    "Microservices", "REST APIs", "RESTful APIs", "GraphQL", "gRPC", "Distributed Systems",
    "Event-Driven Architecture", "Kafka", "RabbitMQ", "SQS", "Pub/Sub", "System Design",
    # AI / ML / Data
    "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Pandas", "NumPy",
    "Scikit-Learn", "Apache Spark", "Airflow", "LLMs", "Generative AI", "NLP", "Computer Vision",
    # Testing & Quality
    "TDD", "Unit Testing", "Pytest", "Jest", "Selenium", "Cypress", "Playwright", "Postman",
    # Tools & Methods
    "Git", "GitHub", "GitLab", "Jira", "Confluence", "Agile", "Scrum", "SDLC",
    # Soft Skills
    "Cross-functional communication", "Technical leadership", "Mentorship", "Problem-solving",
    "Code reviews", "Stakeholder management"
}

# Non-skill terms that must never be treated as technical or ATS skills
NON_SKILL_TERMS = {
    "new grad", "new graduate", "new grads", "new graduates",
    "recent grad", "recent graduate", "recent grads", "recent graduates",
    "entry level", "entry-level", "fresh grad", "fresh graduate",
    "university graduate", "university grad", "college graduate", "college grad",
    "undergraduate", "bachelor", "master", "phd", "degree", "diploma",
    "authorization", "work authorization", "citizenship", "visa",
    "years of experience", "years experience"
}


def is_non_skill(term: str) -> bool:
    if not term:
        return True
    low = term.strip().lower()
    if low in NON_SKILL_TERMS:
        return True
    return any(
        low == ns or low.startswith(ns + " ") or low.endswith(" " + ns)
        for ns in NON_SKILL_TERMS
    )


def filter_skills(skills: List[str]) -> List[str]:
    return [s.strip() for s in skills if s and s.strip() and not is_non_skill(s)]


class HeuristicParser:
    def __init__(self, taxonomy: Set[str] = None):
        self.taxonomy = taxonomy or SKILL_TAXONOMY

    def check_new_grad_eligibility(self, resume_text: str, ref_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Determines whether a candidate qualifies as a New Grad:
        - Graduating in the next 4 months (0 <= months_diff <= 4)
        - Graduated within the last 6 months (-6 <= months_diff < 0)
        """
        ref_date = ref_date or datetime.now()
        months_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        patterns = [
            r'(?:expected|graduation|graduating|degree\s+expected|completion)[:\s]+([A-Za-z]+)\s+((?:20)\d{2})',
            r'(?:expected|graduation|graduating)[:\s]+((?:20)\d{2})',
            r'(?:bachelor|master|bsc|ba|bs|b\.s\.|b\.sc|diploma|degree).*?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s+((?:20)\d{2})',
            r'class\s+of\s+((?:20)\d{2})',
            r'(?:bachelor|master|bsc|ba|bs).*?((?:20)\d{2})'
        ]

        grad_date = None
        grad_str = ''

        for pat in patterns:
            m = re.search(pat, resume_text, re.IGNORECASE)
            if m:
                groups = m.groups()
                if len(groups) == 2 and groups[0].lower()[:3] in months_map:
                    m_num = months_map[groups[0].lower()[:3]]
                    y_num = int(groups[1])
                    grad_date = datetime(y_num, m_num, 1)
                    grad_str = f'{groups[0].capitalize()} {y_num}'
                    break
                elif len(groups) == 1 and groups[0].isdigit():
                    y_num = int(groups[0])
                    grad_date = datetime(y_num, 6, 1)
                    grad_str = f'June {y_num}'
                    break

        if not grad_date:
            return {'eligible': False, 'status': 'Graduation date not detected', 'grad_date': None, 'months_diff': None}

        months_diff = (grad_date.year - ref_date.year) * 12 + (grad_date.month - ref_date.month)
        is_eligible = (-6 <= months_diff <= 4)

        if 0 <= months_diff <= 4:
            timing = f'graduating in {months_diff} month(s) ({grad_str})'
            status = f'Eligible New Grad ({timing})'
        elif -6 <= months_diff < 0:
            timing = f'graduated {-months_diff} month(s) ago ({grad_str})'
            status = f'Eligible New Grad ({timing})'
        elif months_diff > 4:
            timing = f'expected graduation in {months_diff} months ({grad_str})'
            status = f'Current Student ({timing} - exceeds 4-month new grad window)'
        else:
            timing = f'graduated {-months_diff} months ago ({grad_str})'
            status = f'Experienced Professional ({timing} - exceeds 6-month new grad window)'

        return {'eligible': is_eligible, 'status': status, 'grad_date': grad_str, 'months_diff': months_diff}

    def analyze_job_text(self, text: str) -> JobAnalysisResult:
        lowered = text.lower()

        # 1. Salary Detection
        salary_range = "Not specified"
        salary_match = re.search(
            r"(\$\s?[0-9]{2,3}(?:,[0-9]{3})*(?:\s*[kK])?(?:\s*[-–to]+\s*\$\s?[0-9]{2,3}(?:,[0-9]{3})*(?:\s*[kK])?)?(?:\s*(?:/yr|/year|/hr|/hour|per year|annually))?)",
            text,
            re.I,
        )
        if salary_match:
            salary_range = salary_match.group(1).strip()

        # 2. Work Mode Detection
        work_mode = "Unknown"
        if re.search(r"\b(remote|work from home|wfh)\b", lowered):
            work_mode = "Remote"
        elif re.search(r"\b(hybrid)\b", lowered):
            work_mode = "Hybrid"
        elif re.search(r"\b(onsite|in-office|on-site)\b", lowered):
            work_mode = "Onsite"

        # 3. Experience Level & New Grad Detection
        exp_level = "Not specified"
        is_new_grad = bool(re.search(r"\b(new grad|new graduate|recent grad|recent graduate|university graduate|class of (?:20\d{2})|fresh graduate)\b", lowered))
        new_grad_criteria = "Graduating in the next 4 months or graduated within the last 6 months" if is_new_grad else None

        if is_new_grad or re.search(r"\b(entry level|junior|associate|intern)\b", lowered):
            exp_level = "Entry"
        elif re.search(r"\b(lead|principal|staff|architect|director|head of)\b", lowered):
            exp_level = "Senior / Lead"
        elif re.search(r"\b(senior|sr\.)\b", lowered):
            exp_level = "Senior"
        elif re.search(r"\b(mid level|mid-level|intermediate)\b", lowered):
            exp_level = "Mid"

        # 4. Extract Skills from text matching taxonomy
        found_skills = []
        for skill in self.taxonomy:
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, text, re.I):
                found_skills.append(skill)

        # Separate required vs preferred vs tech stack
        required_skills = []
        preferred_skills = []
        tech_stack = []
        soft_skills = []

        req_section = ""
        pref_section = ""

        req_match = re.search(r"(?:requirements|qualifications|must have|what you.ll bring)[:\n](.*?)(?:nice to have|preferred|bonus|what we offer|$)", text, re.I | re.DOTALL)
        if req_match:
            req_section = req_match.group(1).lower()

        pref_match = re.search(r"(?:preferred|nice to have|bonus|plus)[:\n](.*?)(?:what we offer|benefits|about us|$)", text, re.I | re.DOTALL)
        if pref_match:
            pref_section = pref_match.group(1).lower()

        for skill in found_skills:
            low_skill = skill.lower()
            if skill in ["Cross-functional communication", "Technical leadership", "Mentorship", "Problem-solving", "Code reviews", "Stakeholder management", "Agile", "Scrum"]:
                soft_skills.append(skill)
            elif pref_section and low_skill in pref_section:
                preferred_skills.append(skill)
            elif req_section and low_skill in req_section:
                required_skills.append(skill)
                tech_stack.append(skill)
            else:
                tech_stack.append(skill)

        # Filter out any non-skill terms like "New Grad", "Degree", etc.
        required_skills = filter_skills(required_skills)
        preferred_skills = filter_skills(preferred_skills)
        tech_stack = filter_skills(tech_stack)

        if not required_skills:
            required_skills = tech_stack[:5]

        # 5. Extract ATS Keywords (top frequent capitalized and domain keywords, strictly excluding non-skills)
        words = re.findall(r"\b[A-Za-z0-9+#.-]{3,20}\b", text)
        stop_words = {"the", "and", "for", "with", "you", "will", "our", "are", "that", "this", "from", "have", "your", "work", "team", "years", "experience", "about", "role", "help"}
        filtered_words = [w for w in words if w.lower() not in stop_words and len(w) > 2 and not is_non_skill(w)]
        counts = Counter(filtered_words)

        ats_candidates = list(dict.fromkeys(found_skills + [w for w, _ in counts.most_common(30) if w[0].isupper()]))
        ats_keywords = filter_skills(ats_candidates)[:20]

        summary = f"Role requiring proficiency in {', '.join(required_skills[:3]) if required_skills else 'software engineering'} with {work_mode} flexibility."

        return JobAnalysisResult(
            company="Detected Company",
            title="Detected Role",
            location="Identified Location",
            work_mode=work_mode,
            salary_range=salary_range,
            experience_level=exp_level,
            is_new_grad_role=is_new_grad,
            new_grad_criteria=new_grad_criteria,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            tech_stack=list(dict.fromkeys(tech_stack)),
            soft_skills=soft_skills,
            ats_keywords=ats_keywords,
            summary=summary,
        )

    def match_resume(self, resume_text: str, job_analysis: JobAnalysisResult) -> ResumeMatchResult:
        target_skills = list(dict.fromkeys(job_analysis.required_skills + job_analysis.ats_keywords[:10]))
        if not target_skills:
            target_skills = job_analysis.tech_stack[:10]

        target_skills = filter_skills(target_skills)

        matched = []
        missing = []

        for skill in target_skills:
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, resume_text, re.I):
                matched.append(skill)
            else:
                missing.append(skill)

        # Strict filter for missing and matched
        matched = filter_skills(matched)
        missing = filter_skills(missing)

        total_target = len(target_skills)
        if total_target == 0:
            score = 50
        else:
            score = int((len(matched) / total_target) * 100)

        # Check New Grad eligibility
        eligibility = self.check_new_grad_eligibility(resume_text)

        fit_summary = (
            f"Matches {len(matched)} of {total_target} key target skills ({score}%). "
            f"Strong alignment with {', '.join(matched[:3]) if matched else 'core skills'}. "
            f"Missing coverage on: {', '.join(missing[:3]) if missing else 'none'}."
        )

        return ResumeMatchResult(
            match_score=min(max(score, 0), 100),
            matched_keywords=matched,
            missing_keywords=missing,
            fit_summary=fit_summary,
            is_new_grad_role=job_analysis.is_new_grad_role,
            new_grad_eligible=eligibility["eligible"] if job_analysis.is_new_grad_role else None,
            graduation_status=eligibility["status"],
            graduation_date=eligibility["grad_date"],
        )
