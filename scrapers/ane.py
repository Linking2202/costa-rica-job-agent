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
    AUTOCOMPLETE_URL = "https://www.ane.cr/Puesto/AutoCompleteEmpleos"

    def __init__(self, config: dict):
        super().__init__("ANE (ane.cr)", config)
        ane_cfg = config.get("sources", {}).get("ane", {})
        self.categories = ane_cfg.get("categories", [
            {"id": 26, "name": "TI y Telecomunicaciones"},
            {"id": 1, "name": "Administración y Apoyo Administrativo"},
            {"id": 9, "name": "Telecomunicaciones y Electrónica"},
            {"id": 28, "name": "Almacenamiento e Inventario"},
            {"id": 19, "name": "Seguridad y Monitoreo CCTV"},
            {"id": 25, "name": "Supervisores, Operarios y Alisto"},
            {"id": 30, "name": "Comercio, Cajas y Servicio al Cliente"}
        ])
        self.max_pages_per_cat = ane_cfg.get("max_pages", 3)
        self.search_keywords = ane_cfg.get("search_keywords", [
            "soporte", "tecnic", "telecom", "redes", "sistemas", "noc", "comput",
            "ti", "it", "helpdesk", "service", "dato", "analis", "digitad",
            "inventari", "factura", "asistente", "auxiliar", "operador", "compras",
            "archivo", "oficina", "recepcion", "bodega", "back",
            "monitoreo", "cctv", "cajero", "caja", "alisto", "picking", "packing",
            "empaque", "inspector", "calidad", "encuestador", "almacen", "mensajero"
        ])

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []
        seen_keys = set()
        seen_titles = set()

        session = requests.Session()
        session.headers.update(self.get_headers())
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # 1. Exploración por categorías oficiales
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
                    resp = session.get(url, verify=False, timeout=15)
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

                        key = (title.lower(), company.lower(), location.lower())
                        if key in seen_keys:
                            continue

                        seen_titles.add(title.strip().lower())
                        category = self.evaluate_job(title)
                        if category:
                            seen_keys.add(key)
                            found_jobs.append({
                                "source": "ANE Costa Rica (ane.cr)",
                                "title": title,
                                "company": company,
                                "location": location,
                                "url": f"{self.BASE_URL}?Empleos={urllib.parse.quote(title)}",
                                "published_time": published_time,
                                "category": category
                            })

                    time.sleep(1.0)
                except Exception as e:
                    logger.error(f"[ANE] Error consultando categoría '{cat_name}' (Pág {page}): {e}")

        # 2. Sondeo activo por palabras clave vía AutoComplete de ANE
        discovered_titles = set()
        for kw in self.search_keywords:
            try:
                resp = session.post(
                    self.AUTOCOMPLETE_URL,
                    json={"KeyWord": kw},
                    verify=False,
                    timeout=10
                )
                if resp.status_code == 200:
                    for item in resp.json():
                        desc = item.get("DESCRIPCION", "").strip()
                        if desc and desc.lower() not in seen_titles:
                            discovered_titles.add(desc)
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"[ANE] Error en AutoComplete para '{kw}': {e}")

        # 3. Extraer vacantes directas para títulos descubiertos no presentes en categorías
        for title in discovered_titles:
            query_category = self.evaluate_job(title)
            if not query_category:
                continue

            query_url = f"{self.BASE_URL}?Empleos={urllib.parse.quote(title)}"
            try:
                resp = session.get(query_url, verify=False, timeout=12)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                listings = soup.find_all("div", class_="job-listing")
                for item in listings:
                    t_el = item.find("h3", class_="job-listing-title")
                    c_el = item.find("h4", class_="job-listing-company")
                    dt_el = item.find("small")
                    loc_el = item.find("li")

                    t_name = t_el.get_text(strip=True) if t_el else title
                    company = c_el.get_text(strip=True) if c_el else "Confidencial"
                    published_time = dt_el.get_text(strip=True) if dt_el else "Reciente"
                    location = loc_el.get_text(strip=True) if loc_el else "Costa Rica"

                    key = (t_name.lower(), company.lower(), location.lower())
                    if key in seen_keys:
                        continue

                    # Validar individualmente el título de la tarjeta
                    card_category = self.evaluate_job(t_name)
                    if not card_category:
                        continue

                    seen_keys.add(key)
                    found_jobs.append({
                        "source": "ANE Costa Rica (ane.cr)",
                        "title": t_name,
                        "company": company,
                        "location": location,
                        "url": query_url,
                        "published_time": published_time,
                        "category": card_category
                    })

                time.sleep(1.0)
            except Exception as e:
                logger.error(f"[ANE] Error extrayendo vacante '{title}': {e}")

        logger.info(f"[ANE] Encontradas {len(found_jobs)} ofertas coincidentes con tu perfil.")
        return found_jobs
