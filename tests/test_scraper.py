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
