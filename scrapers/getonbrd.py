import time
import logging
import urllib.parse
import requests
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class GetOnBrdScraper(BaseScraper):
    """Scraper para GetOnBrd (empleos tecnológicos y remotos para Costa Rica)."""

    BASE_URL = "https://www.getonbrd.com/api/v0/search/jobs"

    def __init__(self, config: dict):
        super().__init__("GetOnBrd", config)
        self.queries = config.get("sources", {}).get("getonbrd", {}).get("queries", [
            "support",
            "data",
            "soporte",
            "datos"
        ])

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []

        for q in self.queries:
            url = f"{self.BASE_URL}?query={urllib.parse.quote(q)}&country_code=CR"
            try:
                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
                if resp.status_code != 200:
                    continue

                data = resp.json().get("data", [])
                for item in data:
                    attr = item.get("attributes", {})
                    title = attr.get("title", "")
                    link = item.get("links", {}).get("public_url", "")
                    if not title or not link:
                        continue

                    category = self.evaluate_job(title)
                    if category:
                        found_jobs.append({
                            "source": "GetOnBrd",
                            "title": title,
                            "company": "Empresa Tech",
                            "location": "Costa Rica (Remoto/Híbrido)",
                            "url": link,
                            "published_time": "Reciente",
                            "category": category
                        })

                time.sleep(1.0)

            except Exception as e:
                logger.error(f"[GetOnBrd] Error consultando '{q}': {e}")

        logger.info(f"[GetOnBrd] Encontradas {len(found_jobs)} ofertas coincidentes.")
        return found_jobs
