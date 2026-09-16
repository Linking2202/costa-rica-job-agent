from scrapers.linkedin import LinkedInScraper
from scrapers.computrabajo import ComputrabajoScraper
from scrapers.talent import TalentScraper
from scrapers.elempleo import ElEmpleoScraper
from scrapers.unmejorempleo import UnMejorEmpleoScraper
from scrapers.getonbrd import GetOnBrdScraper
from scrapers.companies import CompaniesScraper

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

    if sources_cfg.get("unmejorempleo", {}).get("enabled", True):
        scrapers.append(UnMejorEmpleoScraper(config))

    if sources_cfg.get("getonbrd", {}).get("enabled", True):
        scrapers.append(GetOnBrdScraper(config))

    if sources_cfg.get("companies", {}).get("enabled", True):
        scrapers.append(CompaniesScraper(config))

    return scrapers
