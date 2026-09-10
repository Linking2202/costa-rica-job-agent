import re
import random
import logging
import unicodedata
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def strip_accents(text: str) -> str:
    """Elimina acentos y tildes para comparaciones robustas en español e inglés."""
    if not text:
        return ""
    text_nfkd = unicodedata.normalize('NFKD', text)
    return "".join([c for c in text_nfkd if not unicodedata.combining(c)]).lower()

class BaseScraper(ABC):
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "es-CR,es-419;q=0.9,es;q=0.8,en-US;q=0.7,en;q=0.6",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Connection": "keep-alive"
        }

    @abstractmethod
    def fetch_jobs(self) -> List[Dict]:
        """Extrae ofertas recientes y devuelve una lista de diccionarios normalizados."""
        pass

    def evaluate_job(self, title: str, description: str = "") -> Optional[str]:
        """
        Evalúa si la oferta coincide con el perfil de Luis Diego:
        - Idiomas permitidos: ÚNICAMENTE Español e Inglés.
        - Perfil 1: Soporte TI / Tickets (Permite Senior / Mid / Junior).
        - Perfil 2: Análisis de Datos / Bases de Datos (Solo Junior / Entry).
        - Perfil 3: Digitador, Data Entry & Back Office Administrativo (Excel, SAP, Inventario, Logística).
        - Exclusión global: Descarta puestos de Call Center telefónico.
        """
        raw_text = f"{title} {description}"
        norm_text = strip_accents(raw_text)

        # 1. Filtro estricto de idiomas (Solo Español / Inglés)
        excluded_languages = self.config.get("excluded_languages", [
            "french", "frances", "francais",
            "portuguese", "portugues", "portugues",
            "german", "aleman", "deutsch",
            "italian", "italiano",
            "mandarin", "chinese", "chino",
            "dutch", "holandes", "nederlands",
            "japanese", "japones",
            "russian", "ruso",
            "korean", "coreano"
        ])
        for lang in excluded_languages:
            norm_lang = strip_accents(lang)
            if re.search(rf"\b{re.escape(norm_lang)}\b", norm_text):
                return None

        # 2. Filtro de exclusión global (no llamadas telefónicas / call center)
        global_exclusions = self.config.get("exclusions", [])
        for excl in global_exclusions:
            norm_excl = strip_accents(excl)
            pattern = rf"\b{re.escape(norm_excl)}\b"
            if re.search(pattern, norm_text):
                return None

        # 3. Perfil Datos (Solo Junior / Entry - descarta Senior en Datos/BD)
        data_cfg = self.config.get("profiles", {}).get("data_analytics", {})
        data_keywords = data_cfg.get("keywords", [])
        data_exclusions = data_cfg.get("exclusions", ["senior", "sr.", "sr ", "lead", "principal"])

        for kw in data_keywords:
            norm_kw = strip_accents(kw)
            pattern = rf"\b{re.escape(norm_kw)}\b"
            if re.search(pattern, norm_text):
                has_senior = any(re.search(rf"\b{re.escape(strip_accents(ex))}\b", norm_text) for ex in data_exclusions)
                is_junior = bool(re.search(r"\b(junior|jr\.?|trainee|entry|pasante)\b", norm_text))
                if has_senior and not is_junior:
                    return None
                return "📊 Análisis de Datos (Junior / Entry)"

        # 4. Perfil Soporte TI / Tickets (Aquí SÍ se permiten vacantes Senior)
        it_cfg = self.config.get("profiles", {}).get("it_support", {})
        it_keywords = it_cfg.get("keywords", [])
        for kw in it_keywords:
            norm_kw = strip_accents(kw)
            pattern = rf"\b{re.escape(norm_kw)}\b"
            if re.search(pattern, norm_text):
                is_senior = bool(re.search(r"\b(senior|sr\.?|sr\b)", norm_text))
                badge = " (Senior)" if is_senior else ""
                return f"💻 Soporte TI & Tickets{badge} (Onsite / Backoffice)"

        # 5. Regla flexible de combinaciones de soporte técnico y redes (permite Senior)
        has_soporte = bool(re.search(r"\bsoporte\b", norm_text))
        has_tech = bool(re.search(r"\b(tecnico|ti|it|computo|informatica|usuario|help\s*desk|service\s*desk)\b", norm_text))
        if has_soporte and has_tech:
            is_senior = bool(re.search(r"\b(senior|sr\.?|sr\b)", norm_text))
            badge = " (Senior)" if is_senior else ""
            return f"💻 Soporte TI & Tickets{badge} (Onsite / Backoffice)"

        # 6. Perfil Digitador / Data Entry / Back Office Administrativo
        bo_cfg = self.config.get("profiles", {}).get("backoffice_digitacion", {})
        bo_keywords = bo_cfg.get("keywords", [])
        for kw in bo_keywords:
            norm_kw = strip_accents(kw)
            pattern = rf"\b{re.escape(norm_kw)}\b"
            if re.search(pattern, norm_text):
                # Si es cargo de gerencia o jefe, ignorar
                if re.search(r"\b(jefe|jefatura|gerente|director)\b", norm_text):
                    return None
                return "📝 Digitador & Back Office (Excel / SAP / Operaciones)"

        return None
