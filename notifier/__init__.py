import os
import sys
import logging
from notifier.base import BaseNotifier
from notifier.whatsapp_callmebot import CallMeBotWhatsAppNotifier
from notifier.whatsapp_twilio import TwilioWhatsAppNotifier
from notifier.telegram import TelegramNotifier

logger = logging.getLogger(__name__)

class ConsoleNotifier(BaseNotifier):
    """Notificador por consola en caso de que aún no se configuren credenciales."""
    def send_message(self, message: str) -> bool:
        print("\n" + "="*50)
        print("[NOTIFICACIÓN SIMULADA]")
        try:
            print(message)
        except Exception:
            print(message.encode("ascii", "replace").decode("ascii"))
        print("="*50 + "\n")
        return True

    def send_job_alert(self, job: dict) -> bool:
        return self.send_message(
            f"🚨 [SIMULACIÓN] Nueva vacante: {job.get('title')} en {job.get('company')} ({job.get('location')})\n"
            f"📌 Perfil: {job.get('category')}\n"
            f"🌐 Fuente: {job.get('source')}\n"
            f"🔗 Link: {job.get('url')}"
        )

def get_notifier() -> BaseNotifier:
    provider = os.getenv("ALERT_CHANNEL", os.getenv("WHATSAPP_PROVIDER", "callmebot")).lower()

    if provider == "telegram":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if token and chat_id and token != "tu_bot_token_aqui":
            return TelegramNotifier(token=token, chat_id=chat_id)
        else:
            logger.warning("[Notifier] Token de Telegram incompleto. Usando modo Consola simulado.")
            return ConsoleNotifier()

    elif provider == "callmebot":
        phone = os.getenv("CALLMEBOT_PHONE", "")
        api_key = os.getenv("CALLMEBOT_API_KEY", "")
        if phone and api_key and api_key != "tu_api_key_aqui":
            return CallMeBotWhatsAppNotifier(phone=phone, api_key=api_key)
        else:
            logger.warning("[Notifier] Credenciales CallMeBot no configuradas. Usando modo Consola simulado.")
            return ConsoleNotifier()

    elif provider == "twilio":
        sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        token = os.getenv("TWILIO_AUTH_TOKEN", "")
        from_num = os.getenv("TWILIO_FROM_NUMBER", "")
        to_num = os.getenv("TWILIO_TO_NUMBER", "")
        if sid and token and to_num:
            return TwilioWhatsAppNotifier(account_sid=sid, auth_token=token, from_number=from_num, to_number=to_num)
        else:
            logger.warning("[Notifier] Credenciales Twilio incompletas. Usando modo Consola simulado.")
            return ConsoleNotifier()

    return ConsoleNotifier()
