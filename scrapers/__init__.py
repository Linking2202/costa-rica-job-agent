from scrapers.linkedin import LinkedInScraper
from scrapers.computrabajo import ComputrabajoScraper
from scrapers.talent import TalentScraper
from scrapers.elempleo import ElEmpleoScraper

def get_active_scrapers(config: dict):
    scrapers = []
    sources_cfg = config.get("sources", {})

    if sources_cfg.get("linkedin", {}).get("enabled", True):
        scrapers.append(LinkedInScraper(config))

    if sources_cfg.get("computrabajo", {}).get("enabled", True):
        scrapers.append(ComputrabajoScraper(config))

    if sources_cfg.get("talent", {}).get("enabled", True):
        scrapers.append(TalentScraper(config))

    if sources_cfg.get("elempleo", {}).get("enabled", True):
        scrapers.append(ElEmpleoScraper(config))

    return scrapers
