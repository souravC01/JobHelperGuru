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

            # Check if page embeds an external ATS widget (Greenhouse, Lever, Ashby, iframe)
            embedded_job = self._try_fetch_embedded_ats(html, source_url=clean_url, timeout=timeout)
            if embedded_job and len(embedded_job.raw_text.strip()) > 20:
                return embedded_job

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
        if source_url:
            embedded_job = self._try_fetch_embedded_ats(html, source_url=source_url)
            if embedded_job and len(embedded_job.raw_text.strip()) > 20:
                return embedded_job

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

    def _try_fetch_embedded_ats(self, html_text: str, source_url: str, timeout: int = 15) -> Optional[ScrapedJob]:
        """
        Detects modern ATS widgets embedded on corporate career portals
        (e.g. Greenhouse API embed, Lever embed, Ashby embed, or embedded iframes).
        """
        import html as html_lib

        # 1. Direct Greenhouse API Endpoint in HTML (e.g. IXL, Figma, Stripe, Airbnb)
        gh_match = re.search(
            r"boards-api\.greenhouse\.io[\\/]+v1[\\/]+boards[\\/]+([^\\/\"'\s]+)[\\/]+jobs[\\/]+(\d+)",
            html_text,
            re.IGNORECASE,
        )
        if gh_match:
            board = gh_match.group(1)
            job_id = gh_match.group(2)
            api_job = self._fetch_greenhouse_api(board, job_id, source_url, timeout=timeout)
            if api_job:
                return api_job

        # 2. Greenhouse query parameter `gh_jid` (e.g. https://www.ixl.com/company/careers?gh_jid=8765751002)
        jid_match = re.search(r"[?&]gh_jid=(\d+)", source_url)
        if jid_match:
            job_id = jid_match.group(1)
            # Find board token in HTML
            board_match = (
                re.search(r"boards\.greenhouse\.io/embed/job_board/js\?for=([^\"'\s&]+)", html_text)
                or re.search(r"data-greenhouse-board=[\"']([^\"']+)[\"']", html_text)
                or re.search(r"window\.__RETRIEVE_A_JOB_ENDPOINT__\s*=\s*['\"][^'\"]*boards[\\/]+([^\\/\"'\s]+)", html_text)
                or re.search(r"boards-api\.greenhouse\.io[\\/]+v1[\\/]+boards[\\/]+([^\\/\"'\s]+)", html_text)
            )
            if board_match:
                board = board_match.group(1)
                api_job = self._fetch_greenhouse_api(board, job_id, source_url, timeout=timeout)
                if api_job:
                    return api_job

        # 3. Direct Greenhouse board URL (e.g. boards.greenhouse.io/{board}/jobs/{id} or job-boards.greenhouse.io/{board}/jobs/{id})
        direct_gh = re.search(r"(?:boards|job-boards)\.greenhouse\.io/([^/\"'\s]+)/jobs/(\d+)", source_url)
        if direct_gh:
            board = direct_gh.group(1)
            job_id = direct_gh.group(2)
            api_job = self._fetch_greenhouse_api(board, job_id, source_url, timeout=timeout)
            if api_job:
                return api_job

        # 4. Lever API Endpoint (e.g. jobs.lever.co/{company}/{job_id})
        lever_match = re.search(r"jobs\.lever\.co/([^/\"'\s]+)/([a-f0-9-]+)", source_url) or re.search(
            r"api\.lever\.co/v0/postings/([^/\"'\s]+)/([a-f0-9-]+)", html_text
        )
        if lever_match:
            company_token = lever_match.group(1)
            posting_id = lever_match.group(2)
            api_job = self._fetch_lever_api(company_token, posting_id, source_url, timeout=timeout)
            if api_job:
                return api_job

        # 5. Embedded ATS Iframes in HTML (Greenhouse, Lever, Ashby, SmartRecruiters)
        soup = BeautifulSoup(html_text, "html.parser")
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "").strip()
            if not src:
                continue
            if any(ats in src.lower() for ats in ["greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com"]):
                if not src.startswith("http"):
                    src = urllib.parse.urljoin(source_url, src)
                try:
                    iframe_resp = self.session.get(src, timeout=timeout)
                    if iframe_resp.ok and len(iframe_resp.text) > 300:
                        iframe_job = self.extract_from_html(iframe_resp.text, source_url=source_url)
                        if iframe_job and len(iframe_job.raw_text.strip()) > 150:
                            return iframe_job
                except Exception:
                    pass

        return None

    def _fetch_greenhouse_api(self, board: str, job_id: str, source_url: str, timeout: int = 15) -> Optional[ScrapedJob]:
        import html as html_lib
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"
        try:
            resp = self.session.get(api_url, timeout=timeout)
            if resp.ok:
                data = resp.json()
                title = data.get("title") or "Open Position"
                company = data.get("company_name") or board.capitalize()
                location = data.get("location", {}).get("name") or "Unknown"

                # Check metadata for Brand name if company_name is missing
                if company == board.capitalize():
                    for meta in data.get("metadata", []):
                        if meta.get("name") in ["Brand", "Company"]:
                            company = meta.get("value") or company

                raw_content = html_lib.unescape(data.get("content") or "")
                soup = BeautifulSoup(raw_content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)

                if text and len(text) > 20:
                    return ScrapedJob(
                        title=title.strip(),
                        company=company.strip(),
                        location=location.strip(),
                        raw_text=text.strip(),
                        source_url=source_url,
                    )
        except Exception:
            pass
        return None

    def _fetch_lever_api(self, company_token: str, posting_id: str, source_url: str, timeout: int = 15) -> Optional[ScrapedJob]:
        api_url = f"https://api.lever.co/v0/postings/{company_token}/{posting_id}"
        try:
            resp = self.session.get(api_url, timeout=timeout)
            if resp.ok:
                data = resp.json()
                title = data.get("text") or "Open Position"
                company = company_token.capitalize()
                cats = data.get("categories", {})
                location = cats.get("location") or cats.get("workplaceType") or "Unknown"
                desc = data.get("descriptionPlain") or ""
                if not desc and data.get("description"):
                    soup = BeautifulSoup(data.get("description"), "html.parser")
                    desc = soup.get_text(separator="\n", strip=True)

                # Append lists if present
                lists = data.get("lists", [])
                for lst in lists:
                    desc += f"\n\n{lst.get('text', '')}\n"
                    desc += lst.get("content", "")

                if desc and len(desc) > 100:
                    return ScrapedJob(
                        title=title.strip(),
                        company=company.strip(),
                        location=location.strip(),
                        raw_text=desc.strip(),
                        source_url=source_url,
                    )
        except Exception:
            pass
        return None
