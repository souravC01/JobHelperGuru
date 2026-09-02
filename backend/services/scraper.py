import re
import urllib.parse
from typing import Optional
import requests
from bs4 import BeautifulSoup
import trafilatura

from backend.models import ScrapedJob


class ScraperService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })

    def scrape_url(self, url: str, timeout: int = 15) -> ScrapedJob:
        clean_url = url.strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url

        try:
            response = self.session.get(clean_url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            html = response.text
            return self.extract_from_html(html, source_url=clean_url)
        except Exception as e:
            # If fetch fails (e.g. anti-bot or 403), return error info in raw_text so user knows
            return ScrapedJob(
                title="",
                company="",
                location="",
                raw_text=f"Error fetching URL: {str(e)}. Please paste the job description text directly.",
                source_url=clean_url,
            )

    def extract_from_html(self, html: str, source_url: str = "") -> ScrapedJob:
        soup = BeautifulSoup(html, "html.parser")

        # 1. Title Extraction
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.find("h1"):
            h1 = soup.find("h1")
            title = h1.get_text(strip=True)
        elif soup.title:
            title = soup.title.get_text(strip=True)

        # 2. Company Extraction
        company = ""
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            company = og_site["content"].strip()
        else:
            # Common ATS selectors
            company_el = soup.find(class_=re.compile(r"company(-name)?|employer|organization", re.I))
            if company_el:
                company = company_el.get_text(strip=True)
            elif source_url:
                # Extract domain name as hint (e.g. boards.greenhouse.io/datadog -> datadog)
                parsed = urllib.parse.urlparse(source_url)
                parts = [p for p in parsed.path.split("/") if p]
                if "greenhouse.io" in parsed.netloc and parts:
                    company = parts[0].capitalize()
                elif "lever.co" in parsed.netloc and parts:
                    company = parts[0].capitalize()

        # 3. Location Extraction
        location = ""
        loc_el = soup.find(class_=re.compile(r"location|workplace|work-mode", re.I))
        if loc_el:
            location = loc_el.get_text(strip=True)

        # Clean title if it contains company separator (e.g. "Software Engineer - TechCorp")
        if title and company:
            title = re.sub(rf"\s*[-|–]\s*{re.escape(company)}.*", "", title, flags=re.I).strip()
        elif title and " - " in title:
            parts = title.split(" - ")
            title = parts[0].strip()
            if not company and len(parts) > 1:
                company = parts[1].strip()

        # 4. Body Content Extraction via trafilatura
        extracted_text = trafilatura.extract(
            html,
            include_links=False,
            include_comments=False,
            output_format="txt",
            favor_precision=False,
        )

        if not extracted_text or len(extracted_text) < 100:
            # Fallback to BeautifulSoup clean text if trafilatura stripped too much
            # Remove scripts, styles, navigations
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            extracted_text = soup.get_text(separator="\n", strip=True)

        return ScrapedJob(
            title=title or "Unknown Role",
            company=company or "Unknown Company",
            location=location or "Unknown",
            raw_text=extracted_text,
            source_url=source_url,
        )

    def parse_raw_text(self, text: str, source_url: str = "") -> ScrapedJob:
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        title = ""
        company = ""
        location = ""

        # Check first 5 lines for common headline patterns like "Role at Company"
        for line in lines[:5]:
            match = re.search(r"^(.*?)\s+at\s+(.*?)(?:\s*[-–(].*)?$", line, re.I)
            if match:
                title = match.group(1).strip()
                company = match.group(2).strip()
                break
            if re.search(r"(engineer|developer|manager|analyst|designer|specialist|lead|architect|scientist)", line, re.I):
                if not title:
                    title = line

        # Search for location keyword
        loc_match = re.search(r"(?:location|based in|workplace):\s*([^\n\r]+)", text, re.I)
        if loc_match:
            location = loc_match.group(1).strip()
        elif re.search(r"\b(remote|hybrid|onsite)\b", text, re.I):
            m = re.search(r"\b(remote|hybrid|onsite)\b", text, re.I)
            location = m.group(1).capitalize() if m else ""

        return ScrapedJob(
            title=title or (lines[0] if lines else "Open Position"),
            company=company or "Unknown Company",
            location=location or "Unknown",
            raw_text=text.strip(),
            source_url=source_url or "manual_paste",
        )
