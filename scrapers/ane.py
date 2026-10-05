import time
import logging
import urllib.parse
import urllib3
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from scrapers.base import BaseScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

class ANEScraper(BaseScraper):
    """
    Scraper de la Agencia Nacional de Empleo de Costa Rica (ane.cr - INA / MTSS).
    Monitorea las categorías oficiales de empleo en Costa Rica:
    - 26: Tecnología de la información y las comunicaciones (TI, Redes, Soporte)
    - 1: Administración, mercadeo y apoyo administrativo (Digitador, Back Office, Inventario)
    - 9: Electricidad/Electrónica/Telecomunicaciones (Telecomunicaciones, Redes)
    - 28: Transporte / Conductores / Almacenamiento (Inventarios, Bodega)
    """

    BASE_URL = "https://www.ane.cr/Puesto"

    def __init__(self, config: dict):
        super().__init__("ANE (ane.cr)", config)
        ane_cfg = config.get("sources", {}).get("ane", {})
        self.categories = ane_cfg.get("categories", [
            {"id": 26, "name": "TI y Telecomunicaciones"},
            {"id": 1, "name": "Administración y Apoyo Administrativo"},
            {"id": 9, "name": "Telecomunicaciones y Electrónica"},
            {"id": 28, "name": "Almacenamiento e Inventario"}
        ])
        self.max_pages_per_cat = ane_cfg.get("max_pages", 2)

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []

        for cat in self.categories:
            cat_id = cat.get("id") if isinstance(cat, dict) else cat
            cat_name = cat.get("name", str(cat_id)) if isinstance(cat, dict) else str(cat_id)

            for page in range(1, self.max_pages_per_cat + 1):
                params = {
                    "Cat": cat_id,
                    "Pagina": page
                }
                url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
                try:
                    resp = requests.get(url, headers=self.get_headers(), verify=False, timeout=12)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "html.parser")
                    listings = soup.find_all("div", class_="job-listing")
                    if not listings:
                        break

                    for item in listings:
                        t_el = item.find("h3", class_="job-listing-title")
                        c_el = item.find("h4", class_="job-listing-company")
                        dt_el = item.find("small")
                        loc_el = item.find("li")

                        if not t_el:
                            continue

                        title = t_el.get_text(strip=True)
                        company = c_el.get_text(strip=True) if c_el else "Confidencial"
                        published_time = dt_el.get_text(strip=True) if dt_el else "Reciente"
                        location = loc_el.get_text(strip=True) if loc_el else "Costa Rica"

                        category = self.evaluate_job(title)
                        if category:
                            found_jobs.append({
                                "source": "ANE Costa Rica (ane.cr)",
                                "title": title,
                                "company": company,
                                "location": location,
                                "url": f"{self.BASE_URL}?Cat={cat_id}",
                                "published_time": published_time,
                                "category": category
                            })

                    time.sleep(1.2)
                except Exception as e:
                    logger.error(f"[ANE] Error consultando categoría '{cat_name}' (Pág {page}): {e}")

        logger.info(f"[ANE] Encontradas {len(found_jobs)} ofertas coincidentes con tu perfil.")
        return found_jobs
