import time
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class TalentScraper(BaseScraper):
    """Scraper de ofertas de Talent.com Costa Rica (cr.talent.com)."""

    BASE_URL = "https://cr.talent.com/jobs"

    def __init__(self, config: dict):
        super().__init__("Talent.com CR", config)
        self.queries = config.get("sources", {}).get("talent", {}).get("queries", [
            "soporte tecnico",
            "data analyst",
            "analista de datos",
            "help desk",
            "power bi"
        ])

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []

        for q in self.queries:
            params = {
                "k": q,
                "l": "Costa Rica"
            }
            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
            try:
                resp = requests.get(url, headers=self.get_headers(), timeout=12)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                card_wrappers = soup.find_all(class_=lambda c: c and "JobCard_" in str(c) and "card" in str(c).lower())

                for card in card_wrappers:
                    t_el = card.find(class_=lambda x: x and "title" in str(x).lower())
                    if not t_el:
                        continue
                    title = t_el.get_text(strip=True)

                    comp_el = card.find(class_=lambda x: x and "company" in str(x).lower())
                    company = comp_el.get_text(strip=True) if comp_el else "Confidencial"

                    loc_el = card.find(class_=lambda x: x and "location" in str(x).lower())
                    location = loc_el.get_text(strip=True) if loc_el else "Costa Rica"

                    link_el = card.find("a", href=lambda h: h and "/view?" in h)
                    if not link_el:
                        continue
                    full_link = f"https://cr.talent.com{link_el['href']}"

                    category = self.evaluate_job(title)
                    if category:
                        found_jobs.append({
                            "source": "Talent.com CR",
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": full_link,
                            "published_time": "Reciente",
                            "category": category
                        })

                time.sleep(1.5)

            except Exception as e:
                logger.error(f"[Talent.com] Error consultando '{q}': {e}")

        logger.info(f"[Talent.com] Encontradas {len(found_jobs)} ofertas coincidentes.")
        return found_jobs
