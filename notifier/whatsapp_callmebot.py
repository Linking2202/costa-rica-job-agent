import urllib.parse
import requests
import logging
from notifier.base import BaseNotifier

logger = logging.getLogger(__name__)

class CallMeBotWhatsAppNotifier(BaseNotifier):
    """
    Notificador de WhatsApp usando CallMeBot API.
    Totalmente gratuito y sin necesidad de crear cuenta empresarial en Meta.
    Para activarlo:
    1. Guarda en tus contactos el número: +34 911 06 16 35 (o el bot indicado por CallMeBot)
    2. Envía un mensaje por WhatsApp que diga: 'I allow callmebot to send me messages'
    3. Recibirás tu API Key inmediatamente en WhatsApp.
    """

    def __init__(self, phone: str, api_key: str):
        self.phone = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
        self.api_key = api_key.strip()
        self.base_url = "https://api.callmebot.com/whatsapp.php"

    def send_message(self, message: str) -> bool:
        if not self.phone or not self.api_key:
            logger.warning("[WhatsApp] Número o API Key no configurados en .env")
            return False

        params = {
            "phone": self.phone,
            "text": message,
            "apikey": self.api_key
        }

        try:
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200 and ("Message queued" in resp.text or "ok" in resp.text.lower()):
                logger.info(f"[WhatsApp] Mensaje enviado exitosamente a {self.phone}")
                return True
            else:
                logger.error(f"[WhatsApp] Error al enviar mensaje: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"[WhatsApp] Excepción al enviar mensaje: {e}")
            return False

    def send_job_alert(self, job: dict) -> bool:
        title = job.get("title", "Vacante")
        company = job.get("company", "Empresa Confidencial")
        location = job.get("location", "Costa Rica")
        source = job.get("source", "Portal de Empleo")
        url = job.get("url", "")
        match_category = job.get("category", "Coincidencia con tu perfil")

        msg = (
            f"🚨 *¡NUEVO PUESTO EN COSTA RICA!* 🇨🇷\n\n"
            f"📌 *Perfil:* {match_category}\n"
            f"💼 *Puesto:* {title}\n"
            f"🏢 *Empresa:* {company}\n"
            f"📍 *Ubicación:* {location}\n"
            f"🌐 *Fuente:* {source}\n\n"
            f"⚡ *Postúlate de primero aquí:*\n{url}"
        )
        return self.send_message(msg)

