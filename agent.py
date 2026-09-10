import os
import sys

# Forzar soporte UTF-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import time
import argparse
import logging
from pathlib import Path
import yaml
from dotenv import load_dotenv
import schedule

# Cargar variables de entorno
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

from database import init_db, is_job_seen, save_job, get_stats, generate_job_id
from notifier import get_notifier
from scrapers import get_active_scrapers

# Configurar logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("JobAgent")

def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        logger.error(f"Archivo {config_path} no encontrado.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_scan_cycle(config: dict, notifier):
    """Ejecuta un ciclo completo de escaneo en todas las fuentes configuradas."""
    logger.info("🔍 Iniciando ciclo de búsqueda de ofertas laborales en Costa Rica...")
    scrapers = get_active_scrapers(config)
    max_alerts = config.get("agent", {}).get("max_alerts_per_cycle", 10)
    
    new_jobs_count = 0
    alerts_sent = 0

    for scraper in scrapers:
        try:
            logger.info(f"📡 Consultando {scraper.name}...")
            jobs = scraper.fetch_jobs()
            logger.info(f"Total extraídas de {scraper.name}: {len(jobs)}")

            for job in jobs:
                job_id = generate_job_id(
                    job.get("source", ""),
                    job.get("url", ""),
                    job.get("title", ""),
                    job.get("company", "")
                )
                job["id"] = job_id

                if not is_job_seen(job_id):
                    new_jobs_count += 1
                    # Guardar en base de datos para no repetir
                    save_job(job)
                    logger.info(f"🎯 ¡NUEVA VACANTE!: {job['title']} en {job['company']} ({job['source']})")

                    if alerts_sent < max_alerts:
                        success = notifier.send_job_alert(job)
                        if success:
                            alerts_sent += 1
                        time.sleep(2.5) # Pausa cortés entre mensajes
                    else:
                        logger.warning("⚠️ Se alcanzó el límite de alertas por ciclo para no saturar tu WhatsApp.")

        except Exception as e:
            logger.error(f"Error al ejecutar scraper {scraper.name}: {e}", exc_info=True)

    logger.info(f"✅ Ciclo finalizado. Nuevas ofertas detectadas: {new_jobs_count}, Alertas WhatsApp enviadas: {alerts_sent}")

def test_whatsapp(notifier):
    """Envía un mensaje de prueba al WhatsApp configurado."""
    test_msg = (
        "👋 ¡Hola Luis Diego!\n\n"
        "🤖 Tu Agente de Empleos de Costa Rica está listo y conectado con éxito.\n"
        "Te notificaré de inmediato cada vez que aparezca un nuevo puesto de:\n"
        "  • Análisis de Datos Junior\n"
        "  • Soporte TI y Tickets (Onsite / Backoffice sin llamadas)\n\n"
        "¡Estarás de primero en enterarte! 🇨🇷⚡"
    )
    logger.info("Enviando mensaje de prueba...")
    success = notifier.send_message(test_msg)
    if success:
        logger.info("✅ ¡Mensaje de prueba entregado con éxito!")
    else:
        logger.error("❌ Falló el envío del mensaje de prueba. Verifica tu .env")

def main():
    parser = argparse.ArgumentParser(description="Agente Monitor de Empleos para Costa Rica")
    parser.add_argument("--run-once", action="store_true", help="Ejecuta un único ciclo de escaneo y termina.")
    parser.add_argument("--test-whatsapp", action="store_true", help="Envía un mensaje de prueba a tu WhatsApp.")
    parser.add_argument("--stats", action="store_true", help="Muestra estadísticas de vacantes detectadas.")
    parser.add_argument("--daemon", action="store_true", help="Ejecuta el agente de forma continua según el intervalo.")
    args = parser.parse_args()

    init_db()
    config = load_config()
    notifier = get_notifier()

    if args.test_whatsapp:
        test_whatsapp(notifier)
        return

    if args.stats:
        stats = get_stats()
        print("\n" + "="*40)
        print("📊 ESTADÍSTICAS DEL AGENTE")
        print(f"Total vacantes registradas: {stats['total_jobs']}")
        print("Por fuente:", stats['by_source'])
        print("="*40 + "\n")
        return

    if args.run_once or not args.daemon:
        run_scan_cycle(config, notifier)
        return

    if args.daemon:
        interval = config.get("agent", {}).get("scan_interval_minutes", 15)
        logger.info(f"🚀 Agente iniciado en modo continuo. Escaneando cada {interval} minutos. Presiona Ctrl+C para detener.")
        run_scan_cycle(config, notifier)
        schedule.every(interval).minutes.do(run_scan_cycle, config=config, notifier=notifier)

        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    main()
