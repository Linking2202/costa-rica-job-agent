import time
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class ElEmpleoScraper(BaseScraper):
    """Scraper de ofertas de ElEmpleo Costa Rica (elempleo.com/cr)."""

    BASE_URL = "https://www.elempleo.com/cr/ofertas-empleo/"

    def __init__(self, config: dict):
        super().__init__("ElEmpleo CR", config)
        self.queries = config.get("sources", {}).get("elempleo", {}).get("queries", [
            "soporte tecnico",
            "analista datos",
            "help desk",
            "it support"
        ])

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []

        for q in self.queries:
            url = f"{self.BASE_URL}?JobOffer={urllib.parse.quote(q)}"
            try:
                resp = requests.get(url, headers=self.get_headers(), timeout=12)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.find_all("a", href=lambda h: h and "/cr/ofertas-trabajo/" in h)

                for link in links:
                    title = link.get_text(strip=True)
                    if not title or len(title) < 4:
                        continue

                    raw_href = link.get("href", "")
                    full_link = raw_href if raw_href.startswith("http") else f"https://www.elempleo.com{raw_href}"

                    category = self.evaluate_job(title)
                    if category:
                        found_jobs.append({
                            "source": "ElEmpleo CR",
                            "title": title,
                            "company": "Empresa Confidencial",
                            "location": "Costa Rica",
                            "url": full_link,
                            "published_time": "Reciente",
                            "category": category
                        })

                time.sleep(1.5)

            except Exception as e:
                logger.error(f"[ElEmpleo] Error consultando '{q}': {e}")

        logger.info(f"[ElEmpleo] Encontradas {len(found_jobs)} ofertas coincidentes.")
        return found_jobs
