@echo off
title Controle de Estoque ITEC - Supabase PostgreSQL
cls
echo =========================================================
echo   INICIANDO CONTROLE DE ESTOQUE ITEC (SUPABASE POSTGRESQL)
echo =========================================================
echo.
cd /d "%~dp0"

:: Garantir dependências instaladas
python -m pip install flask psycopg2-binary python-dotenv --quiet

python run.py
pause
