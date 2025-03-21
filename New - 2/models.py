from dataclasses import dataclass, field  # Adicionado import de field
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import json
from pathlib import Path
from utils.logger import setup_logger

# Configuração do logger
logger = setup_logger('ABDM.Models')

@dataclass
class BrokerData:
    timestamp: datetime
    name: str
    volume: float
    avg_price: float
    aggr_buy: float
    aggr_sell: float
    net_aggr: float
    passive_net: float
    gross_pl: float

    def to_row(self) -> List:
        return [
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.name,
            f"{self.volume:,.0f}",
            f"{self.avg_price:.2f}",
            f"{self.aggr_buy:,.0f}",
            f"{self.aggr_sell:,.0f}",
            f"{self.net_aggr:,.0f}",
            f"{self.passive_net:,.0f}",
            f"{self.gross_pl:,.0f}"
        ]

@dataclass
class MarketData:
    ultimo_preco: Optional[float] = None
    net_saldo_passivo_liquido: float = 0
    net_saldo_passivo_varejo: float = 0
    net_saldo_agressivo_varejo: float = 0

@dataclass
class HistoricalData:
    timestamps: deque = field(default_factory=lambda: deque(maxlen=1000))
    passive_liquido: deque = field(default_factory=lambda: deque(maxlen=1000))
    passive_varejo: deque = field(default_factory=lambda: deque(maxlen=1000))
    aggressive_varejo: deque = field(default_factory=lambda: deque(maxlen=1000))
    net_varejo: deque = field(default_factory=lambda: deque(maxlen=1000))

    def __post_init__(self):
        self.logger = setup_logger('ABDM.Models.Historical')
        self.logger.info("Inicializando HistoricalData")
        self.data_file = Path('historical_data.json')
        self.load_data()

    def add_point(self, timestamp: datetime, values: Dict[str, float]):
        """Adiciona um novo ponto aos dados históricos"""
        try:
            self.timestamps.append(timestamp)
            self.passive_liquido.append(values.get('passive_liquido', 0))
            self.passive_varejo.append(values.get('passive_varejo', 0))
            self.aggressive_varejo.append(values.get('aggressive_varejo', 0))
            self.net_varejo.append(values.get('net_varejo', 0))
            
            self.logger.debug(
                f"Ponto adicionado - Timestamp: {timestamp}, "
                f"Valores: passive_liquido={values.get('passive_liquido', 0)}, "
                f"passive_varejo={values.get('passive_varejo', 0)}, "
                f"aggressive_varejo={values.get('aggressive_varejo', 0)}, "
                f"net_varejo={values.get('net_varejo', 0)}"
            )
            self.save_data()  # Salva os dados após adicionar um novo ponto
        except Exception as e:
            self.logger.error(f"Erro ao adicionar ponto: {e}", exc_info=True)
            raise

    def save_data(self):
        """Salva os dados históricos em um arquivo JSON"""
        try:
            data = {
                'timestamps': [ts.isoformat() for ts in self.timestamps],
                'passive_liquido': list(self.passive_liquido),
                'passive_varejo': list(self.passive_varejo),
                'aggressive_varejo': list(self.aggressive_varejo),
                'net_varejo': list(self.net_varejo),
            }
            with self.data_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info("Dados históricos salvos com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados históricos: {e}", exc_info=True)

    def load_data(self):
        """Carrega os dados históricos de um arquivo JSON"""
        try:
            if self.data_file.exists():
                with self.data_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                self.timestamps.extend(datetime.fromisoformat(ts) for ts in data['timestamps'])
                self.passive_liquido.extend(data['passive_liquido'])
                self.passive_varejo.extend(data['passive_varejo'])
                self.aggressive_varejo.extend(data['aggressive_varejo'])
                self.net_varejo.extend(data['net_varejo'])
                self.logger.info("Dados históricos carregados com sucesso.")
            else:
                self.logger.info("Nenhum arquivo de dados históricos encontrado. Iniciando vazio.")
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados históricos: {e}", exc_info=True)
