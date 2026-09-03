import pytest
from backend.services.scraper import ScraperService

def test_parse_raw_text():
    scraper = ScraperService()
    text = """
    Software Engineer at Stripe
    Location: San Francisco, CA (Hybrid)
    Requirements:
    - 3+ years experience with Python and Go
    - Strong knowledge of distributed systems and PostgreSQL
    """
    job = scraper.parse_raw_text(text, source_url="https://stripe.com/jobs/123")
    assert "Software Engineer" in job.title or "Stripe" in job.company or "Stripe" in job.raw_text
    assert len(job.raw_text) > 50
    assert job.source_url == "https://stripe.com/jobs/123"

def test_extract_from_html():
    scraper = ScraperService()
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Senior Python Developer - TechCorp</title>
        <meta property="og:title" content="Senior Python Developer" />
        <meta property="og:site_name" content="TechCorp" />
      </head>
      <body>
        <main>
          <h1>Senior Python Developer</h1>
          <div class="company">TechCorp</div>
          <div class="location">Remote, US</div>
          <div class="description">
            <p>We are looking for a Senior Python Developer with 5+ years of experience in FastAPI, Docker, and AWS.</p>
            <p>You will build high performance microservices.</p>
          </div>
        </main>
      </body>
    </html>
    """
    job = scraper.extract_from_html(html, "https://techcorp.com/jobs/456")
    assert "Senior Python Developer" in job.title
    assert "TechCorp" in job.company
    assert "FastAPI" in job.raw_text
    assert "Docker" in job.raw_text
    assert job.source_url == "https://techcorp.com/jobs/456"

def test_extract_greenhouse_lever_style():
    scraper = ScraperService()
    html = """
    <html>
      <head><title>Greenhouse Job</title></head>
      <body>
        <div id="header">
          <h1 class="app-title">Backend Infrastructure Engineer</h1>
          <span class="company-name">Datadog</span>
          <div class="location">New York, NY</div>
        </div>
        <div id="content">
          <p>Join our team to scale cloud platforms using Go, Python, and Kafka.</p>
        </div>
      </body>
    </html>
    """
    job = scraper.extract_from_html(html, "https://boards.greenhouse.io/datadog/jobs/999")
    assert "Backend Infrastructure Engineer" in job.title
    assert "Datadog" in job.company or "Datadog" in job.raw_text
    assert "Kafka" in job.raw_text

def test_extract_embedded_greenhouse_ats(monkeypatch):
    scraper = ScraperService()
    portal_html = r"""
    <html>
      <head><title>Careers - Acme</title></head>
      <body>
        <div id="grnhse_app"></div>
        <script>
          window.__RETRIEVE_A_JOB_ENDPOINT__ = 'https:\/\/boards-api.greenhouse.io\/v1\/boards\/acme\/jobs\/12345';
        </script>
      </body>
    </html>
    """

    class MockResponse:
        ok = True
        status_code = 200
        text = portal_html
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "title": "Full Stack Engineer",
                "company_name": "Acme Corp",
                "location": {"name": "Remote, US"},
                "content": "&lt;p&gt;Looking for a Full Stack Engineer with React, Python, and PostgreSQL experience.&lt;/p&gt;",
            }

    def mock_get(url, *args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(scraper.session, "get", mock_get)

    job = scraper.scrape_url("https://www.acme.com/careers?gh_jid=12345")
    assert job.title == "Full Stack Engineer"
    assert job.company == "Acme Corp"
    assert job.location == "Remote, US"
    assert "React" in job.raw_text
    assert "PostgreSQL" in job.raw_text

def test_extract_nextjs_hydration_dayforce_portal():
    scraper = ScraperService()
    next_html = """
    <!DOCTYPE html>
    <html>
      <head><title>Job Details | Dayforce Jobs</title></head>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
        {
          "props": {
            "pageProps": {
              "jobData": {
                "jobTitle": "QA & Test Automation Developer",
                "postingLocations": [
                  {"formattedAddress": "MindBridge Analytics, 80 Aberdeen Street, Ottawa, Ontario, Canada"}
                ],
                "jobPostingContent": {
                  "jobDescription": "<p>MindBridge is looking for a QA Developer skilled in Python, Playwright, and CI/CD pipelines.</p>"
                }
              }
            }
          }
        }
        </script>
      </body>
    </html>
    """
    job = scraper.extract_from_html(next_html, source_url="https://jobs.dayforcehcm.com/en-CA/mindbridge/CANDIDATEPORTAL/jobs/217")
    assert job.title == "QA & Test Automation Developer"
    assert job.company == "MindBridge Analytics"
    assert "Ottawa, Ontario, Canada" in job.location
    assert "Playwright" in job.raw_text
    assert "Python" in job.raw_text

def test_extract_json_ld_schema():
    scraper = ScraperService()
    ld_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "title": "Senior Cloud Architect",
          "description": "<p>Join our team to build multi-cloud platforms using Kubernetes, Terraform, and Go.</p>",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "CloudScale Systems"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "addressLocality": "Austin",
              "addressRegion": "TX",
              "addressCountry": "US"
            }
          }
        }
        </script>
      </head>
      <body><h1>Loading Application...</h1></body>
    </html>
    """
    job = scraper.extract_from_html(ld_html, source_url="https://cloudscale.io/jobs/101")
    assert job.title == "Senior Cloud Architect"
    assert job.company == "CloudScale Systems"
    assert "Austin, TX, US" in job.location
    assert "Kubernetes" in job.raw_text
    assert "Terraform" in job.raw_text


def test_scrape_url_blocks_internal_and_cloud_metadata():
    scraper = ScraperService()
    blocked_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/api/health",
        "http://127.0.0.1:8000/",
        "http://10.0.0.1/admin",
        "file:///etc/passwd",
    ]
    for url in blocked_urls:
        job = scraper.scrape_url(url)
        # Should be caught by SSRF filter without making a network request
        assert any(term in job.raw_text.lower() for term in ["blocked", "disallowed", "invalid", "security"])

