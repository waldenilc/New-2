import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import threading

# Bloqueio para sincronizar o acesso ao arquivo de log
log_lock = threading.Lock()

class CustomFormatter(logging.Formatter):
    """Formatador personalizado para logs"""
    def format(self, record):
        record.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return super().format(record)

def setup_logger(name='ABDM'):
    """Configura o logger com saída para arquivo e console"""
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger  # Evita configurar o logger múltiplas vezes

    logger.setLevel(logging.DEBUG)

    # Criar diretório de logs se não existir
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8',
        delay=True  # Abre o arquivo apenas quando necessário
    )
    file_handler.setLevel(logging.DEBUG)

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formato detalhado para arquivo
    file_formatter = CustomFormatter(
        '%(timestamp)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Formato simplificado para console
    console_formatter = CustomFormatter('%(timestamp)s | %(levelname)-8s | %(message)s')
    console_handler.setFormatter(console_formatter)

    # Adiciona o bloqueio ao handler de arquivo
    class LockedRotatingFileHandler(RotatingFileHandler):
        def emit(self, record):
            with log_lock:
                super().emit(record)

    # Substitui o handler padrão pelo handler com bloqueio
    logger.addHandler(LockedRotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
        delay=True
    ))
    logger.addHandler(console_handler)

    return logger
