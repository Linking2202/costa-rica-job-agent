@echo off
title Probar Notificacion de WhatsApp
cd /d "%~dp0"
echo Enviando mensaje de prueba a tu WhatsApp...
call .\.venv\Scripts\python.exe agent.py --test-whatsapp
pause
