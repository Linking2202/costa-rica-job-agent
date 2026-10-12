import time
import logging
import requests
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class WorkdayScraper(BaseScraper):
    """
    Scraper oficial para portales corporativos de Workday (*.myworkdayjobs.com).
    Conecta directamente con la API REST interna (CXS) de las principales
    empresas multinacionales con centros de operaciones en Costa Rica:
    - Abbott Costa Rica
    - Procter & Gamble (P&G)
    - Pfizer Costa Rica
    - Stryker Costa Rica
    - JLL Costa Rica
    - TransUnion Costa Rica
    - Sysco Costa Rica
    - Workday Inc (Costa Rica Hub)
    """

    DEFAULT_COMPANIES = [
        {
            "name": "Abbott",
            "api_url": "https://abbott.wd5.myworkdayjobs.com/wday/cxs/abbott/abbottcareers/jobs",
            "base_url": "https://abbott.wd5.myworkdayjobs.com/en-US/abbottcareers"
        },
        {
            "name": "Procter & Gamble (P&G)",
            "api_url": "https://pg.wd5.myworkdayjobs.com/wday/cxs/pg/1000/jobs",
            "base_url": "https://pg.wd5.myworkdayjobs.com/en-US/1000"
        },
        {
            "name": "Pfizer",
            "api_url": "https://pfizer.wd1.myworkdayjobs.com/wday/cxs/pfizer/PfizerCareers/jobs",
            "base_url": "https://pfizer.wd1.myworkdayjobs.com/en-US/PfizerCareers"
        },
        {
            "name": "Stryker",
            "api_url": "https://stryker.wd1.myworkdayjobs.com/wday/cxs/stryker/StrykerCareers/jobs",
            "base_url": "https://stryker.wd1.myworkdayjobs.com/en-US/StrykerCareers"
        },
        {
            "name": "JLL",
            "api_url": "https://jll.wd1.myworkdayjobs.com/wday/cxs/jll/jllcareers/jobs",
            "base_url": "https://jll.wd1.myworkdayjobs.com/en-US/jllcareers"
        },
        {
            "name": "TransUnion",
            "api_url": "https://transunion.wd5.myworkdayjobs.com/wday/cxs/transunion/TransUnion/jobs",
            "base_url": "https://transunion.wd5.myworkdayjobs.com/en-US/TransUnion"
        },
        {
            "name": "Sysco",
            "api_url": "https://sysco.wd5.myworkdayjobs.com/wday/cxs/sysco/SyscoCareers/jobs",
            "base_url": "https://sysco.wd5.myworkdayjobs.com/en-US/SyscoCareers"
        },
        {
            "name": "Workday",
            "api_url": "https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs",
            "base_url": "https://workday.wd5.myworkdayjobs.com/en-US/Workday"
        }
    ]

    def __init__(self, config: dict):
        super().__init__("Workday Portales CR", config)
        wd_cfg = config.get("sources", {}).get("workday", {})
        self.companies = wd_cfg.get("companies", self.DEFAULT_COMPANIES)
        self.search_queries = wd_cfg.get("queries", ["Costa Rica"])
        self.max_jobs_per_company = wd_cfg.get("limit_per_company", 20)

    def fetch_jobs(self) -> List[Dict]:
        found_jobs = []
        seen_keys = set()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        logger.info(f"[Workday] Iniciando sondeo directo en {len(self.companies)} portales de Workday en Costa Rica...")

        for comp in self.companies:
            comp_name = comp.get("name", "Multinacional")
            api_url = comp.get("api_url", "")
            base_url = comp.get("base_url", "")

            if not api_url or not base_url:
                continue

            for query in self.search_queries:
                payload = {
                    "appliedFacets": {},
                    "limit": self.max_jobs_per_company,
                    "offset": 0,
                    "searchText": query
                }

                try:
                    resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    postings = data.get("jobPostings", [])

                    for job in postings:
                        title = job.get("title", "").strip()
                        location = job.get("locationsText", "Costa Rica").strip()
                        path = job.get("externalPath", "")
                        posted_on = job.get("postedOn", "Reciente").strip()

                        if not title:
                            continue

                        # Validar que la posición corresponda geográficamente a Costa Rica
                        loc_lower = location.lower()
                        title_lower = title.lower()
                        is_cr = any(kw in loc_lower or kw in title_lower for kw in [
                            "costa rica", "costa_rica", "heredia", "san jose", "san josé",
                            "alajuela", "cartago", "belen", "belén", "grecia", "coyol",
                            "ulloa", "lagunilla", "cri"
                        ])

                        if not is_cr:
                            continue

                        key = (title.lower(), comp_name.lower(), location.lower())
                        if key in seen_keys:
                            continue

                        category = self.evaluate_job(title)
                        if category:
                            seen_keys.add(key)
                            full_url = f"{base_url}{path}" if path.startswith("/") else f"{base_url}/{path}"
                            found_jobs.append({
                                "source": f"Workday - {comp_name}",
                                "title": title,
                                "company": f"{comp_name} Costa Rica",
                                "location": location,
                                "url": full_url,
                                "published_time": posted_on,
                                "category": category
                            })

                    time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"[Workday] Error consultando portal de {comp_name}: {e}")

        logger.info(f"[Workday] Sondeo completado: {len(found_jobs)} ofertas coincidentes encontradas.")
        return found_jobs
