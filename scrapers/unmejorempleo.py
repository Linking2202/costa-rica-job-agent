import time
import logging
import urllib.parse
import urllib3
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from scrapers.base import BaseScraper

urllib3.disable_warnings()
logger = logging.getLogger(__name__)

class UnMejorEmpleoScraper(BaseScraper):
    """Scraper de ofertas de UnMejorEmpleo Costa Rica (unmejorempleo.co.cr)."""

    BASE_URL = "https://www.unmejorempleo.co.cr"

    def __init__(self, config: dict):
        super().__init__("UnMejorEmpleo CR", config)
        self.queries = config.get("sources", {}).get("unmejorempleo", {}).get("queries", [
            "soporte",
            "datos",
            "digitador",
            "inventario",
            "back office"
        ])

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []

        for q in self.queries:
            url = f"{self.BASE_URL}/empleos?q={urllib.parse.quote(q)}"
            try:
                resp = requests.get(url, headers=self.get_headers(), verify=False, timeout=12)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                for h in soup.find_all(["h2", "h3"]):
                    a = h.find("a", href=True)
                    if not a or "empleo-" not in a["href"]:
                        continue

                    title = a.get_text(strip=True)
                    raw_href = a["href"]
                    full_link = raw_href if raw_href.startswith("http") else f"{self.BASE_URL}/{raw_href.lstrip('/')}"

                    # Ubicación
                    card = h.find_parent("div")
                    card_text = card.get_text(" ", strip=True) if card else ""
                    location = "Costa Rica"
                    for prov in ["San José", "Alajuela", "Heredia", "Cartago", "Puntarenas", "Guanacaste", "Limón"]:
                        if prov.lower() in card_text.lower():
                            location = f"{prov}, Costa Rica"
                            break

                    category = self.evaluate_job(title)
                    if category:
                        found_jobs.append({
                            "source": "UnMejorEmpleo CR",
                            "title": title,
                            "company": "Empresa Confidencial",
                            "location": location,
                            "url": full_link,
                            "published_time": "Reciente",
                            "category": category
                        })

                time.sleep(1.5)

            except Exception as e:
                logger.error(f"[UnMejorEmpleo] Error consultando '{q}': {e}")

        logger.info(f"[UnMejorEmpleo] Encontradas {len(found_jobs)} ofertas coincidentes.")
        return found_jobs
