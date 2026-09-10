import logging
import requests
from notifier.base import BaseNotifier

logger = logging.getLogger(__name__)

class TwilioWhatsAppNotifier(BaseNotifier):
    """Notificador usando la API REST de Twilio WhatsApp Sandbox/Production."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str):
        self.account_sid = account_sid.strip()
        self.auth_token = auth_token.strip()
        self.from_number = from_number.strip()
        self.to_number = to_number.strip()
        self.url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

    def send_message(self, message: str) -> bool:
        if not (self.account_sid and self.auth_token and self.to_number):
            logger.warning("[Twilio] Credenciales no configuradas.")
            return False

        from_str = self.from_number if self.from_number.startswith("whatsapp:") else f"whatsapp:{self.from_number}"
        to_str = self.to_number if self.to_number.startswith("whatsapp:") else f"whatsapp:{self.to_number}"

        data = {
            "From": from_str,
            "To": to_str,
            "Body": message
        }

        try:
            resp = requests.post(self.url, data=data, auth=(self.account_sid, self.auth_token), timeout=15)
            if resp.status_code in [200, 201]:
                logger.info("[Twilio] Alerta enviada por WhatsApp.")
                return True
            else:
                logger.error(f"[Twilio] Error: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"[Twilio] Excepción: {e}")
            return False

    def send_job_alert(self, job: dict) -> bool:
        msg = (
            f"🚨 *NUEVA VACANTE (COSTA RICA)* 🇨🇷\n\n"
            f"💼 *Puesto:* {job.get('title')}\n"
            f"🏢 *Empresa:* {job.get('company')}\n"
            f"📍 *Ubicación:* {job.get('location')}\n"
            f"🌐 *Fuente:* {job.get('source')}\n\n"
            f"🔗 *Enlace:* {job.get('url')}"
        )
        return self.send_message(msg)

