import os
import logging
import requests
from notifier.base import BaseNotifier

logger = logging.getLogger(__name__)

class TelegramNotifier(BaseNotifier):
    """
    Notificador de Telegram.
    100% gratuito, sin límites de capacidad y creado en 30 segundos:
    1. En Telegram buscas @BotFather
    2. Envías /newbot y te da tu TOKEN
    3. Le escribes a tu bot y obtienes tu CHAT_ID
    """
    def __init__(self, token: str, chat_id: str):
        self.token = token.strip()
        self.chat_id = chat_id.strip()
        self.url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            logger.warning("[Telegram] Token o Chat ID no configurados.")
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            resp = requests.post(self.url, json=payload, timeout=10)
            if resp.status_code == 200 and resp.json().get("ok"):
                logger.info("[Telegram] Alerta enviada con éxito.")
                return True
            else:
                # Si markdown falla por caracteres especiales, enviar en texto plano
                payload.pop("parse_mode", None)
                resp = requests.post(self.url, json=payload, timeout=10)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"[Telegram] Error enviando mensaje: {e}")
            return False

    def send_job_alert(self, job: dict) -> bool:
        msg = (
            f"🚨 *¡NUEVO PUESTO EN COSTA RICA!* 🇨🇷\n\n"
            f"📌 *Perfil:* {job.get('category')}\n"
            f"💼 *Puesto:* {job.get('title')}\n"
            f"🏢 *Empresa:* {job.get('company')}\n"
            f"📍 *Ubicación:* {job.get('location')}\n"
            f"🌐 *Fuente:* {job.get('source')}\n\n"
            f"⚡ *Postúlate de primero aquí:*\n{job.get('url')}"
        )
        return self.send_message(msg)
