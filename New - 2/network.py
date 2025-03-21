import asyncio
import logging
from typing import Optional
from config import ServerConfig
from models import MarketData
import socket
from datetime import datetime
from utils.logger import setup_logger

class MarketConnection:
    def __init__(self, config: ServerConfig):
        self.logger = setup_logger('ABDM.Network')
        self.config = config
        self.socket = None
        self.buffer = ""
        self.market_data = MarketData()
        self.brokers_data = {}
        self.buffer = ""
        self._connect()

    def _connect(self):
        """Estabelece conexão com o servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.config.host, self.config.port))
            self._send_command(self.config.init_command)
            self.logger.info(f"Conectado ao servidor {self.config.host}:{self.config.port}")
        except Exception as e:
            self.logger.error(f"Erro ao conectar: {e}", exc_info=True)
            raise

    def _send_command(self, command: str) -> str:
        """Envia comando para o servidor e retorna a resposta"""
        command += '\r\n'
        self.socket.sendall(command.encode(self.config.encoding))
        return self.socket.recv(self.config.buffer_size).decode(self.config.encoding)

    def request_broker_balance(self, asset: str, period: int) -> str:
        """Solicita saldo das corretoras"""
        command = f'on{self.config.field_separator}BRKSLD{self.config.field_separator}{asset}{self.config.field_separator}{period}'
        return self._send_command(command)

    def request_last_price(self, asset: str) -> str:
        """Solicita último preço do ativo"""
        command = f'on{self.config.field_separator}SQT{self.config.field_separator}{asset}{self.config.field_separator}LAST'
        return self._send_command(command)

    def process_data(self) -> None:
        """Processa os dados recebidos do servidor"""
        try:
            data = self.socket.recv(self.config.buffer_size).decode(self.config.encoding)
            if data:
                self.logger.debug(f"Dados recebidos: {data[:100]}...")  # Log primeiros 100 caracteres
                self.buffer += data
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    self._process_line(line)
        except Exception as e:
            self.logger.error(f"Erro ao processar dados: {e}", exc_info=True)
            raise

    def _process_line(self, line: str) -> None:
        """Processa uma linha de dados"""
        try:
            if line.startswith('BRKSLD'):
                self.logger.debug(f"Processando dados de corretora: {line[:100]}...")
                fields = line.split(self.config.field_separator)
                if len(fields) >= 25:
                    broker_code = fields[3]
                    # Usar timestamp atual já que o dado não vem com timestamp
                    data_timestamp = datetime.now()
                    
                    # Log dos campos para debug
                    self.logger.debug(f"Campos processados: {', '.join(fields[:16])}")
                    
                    try:
                        self.brokers_data[broker_code] = {
                            'timestamp': data_timestamp,
                            'name': fields[4],
                            'volume': fields[5],
                            'avg_price': fields[7],
                            'aggr_buy': float(fields[8]) if fields[8] else 0,
                            'aggr_sell': float(fields[9]) if fields[9] else 0,
                            'net_aggr': float(fields[8] if fields[8] else 0) - float(fields[9] if fields[9] else 0),
                            'passive_net': fields[15],
                            'gross_pl': fields[16] if len(fields) > 16 else '0',
                            'last_update': datetime.now()
                        }
                        self.new_data = True
                        self.logger.debug(f"Dados processados com sucesso para corretora: {fields[4]}")
                    except (ValueError, IndexError) as e:
                        self.logger.error(f"Erro ao processar campos numéricos: {e}")
                else:
                    self.logger.warning(f"Linha BRKSLD com campos insuficientes: {len(fields)} campos")
            
            elif line.startswith('SQT'):
                self.logger.debug(f"Processando último preço: {line}")
                fields = line.split(self.config.field_separator)
                if len(fields) >= 4 and fields[2] == 'LAST':
                    try:
                        self.market_data.ultimo_preco = float(fields[3])
                        self.logger.info(f"Último preço atualizado: {self.market_data.ultimo_preco}")
                    except ValueError as e:
                        self.logger.error(f"Erro ao converter último preço: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao processar linha: {line[:100]}... Erro: {e}", exc_info=True)

    def get_broker_data(self):
        """Retorna os dados das corretoras"""
        return self.brokers_data

    def get_market_data(self):
        """Retorna os dados de mercado"""
        return self.market_data

    def close(self):
        """Fecha a conexão com o servidor"""
        if self.socket:
            self.socket.close()

    def __del__(self):
        self.close()
