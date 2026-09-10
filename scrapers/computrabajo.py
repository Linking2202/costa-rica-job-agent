import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class ComputrabajoScraper(BaseScraper):
    """Scraper de ofertas de Computrabajo Costa Rica (cr.computrabajo.com)."""

    BASE_URL = "https://cr.computrabajo.com"

    def __init__(self, config: dict):
        super().__init__("Computrabajo CR", config)
        self.slugs = config.get("sources", {}).get("computrabajo", {}).get("slugs", [
            "analista-de-datos",
            "soporte-tecnico",
            "help-desk",
            "power-bi",
            "junior"
        ])

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []

        for slug in self.slugs:
            url = f"{self.BASE_URL}/trabajo-de-{slug}?pubdate=1" # ofertas recientes
            try:
                resp = requests.get(url, headers=self.get_headers(), timeout=12)
                if resp.status_code == 404:
                    # Si pubdate=1 no encuentra, probar sin parámetro
                    resp = requests.get(f"{self.BASE_URL}/trabajo-de-{slug}", headers=self.get_headers(), timeout=12)

                if resp.status_code != 200:
                    logger.warning(f"[Computrabajo] Status {resp.status_code} al consultar slug '{slug}'")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                offers = soup.select("article.box_offer")

                for offer in offers:
                    link_el = offer.find("a", class_="js-o-link")
                    if not link_el:
                        continue

                    title = link_el.get_text(strip=True)
                    raw_href = link_el.get("href", "")
                    if raw_href.startswith("/"):
                        full_link = f"{self.BASE_URL}{raw_href.split('#')[0]}"
                    else:
                        full_link = raw_href.split("#")[0]

                    # Empresa y ubicación
                    company_el = offer.find("p", class_="fs16")
                    company = "Confidencial"
                    if company_el:
                        company = company_el.get_text(strip=True)
                        # Limpiar calificaciones pegadas como "4,2Globalex"
                        if len(company) > 3 and company[1] in [',', '.']:
                            company = company[3:].strip()

                    loc_el = offer.find("p", class_="fs13") or offer.find("span", class_="mr10")
                    location = loc_el.get_text(strip=True) if loc_el else "Costa Rica"

                    category = self.evaluate_job(title)
                    if category:
                        found_jobs.append({
                            "source": "Computrabajo CR",
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": full_link,
                            "published_time": "Reciente",
                            "category": category
                        })

                time.sleep(1.5)

            except Exception as e:
                logger.error(f"[Computrabajo] Error consultando '{slug}': {e}")

        logger.info(f"[Computrabajo] Encontradas {len(found_jobs)} ofertas coincidentes con tu perfil.")
        return found_jobs

