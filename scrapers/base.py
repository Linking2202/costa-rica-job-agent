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
        - Perfil 1: Soporte TI / Tickets (Bilingüe ES/EN, Soporte Técnico, Technical Support, Tier 1, L1, Service Desk).
        - Perfil 2: Análisis de Datos / Bases de Datos (Solo Junior / Entry Level).
        - Perfil 3: Digitador, Data Entry, Data Management & Back Office Administrativo.
        - Exclusión global: Descarta puestos de Call Center telefónico / ventas salientes.
        """
        raw_text = f"{title} {description}"
        norm_text = strip_accents(raw_text)

        # 1. Filtro estricto de idiomas (Solo Español / Inglés)
        excluded_languages = self.config.get("excluded_languages", [
            "french", "frances", "francais",
            "portuguese", "portugues",
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

        # 2. Filtro de exclusión global
        global_exclusions = self.config.get("exclusions", [])
        for excl in global_exclusions:
            norm_excl = strip_accents(excl)
            pattern = rf"\b{re.escape(norm_excl)}\b"
            if re.search(pattern, norm_text):
                return None

        # 2.1 Exclusiones de ventas activas, telemercadeo y redes sociales
        if re.search(r"\b(vendedor|vendedora|ventas\s+(de|para)|asesor(a)?\s+de\s+ventas|promotor(a)?\s+de\s+ventas|supervisor(a)?\s+de\s+ventas|ejecutivo(a)?\s+de\s+ventas|televentas|redes\s+sociales|community\s*manager)\b", norm_text):
            return None

        # 2.2 Exclusiones de profesiones reguladas / médicas / docencia / oficios no relacionados
        if re.search(r"\b(quirurgico|quirurgica|enfermeria|enfermero|enfermera|medico|medica|dental|odontolog|veterinari|avicola|farmacia|farmaceutic|clinico|clinica|docente|profesor|profesora|maestro|maestra|sistemas\s+de\s+agua|acueducto|fontaneria|aguas\s+residuales|electromecanica\s+y\s+bombeo|tratamiento\s+de\s+agua|automotriz|mecanico\s+automotriz|soldador|soldadura|albanil|montacargas|extrusion|inyeccion)\b", norm_text):
            return None

        # 2.3 Exclusión de jefaturas y gerencias de alto nivel
        if re.search(r"\b(jefe\b|jefatura|gerente|director\b|directora|head\s+of)\b", norm_text):
            return None

        # 2.4 Exclusión estricta de contabilidad, crédito y cobro, cuentas por cobrar/pagar
        if re.search(r"\b(contable|contabilidad|contador[a]?|credito\s+(y|&)\s+cobro|cobro|cobros|cxc|cxp|cuentas\s+por\s+(cobrar|pagar)|accounting|accountant|bookkeeper|bookkeeping|auditoria|auditor[a]?|tesoreria)\b", norm_text):
            return None

        # 2.5 Exclusión de ciencia de datos avanzada, bases de datos avanzadas y master data
        if re.search(r"\b(master\s+data|data\s+science|ciencias?\s+de\s+datos|cientific[oa]\s+de\s+datos|data\s+scientist|data\s+engineer|ingenier[oa]\s+de\s+datos|dba\b|database\s+administrator|administrador(a)?\s+de\s+bases?\s+de\s+datos|data\s+architect|arquitect[oa]\s+de\s+datos|big\s+data)\b", norm_text):
            return None

        # 3. Perfil Datos (Solo Junior / Entry o nivel no especificado - descarta Senior, Data Science y Master Data)
        data_cfg = self.config.get("profiles", {}).get("data_analytics", {})
        data_keywords = data_cfg.get("keywords", [])
        data_exclusions = data_cfg.get("exclusions", [
            "senior", "sr.", "sr ", "lead", "principal", "director", "gerente",
            "master data", "data science", "ciencias de datos", "cientifico de datos", "dba", "data engineer"
        ])

        for kw in data_keywords:
            norm_kw = strip_accents(kw)
            pattern = rf"\b{re.escape(norm_kw)}\b"
            if re.search(pattern, norm_text):
                has_senior = any(re.search(rf"\b{re.escape(strip_accents(ex))}\b", norm_text) for ex in data_exclusions)
                is_junior = bool(re.search(r"\b(junior|jr\.?|trainee|entry|pasante|intern)\b", norm_text))
                if has_senior and not is_junior:
                    return None
                return "📊 Análisis de Datos (Junior / Entry)"

        # 4. Perfil Soporte TI, Redes & Telecomunicaciones
        it_cfg = self.config.get("profiles", {}).get("it_support", {})
        it_keywords = it_cfg.get("keywords", [])
        for kw in it_keywords:
            norm_kw = strip_accents(kw)
            pattern = rf"\b{re.escape(norm_kw)}\b"
            if re.search(pattern, norm_text):
                is_senior = bool(re.search(r"\b(senior|sr\.?|sr\b)", norm_text))
                badge = " (Senior)" if is_senior else ""
                return f"💻 Soporte TI & Telecomunicaciones{badge}"

        # 4.1 Coincidencia directa de Help Desk / Mesa de Ayuda / NOC / Telecom
        if re.search(r"\b(help\s*desk|helpdesk|service\s*desk|servicedesk|mesa\s*de\s*ayuda|cableado\s+estructurado|noc\s+(technician|operator|analyst)|soc\s+analyst)\b", norm_text):
            is_senior = bool(re.search(r"\b(senior|sr\.?|sr\b)", norm_text))
            badge = " (Senior)" if is_senior else ""
            return f"💻 Soporte TI & Telecomunicaciones{badge}"

        # 4.2 Coincidencia directa de Redes, Telecomunicaciones y SysAdmin
        if re.search(r"\b(telecomunicaciones|telecommunications|telecom|administrador\s+de\s+(redes|sistemas|telecomunicaciones|ti|it)|network\s+administrator|systems\s+administrator|sysadmin|network\s+engineer|ingeniero\s+de\s+(redes|telecomunicaciones|soporte|infraestructura)|tecnico\s+en\s+telecomunicaciones|tecnico\s+en\s+redes|infraestructura\s+y\s+redes)\b", norm_text):
            is_senior = bool(re.search(r"\b(senior|sr\.?|sr\b)", norm_text))
            badge = " (Senior)" if is_senior else ""
            return f"💻 Soporte TI & Telecomunicaciones{badge}"

        # 4.3 Regla flexible de tecnología y soporte (Rol técnico + Dominio de TI)
        has_tech_role = bool(re.search(r"\b(tecnico|tecnica|technician|soporte|soportista|support|administrador|administrator|ingeniero|engineer|analista|analyst|especialista|specialist|operador|operator|asistente|auxiliar)\b", norm_text))
        has_tech_domain = bool(re.search(r"\b(ti|it|sistemas|systems|redes|network|networking|telecomunicaciones|telecom|telecommunications|computo|computacion|informatica|informatico|hardware|servidores|server|servers|desktop|nivel\s*(1|i|2|ii|3|iii)|tier\s*(1|i|2|ii|3|iii)|level\s*(1|i|2|ii|3|iii)|l1|l2|l3|ticket|ticketing|incident|incidente|noc|soc|infraestructura|infrastructure|active\s*directory|jira|cloud|technical|soporte|soportista)\b", norm_text))
        if has_tech_role and has_tech_domain and "soporte de eventos" not in norm_text:
            is_senior = bool(re.search(r"\b(senior|sr\.?|sr\b)", norm_text))
            badge = " (Senior)" if is_senior else ""
            return f"💻 Soporte TI & Telecomunicaciones{badge}"

        # 5. Perfil Digitación & Entrada de Datos
        if re.search(r"\b(digitador|digitadora|data\s*entry|transcriptor|transcriptora|captura\s+de\s+datos|ingreso\s+de\s+datos|digitacion|digitalizador|digitalizadora|operador\s+de\s+datos|operadora\s+de\s+datos|digitador\s+tica)\b", norm_text):
            return "📝 Digitación & Entrada de Datos"

        # 6. Perfil Control de Inventarios, Bodega & Logística Accesible
        if re.search(r"\b(control\s+de\s+inventario|control\s+de\s+inventarios|auxiliar\s+de\s+inventarios|auxiliar\s+de\s+inventario|bodeguero\s+de\s+inventarios|bodega\s+e\s+inventarios|bodeguero\s*\(?a\)?\s+de\s+inventarios|asistente\s+de\s+inventarios|auxiliar\s+de\s+bodega|asistente\s+de\s+bodega|almacenista|almacen\s+e\s+inventarios|alisto-bodega|alistador\s+de\s+bodega|auxiliar\s+logistico|asistente\s+logistica|despacho\s+de\s+contenedores|auxiliar\s+aduanal)\b", norm_text):
            return "📦 Control de Inventarios & Bodega"

        # 7. Perfil Facturación & Asistente de Compras
        if re.search(r"\b(facturador|facturadora|facturacion|asistente\s+de\s+facturacion|auxiliar\s+de\s+facturacion|chequeador\s*,\s*facturador|asistente\s+de\s+compras|auxiliar\s+de\s+compras|auxiliar\s+de\s+oficina\s+para\s+compras|compras\s+y\s+proveeduria)\b", norm_text):
            return "🧾 Facturación & Asistente de Compras"

        # 8. Perfil Auxiliar Administrativo, Oficina & Operaciones (Sin contabilidad / sin crédito y cobro)
        if re.search(r"\b(asistente\s+administrativo|asistente\s+administrativa|auxiliar\s+administrativo|auxiliar\s+administrativa|asistente\s+de\s+oficina|auxiliar\s+de\s+oficina|oficinista|asistente\s+de\s+operaciones|auxiliar\s+de\s+operaciones|back\s*office|backoffice|gestor\s+documental|gestora\s+documental|auxiliar\s+de\s+archivo|recepcionista|recepcionista\s+bilingue|recepcionista\s+bilingüe|asistente\s+de\s+licitaciones)\b", norm_text):
            return "📋 Auxiliar Administrativo, Oficina & Operaciones"

        # 9. Coincidencias de configuración de fallback
        bo_cfg = self.config.get("profiles", {}).get("backoffice_digitacion", {})
        for kw in bo_cfg.get("keywords", []):
            norm_kw = strip_accents(kw)
            if re.search(rf"\b{re.escape(norm_kw)}\b", norm_text):
                return "📝 Digitación & Back Office"

        return None
