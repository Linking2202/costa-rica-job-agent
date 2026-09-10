import time
import urllib.parse
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class LinkedInScraper(BaseScraper):
    """Scraper de ofertas de empleo públicas de LinkedIn para Costa Rica."""

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    def __init__(self, config: dict):
        super().__init__("LinkedIn", config)
        self.queries = config.get("sources", {}).get("linkedin", {}).get("queries", [
            "Junior Data Analyst",
            "Data Analyst",
            "IT Support",
            "Desktop Support",
            "Help Desk",
            "Soporte Tecnico",
            "Service Desk"
        ])
        # f_TPR: r86400 = últimas 24 horas, r3600 = última hora
        self.time_filter = config.get("sources", {}).get("linkedin", {}).get("time_filter", "r86400")

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []

        for q in self.queries:
            params = {
                "keywords": q,
                "location": "Costa Rica",
                "f_TPR": self.time_filter,
                "start": 0
            }
            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
            
            try:
                resp = requests.get(url, headers=self.get_headers(), timeout=12)
                if resp.status_code != 200:
                    logger.warning(f"[LinkedIn] Status {resp.status_code} al buscar '{q}'")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("li")

                for card in cards:
                    title_el = card.find("h3", class_="base-search-card__title")
                    company_el = card.find("h4", class_="base-search-card__subtitle")
                    loc_el = card.find("span", class_="job-search-card__location")
                    link_el = card.find("a", class_="base-card__full-link")
                    time_el = card.find("time")

                    if not title_el or not link_el:
                        continue

                    title = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True) if company_el else "Confidencial"
                    location = loc_el.get_text(strip=True) if loc_el else "Costa Rica"
                    raw_link = link_el.get("href", "")
                    # Limpiar parámetros de tracking de la URL
                    clean_link = raw_link.split("?")[0]
                    pub_time = time_el.get_text(strip=True) if time_el else "Reciente"

                    category = self.evaluate_job(title)
                    if category:
                        found_jobs.append({
                            "source": "LinkedIn",
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": clean_link,
                            "published_time": pub_time,
                            "category": category
                        })

                # Pausa breve entre consultas para respetar rate limits
                time.sleep(1.5)

            except Exception as e:
                logger.error(f"[LinkedIn] Error consultando '{q}': {e}")

        logger.info(f"[LinkedIn] Encontradas {len(found_jobs)} ofertas coincidentes con tu perfil.")
        return found_jobs

