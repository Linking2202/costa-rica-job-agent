@echo off
title Subir a GitHub
cd /d "%~dp0"
echo Conectando con tu repositorio en GitHub...
echo.
C:\Users\123\.mingit\cmd\git.exe push -u origin main
echo.
echo Proceso finalizado.
pause
