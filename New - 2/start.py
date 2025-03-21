import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import json

# Lista de dependências necessárias
DEPENDENCIES = [
    "matplotlib"
]

# Função para verificar e instalar dependências
def check_and_install_dependencies():
    for package in DEPENDENCIES:
        try:
            __import__(package)
        except ImportError:
            print(f"Pacote '{package}' não encontrado. Instalando...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Função para verificar e limpar o cache, se necessário
def check_and_clear_cache():
    cache_file = Path("data_cache.json")
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cache = json.load(f)
                if "timestamps" in cache and cache["timestamps"]:
                    last_timestamp = datetime.fromisoformat(cache["timestamps"][-1])
                    if last_timestamp.date() < datetime.now().date():
                        print("Cache é do dia anterior. Limpando...")
                        cache_file.unlink()
        except (json.JSONDecodeError, ValueError):
            print("Erro ao ler o cache. Limpando...")
            cache_file.unlink()

# Função principal para iniciar a aplicação
def main():
    print("Verificando dependências...")
    check_and_install_dependencies()
    print("Verificando cache...")
    check_and_clear_cache()
    print("Iniciando aplicação...")
    os.system(f"{sys.executable} main.py")

if __name__ == "__main__":
    main()
