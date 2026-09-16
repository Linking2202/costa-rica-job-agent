import time
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class CompaniesScraper(BaseScraper):
    """
    Scraper especializado en sondeo directo de empresas multinacionales en Costa Rica:
    - APIs directas (Amazon Jobs CR, Experian SmartRecruiters).
    - Sondeo específico en LinkedIn por empresa (Equifax, DHL, Intel, Align, etc.).
    """

    def __init__(self, config: dict):
        super().__init__("Sondeo Empresas CR", config)
        companies_cfg = config.get("sources", {}).get("companies", {})
        self.target_companies = companies_cfg.get("target_companies", [
            "Equifax",
            "DHL",
            "Intel",
            "Amazon",
            "Align Technology",
            "Experian",
            "Foundever",
            "Tek Experts",
            "Concentrix",
            "Western Union",
            "Procter & Gamble",
            "Boston Scientific",
            "Microsoft",
            "Kyndryl"
        ])
        self.time_filter = companies_cfg.get("time_filter", "r604800")

    def fetch_amazon_jobs(self) -> List[Dict]:
        """Consulta directamente la API oficial de Amazon Jobs en Costa Rica."""
        found = []
        url = "https://www.amazon.jobs/en/search.json?country=CRI"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                for job in data.get("jobs", []):
                    title = job.get("title", "")
                    category = self.evaluate_job(title)
                    if category:
                        path = job.get("job_path", "")
                        full_link = f"https://www.amazon.jobs{path}" if path else "https://www.amazon.jobs"
                        found.append({
                            "source": "Amazon Careers (CR)",
                            "title": title,
                            "company": "Amazon Costa Rica",
                            "location": "San José / Heredia, Costa Rica",
                            "url": full_link,
                            "published_time": "Reciente",
                            "category": category
                        })
        except Exception as e:
            logger.error(f"[Empresas] Error consultando Amazon Jobs: {e}")
        return found

    def fetch_smartrecruiters_jobs(self) -> List[Dict]:
        """Consulta la API de SmartRecruiters para empresas en Costa Rica (ej: Experian)."""
        found = []
        url = "https://api.smartrecruiters.com/v1/companies/Experian/postings?country=cr"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("content", []):
                    title = item.get("name", "")
                    category = self.evaluate_job(title)
                    if category:
                        job_id = item.get("id")
                        found.append({
                            "source": "Experian Careers",
                            "title": title,
                            "company": "Experian Costa Rica",
                            "location": "Heredia, Costa Rica",
                            "url": f"https://jobs.smartrecruiters.com/Experian/{job_id}",
                            "published_time": "Reciente",
                            "category": category
                        })
        except Exception as e:
            logger.error(f"[Empresas] Error consultando SmartRecruiters: {e}")
        return found

    def fetch_linkedin_company_jobs(self) -> List[Dict]:
        """Sondea específicamente las vacantes de cada empresa multinacional en LinkedIn Costa Rica."""
        found = []
        base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

        for company in self.target_companies:
            params = {
                "keywords": company,
                "location": "Costa Rica",
                "f_TPR": self.time_filter,
                "start": 0
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            try:
                resp = requests.get(url, headers=self.get_headers(), timeout=12)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("li")

                for card in cards:
                    t_el = card.find("h3", class_="base-search-card__title")
                    c_el = card.find("h4", class_="base-search-card__subtitle")
                    l_el = card.find("span", class_="job-search-card__location")
                    link_el = card.find("a", class_="base-card__full-link")

                    if not t_el or not link_el:
                        continue

                    title = t_el.get_text(strip=True)
                    comp_name = c_el.get_text(strip=True) if c_el else company
                    location = l_el.get_text(strip=True) if l_el else "Costa Rica"
                    clean_link = link_el.get("href", "").split("?")[0]

                    category = self.evaluate_job(title)
                    if category:
                        found.append({
                            "source": f"Portal {company} (CR)",
                            "title": title,
                            "company": comp_name,
                            "location": location,
                            "url": clean_link,
                            "published_time": "Reciente",
                            "category": category
                        })

                time.sleep(1.2)
            except Exception as e:
                logger.error(f"[Empresas] Error sondeando {company}: {e}")

        return found

    def fetch_jobs(self) -> List[Dict]:
        all_found = []
        logger.info("[Empresas] Iniciando sondeo de empresas multinacionales en Costa Rica...")

        # 1. Amazon API
        amazon_jobs = self.fetch_amazon_jobs()
        all_found.extend(amazon_jobs)

        # 2. SmartRecruiters (Experian, etc.)
        smart_jobs = self.fetch_smartrecruiters_jobs()
        all_found.extend(smart_jobs)

        # 3. Sondeo por empresa en LinkedIn
        company_jobs = self.fetch_linkedin_company_jobs()
        all_found.extend(company_jobs)

        logger.info(f"[Empresas] Sondeo completado: {len(all_found)} vacantes coincidentes encontradas.")
        return all_found
