import re
from collections import Counter
from typing import List, Set, Tuple

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


class HeuristicParser:
    def __init__(self, taxonomy: Set[str] = None):
        self.taxonomy = taxonomy or SKILL_TAXONOMY

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

        # 3. Experience Level Detection
        exp_level = "Not specified"
        if re.search(r"\b(entry level|junior|associate|intern|new grad)\b", lowered):
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

        # Find sections in the JD
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

        if not required_skills:
            required_skills = tech_stack[:5]

        # 5. Extract ATS Keywords (top frequent capitalized and domain keywords)
        words = re.findall(r"\b[A-Za-z0-9+#.-]{3,20}\b", text)
        stop_words = {"the", "and", "for", "with", "you", "will", "our", "are", "that", "this", "from", "have", "your", "work", "team", "years", "experience", "about", "role", "help"}
        filtered_words = [w for w in words if w.lower() not in stop_words and len(w) > 2]
        counts = Counter(filtered_words)

        ats_candidates = list(dict.fromkeys(found_skills + [w for w, _ in counts.most_common(30) if w[0].isupper()]))
        ats_keywords = ats_candidates[:20]

        summary = f"Role requiring proficiency in {', '.join(required_skills[:3]) if required_skills else 'software engineering'} with {work_mode} flexibility."

        return JobAnalysisResult(
            company="Detected Company",
            title="Detected Role",
            location="Identified Location",
            work_mode=work_mode,
            salary_range=salary_range,
            experience_level=exp_level,
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

        matched = []
        missing = []

        for skill in target_skills:
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, resume_text, re.I):
                matched.append(skill)
            else:
                missing.append(skill)

        total_target = len(target_skills)
        if total_target == 0:
            score = 50
        else:
            score = int((len(matched) / total_target) * 100)

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
        )
