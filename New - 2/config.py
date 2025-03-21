from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class ServerConfig:
    host: str = '127.0.0.1'
    port: int = 557
    buffer_size: int = 65536
    encoding: str = 'utf-8'
    init_command: str = 'OPENFAST'
    field_separator: str = '\001'

@dataclass
class AppConfig:
    update_interval: float = 0.5
    asset: str = 'WINJ25'
    period: int = 0
    log_file: Path = Path('app.log')
