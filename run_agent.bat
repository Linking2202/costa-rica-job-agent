@echo off
title Agente Monitor de Empleos Costa Rica - WhatsApp
cd /d "%~dp0"
echo Iniciando Agente de Empleos (Modo Continuo)...
call .\.venv\Scripts\python.exe agent.py --daemon
pause
