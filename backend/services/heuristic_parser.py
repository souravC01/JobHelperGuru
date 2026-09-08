import re
from collections import Counter
from datetime import datetime
from typing import List, Set, Tuple, Optional, Dict, Any

from backend.models import JobAnalysisResult, ResumeMatchResult
from backend.services.skill_matching import contains_skill, match_skills

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


def extract_experience_required(text: str, is_new_grad: bool = False) -> str:
    """
    Extracts required professional work experience from job description text.
    Returns:
      - 'New Grad' if new/recent graduate indicators are found
      - Exact years like '1-4 years', '3+ years', '5 years' if found
      - 'Not specified' if no tenure requirement is present
    """
    if is_new_grad or re.search(r"\b(recent grads?|recent graduates?|new grads?|new graduates?|fresh graduates?|university graduates?)\b", text, re.I):
        return "New Grad"
    patterns = [
        r"(?:(?:minimum|at least)\s+)?(\d+\s*(?:-|to)\s*\d+)\+?\s*(?:years?|yrs?)(?:\s*(?:of)?\s*(?:professional|relevant|software|work|industry)?\s*experience)?",
        r"(?:(?:minimum|at least)\s+)?(\d+\+)\s*(?:years?|yrs?)(?:\s*(?:of)?\s*(?:professional|relevant|software|work|industry)?\s*experience)?",
        r"(?:(?:minimum|at least)\s+)?(\d+)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:professional|relevant|software|work|industry)?\s*experience",
        r"(?:minimum|at least)\s+(\d+)\s*(?:years?|yrs?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            val = m.group(1).strip()
            val_cleaned = re.sub(r"\s*to\s*", "-", val, flags=re.I)
            val_cleaned = re.sub(r"\s+", "", val_cleaned)
            return f"{val_cleaned} years"
    return "Not specified"


def extract_employer_grad_criteria(text: str) -> Optional[str]:
    """
    Extracts explicit employer graduation date criteria if specified.
    Returns None when no explicit criteria is detected.
    """
    if not text:
        return None

    # 1. Between month-year and month-year
    m_between = re.search(
        r"(?:graduat(?:ing|ed|ion)(?:\s+date)?|completion|degrees?\s+conferred)\s+between\s+([A-Za-z]+\s+\d{4})\s+(?:and|-)\s+([A-Za-z]+\s+\d{4})",
        text,
        re.I,
    )
    if m_between:
        return f"Between {m_between.group(1).strip()} and {m_between.group(2).strip()}"

    # 2. Between year and year
    m_years = re.search(
        r"(?:graduat(?:ing|ed|ion)|degrees?|class\s+of)\s+between\s+(\d{4})\s+(?:and|-)\s+(\d{4})",
        text,
        re.I,
    )
    if m_years:
        return f"Between {m_years.group(1).strip()} and {m_years.group(2).strip()}"

    # 3. Class of YYYY
    m_class = re.search(
        r"\bclass\s+of\s+(\d{4}(?:\s*(?:or|/|-)\s*\d{4})*)\b",
        text,
        re.I,
    )
    if m_class:
        return f"Class of {m_class.group(1).strip()}"

    # 4. Within N months/years of graduation
    m_within = re.search(
        r"\bwithin\s+(\d+)\s*(months?|years?)\s+of\s+(?:graduation|graduating|degree\s+completion)\b",
        text,
        re.I,
    )
    if m_within:
        return f"Within {m_within.group(1)} {m_within.group(2)} of graduation"

    # 5. Graduating by Month Year
    m_by = re.search(
        r"(?:graduat(?:ing|ed|ion)|completion)\s+(?:by|before|no\s+later\s+than)\s+([A-Za-z]+\s+\d{4}|\d{4})",
        text,
        re.I,
    )
    if m_by:
        return f"Graduating by {m_by.group(1).strip()}"

    return None


class HeuristicParser:
    def __init__(self, taxonomy: Set[str] = None):
        self.taxonomy = taxonomy or SKILL_TAXONOMY

    def check_new_grad_eligibility(
        self,
        resume_text: str,
        employer_criteria: Optional[Any] = None,
        ref_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Determines candidate graduation eligibility against the employer criteria:
        Returns:
          eligible: True (meets timeline), False (outside window), None (unknown / criteria unspecified)
        """
        if isinstance(employer_criteria, datetime):
            ref_date = employer_criteria
            employer_criteria = None
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
            return {'eligible': None, 'status': 'Graduation date not detected', 'grad_date': None, 'months_diff': None}

        months_diff = (grad_date.year - ref_date.year) * 12 + (grad_date.month - ref_date.month)

        if not employer_criteria or str(employer_criteria).strip().lower() in ("none", "not specified", "unknown"):
            return {
                'eligible': None,
                'status': f'Graduation date detected ({grad_str}); employer window not specified',
                'grad_date': grad_str,
                'months_diff': months_diff,
            }

        crit_lower = employer_criteria.strip().lower()

        # 1. Between dates
        m_between = re.search(r"between\s+([a-z]+)?\s*(\d{4})\s+(?:and|-)\s+([a-z]+)?\s*(\d{4})", crit_lower)
        if m_between:
            m1_name, y1, m2_name, y2 = m_between.groups()
            m1 = months_map.get(m1_name[:3], 1) if m1_name else 1
            y1 = int(y1)
            m2 = months_map.get(m2_name[:3], 12) if m2_name else 12
            y2 = int(y2)
            start_date = datetime(y1, m1, 1)
            end_date = datetime(y2, m2, 28)
            is_eligible = start_date <= grad_date <= end_date
            if is_eligible:
                status = f"Eligible New Grad ({grad_str} is within employer window {employer_criteria})"
            else:
                status = f"Ineligible for New Grad window ({grad_str} is outside employer window {employer_criteria})"
            return {'eligible': is_eligible, 'status': status, 'grad_date': grad_str, 'months_diff': months_diff}

        # 2. Class of
        m_class = re.search(r"class\s+of\s+([\d\s/,or-]+)", crit_lower)
        if m_class:
            allowed_years = [int(y) for y in re.findall(r"\b20\d{2}\b", m_class.group(1))]
            is_eligible = grad_date.year in allowed_years
            if is_eligible:
                status = f"Eligible New Grad (Class of {grad_date.year} matches employer criteria)"
            else:
                status = f"Ineligible for New Grad window (Class of {grad_date.year} does not match {employer_criteria})"
            return {'eligible': is_eligible, 'status': status, 'grad_date': grad_str, 'months_diff': months_diff}

        # 3. Within N months/years
        m_within = re.search(r"within\s+(\d+)\s*(months?|years?)", crit_lower)
        if m_within:
            num = int(m_within.group(1))
            unit = m_within.group(2)
            n_months = num * 12 if "year" in unit else num
            is_eligible = -n_months <= months_diff <= 4
            if is_eligible:
                status = f"Eligible New Grad ({grad_str} is within {num} {unit} of graduation)"
            else:
                status = f"Ineligible for New Grad window ({grad_str} exceeds {num} {unit} of graduation)"
            return {'eligible': is_eligible, 'status': status, 'grad_date': grad_str, 'months_diff': months_diff}

        # 4. Standard 4-month-ahead / 6-month-past window
        if "4 months" in crit_lower and "6 months" in crit_lower:
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

        return {
            'eligible': None,
            'status': f'Candidate graduation detected ({grad_str}); verify against employer criteria: {employer_criteria}',
            'grad_date': grad_str,
            'months_diff': months_diff,
        }

    def analyze_job_text(self, text: str) -> JobAnalysisResult:
        lowered = text.lower()

        # 1. Salary Detection
        salary_range = "Not specified"
        salary_match = re.search(
            r"(\$\s?[0-9]{2,3}(?:,[0-9]{3})*(?:\s*[kK])?(?:\s*[-to]+\s*\$\s?[0-9]{2,3}(?:,[0-9]{3})*(?:\s*[kK])?)?(?:\s*(?:/yr|/year|/hr|/hour|per year|annually))?)",
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
        new_grad_criteria = extract_employer_grad_criteria(text) if is_new_grad else None

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
            if contains_skill(text, skill):
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

        exp_required = extract_experience_required(text, is_new_grad=is_new_grad)

        summary = f"Role requiring proficiency in {', '.join(required_skills[:3]) if required_skills else 'software engineering'} with {work_mode} flexibility."

        return JobAnalysisResult(
            company="Unknown Company",
            title="Open Position",
            location="Unknown",
            work_mode=work_mode,
            salary_range=salary_range,
            experience_level=exp_level,
            experience_required=exp_required,
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

        matched, missing = match_skills(resume_text, target_skills)

        # Strict filter for missing and matched
        matched = filter_skills(matched)
        missing = filter_skills(missing)

        total_target = len(target_skills)
        if total_target == 0:
            score = 50
        else:
            score = int((len(matched) / total_target) * 100)

        # Check New Grad eligibility
        eligibility = self.check_new_grad_eligibility(
            resume_text,
            employer_criteria=job_analysis.new_grad_criteria,
        )

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
