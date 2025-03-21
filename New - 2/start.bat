@echo off

:: Verifica se o Python está instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python não está instalado. Por favor, instale o Python e tente novamente.
    pause
    exit /b
)

:: Ativa o ambiente virtual, se existir
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: Verifica e instala dependências
echo Verificando dependências...
python -m pip install --upgrade pip >nul 2>nul
python -m pip install matplotlib >nul 2>nul

:: Verifica e limpa o cache, se necessário
set CACHE_FILE=data_cache.json
if exist %CACHE_FILE% (
    echo Verificando cache...
    python -c "import json, os; from datetime import datetime; from pathlib import Path; \
try: \
    with open('%CACHE_FILE%', 'r') as f: \
        cache = json.load(f); \
        if 'timestamps' in cache and cache['timestamps']: \
            last_timestamp = datetime.fromisoformat(cache['timestamps'][-1]); \
            if last_timestamp.date() < datetime.now().date(): \
                print('Cache é do dia anterior. Limpando...'); \
                Path('%CACHE_FILE%').unlink(); \
except (json.JSONDecodeError, ValueError): \
    print('Erro ao ler o cache. Limpando...'); \
    Path('%CACHE_FILE%').unlink()"
)

:: Inicia a aplicação
echo Iniciando aplicação...
python main.py
pause
