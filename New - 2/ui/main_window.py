import tkinter as tk
from tkinter import ttk
from datetime import datetime
import logging
from network import MarketConnection
from config import AppConfig
from .chart_panel import ChartPanel
from models import HistoricalData
from utils.logger import setup_logger

class MainWindow:
    def __init__(self, root: tk.Tk, market: MarketConnection, config: AppConfig):
        self.logger = setup_logger('ABDM.UI')
        self.root = root
        self.market = market
        self.config = config
        self.root.title("Dados das Corretoras e Resultado")
        self.historical_data = HistoricalData()
        self.charts = {}  # Inicializa o dicionário de gráficos
        self.root.state('zoomed')  # Inicia maximizado
        self.setup_ui()
        self.start_updates()

        # Adiciona funcionalidade de tela cheia
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.fullscreen = False

    def toggle_fullscreen(self, event=None):
        """Ativa/desativa o modo de tela cheia"""
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self, event=None):
        """Sai do modo tela cheia"""
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

    def setup_ui(self):
        """Configura a interface do usuário apenas com os gráficos"""
        # Configura a janela para expandir células igualmente
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame principal usando grid
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Configura o frame principal para distribuir espaço igualmente
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # Configura os gráficos usando grid com novos títulos
        self.charts = {}
        self.charts['market_maker'] = ChartPanel(self.main_frame, "Market Maker")
        self.charts['corporativo'] = ChartPanel(self.main_frame, "Corporativo")
        self.charts['provedor_liquidez_varejo'] = ChartPanel(self.main_frame, "Provedor de Liquidez - Varejo")
        self.charts['exposicao_varejo'] = ChartPanel(self.main_frame, "Exposição Varejo")
        
        # Reorganiza os gráficos em grade 2x2
        self.charts['market_maker'].grid(row=0, column=0, sticky='nsew')
        self.charts['corporativo'].grid(row=1, column=0, sticky='nsew')
        self.charts['provedor_liquidez_varejo'].grid(row=0, column=1, sticky='nsew')
        self.charts['exposicao_varejo'].grid(row=1, column=1, sticky='nsew')

        # Configura tela cheia
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        self.fullscreen = False
        
        # Configura tamanho mínimo
        self.root.minsize(1024, 768)

        # Criar nova janela para as tabelas
        self.table_window = tk.Toplevel(self.root)
        self.table_window.title("Tabelas de Dados")
        self.setup_tables(self.table_window)
        self.table_window.minsize(800, 400)

    def setup_tables(self, tables_frame):
        # Criar painel principal
        self.main_panel = ttk.PanedWindow(tables_frame, orient=tk.VERTICAL)
        self.main_panel.pack(fill=tk.BOTH, expand=True)

        # Frame para a tabela de corretoras
        brokers_frame = ttk.LabelFrame(self.main_panel, text="Dados das Corretoras")
        self.main_panel.add(brokers_frame, weight=3)

        # Frame para a tabela de resultados
        results_frame = ttk.LabelFrame(self.main_panel, text="Resultados")
        self.main_panel.add(results_frame, weight=1)

        # Configurar tabela de corretoras
        columns = (
            "Timestamp", "Corretora", "Vol. Qtd (Saldo)", "Preço Médio", 
            "Agr. Compra", "Agr. Venda", "Agressão Líquida", 
            "Passivo líquido", "L/P Bruto"
        )
        self.treeview = ttk.Treeview(brokers_frame, columns=columns, show='headings')
        for col in columns:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, width=100)  # Largura inicial das colunas
        
        # Adicionar scrollbars para a tabela de corretoras
        brokers_scroll_y = ttk.Scrollbar(brokers_frame, orient=tk.VERTICAL, command=self.treeview.yview)
        brokers_scroll_x = ttk.Scrollbar(brokers_frame, orient=tk.HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(yscrollcommand=brokers_scroll_y.set, xscrollcommand=brokers_scroll_x.set)
        
        # Posicionar elementos da tabela de corretoras
        brokers_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        brokers_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configurar tabela de resultados
        resultado_columns = ("Descrição", "Contratos", "Financeiro")
        self.resultado_treeview = ttk.Treeview(
            results_frame, 
            columns=resultado_columns, 
            show='headings',
            height=5  # Limitar altura inicial
        )
        for col in resultado_columns:
            self.resultado_treeview.heading(col, text=col)
            self.resultado_treeview.column(col, width=150)  # Largura inicial das colunas
        
        # Adicionar scrollbars para a tabela de resultados
        results_scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.resultado_treeview.yview)
        results_scroll_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.resultado_treeview.xview)
        self.resultado_treeview.configure(yscrollcommand=results_scroll_y.set, xscrollcommand=results_scroll_x.set)
        
        # Posicionar elementos da tabela de resultados
        results_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        results_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.resultado_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configurar tamanho mínimo da janela
        self.root.minsize(800, 600)

    def start_updates(self):
        self.market.request_broker_balance(self.config.asset, self.config.period)
        self.market.request_last_price(self.config.asset)
        self.update_data()

    def update_data(self):
        """Atualiza os dados nas tabelas e gráficos"""
        try:
            self.logger.debug("Iniciando atualização de dados")
            self.market.process_data()
            
            if hasattr(self.market, 'new_data') and self.market.new_data:
                self.logger.info("Novos dados recebidos, atualizando interface")
                try:
                    self.update_broker_table()
                    self.update_result_table()
                    self.market.new_data = False
                    
                    # Agenda a próxima atualização usando after
                    self.root.after(0, self.root.update_idletasks)
                except Exception as e:
                    self.logger.error(f"Erro ao atualizar interface: {e}", exc_info=True)
            
        except Exception as e:
            self.logger.error(f"Erro na atualização: {e}", exc_info=True)
        finally:
            # Agenda a próxima atualização
            self.root.after(100, self.update_data)

    def update_broker_table(self):
        """Atualiza a tabela de corretoras"""
        # Limpa a tabela
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        
        # Insere os dados atualizados
        for broker_data in self.market.get_broker_data().values():
            self.treeview.insert('', 'end', values=[
                broker_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                broker_data['name'],
                broker_data['volume'],
                broker_data['avg_price'],
                f"{int(broker_data['aggr_buy'])}",  # Removido .0
                f"{int(broker_data['aggr_sell'])}",  # Removido .0
                f"{int(broker_data['net_aggr'])}",  # Removido .0
                broker_data['passive_net'],
                f"{int(float(broker_data['gross_pl']))}"  # Convertido para inteiro
            ])

    def update_result_table(self):
        """Atualiza a tabela de resultados"""
        # Limpa a tabela
        for item in self.resultado_treeview.get_children():
            self.resultado_treeview.delete(item)
        
        market_data = self.market.get_market_data()
        brokers_data = self.market.get_broker_data()
        
        # Calcula totais
        # Soma do passivo líquido de todas as corretoras
        net_saldo_passivo_liquido = sum(float(data['passive_net']) for data in brokers_data.values())
        
        # Soma do passivo líquido das corretoras específicas
        corretoras_varejo = ['GENIAL', 'CM CAPITAL', 'NOVA FUTURA', 'SAFRA', 
                            'TORO', 'INTER', 'UBS', 'GUIDE', 'CLEAR', 'IDEAL', 
                            'XP', 'BTG', 'AGORA']
        
        net_saldo_passivo_varejo = sum(float(data['passive_net']) 
                                     for data in brokers_data.values() 
                                     if data['name'] in corretoras_varejo)
        
        # Soma da agressão líquida das corretoras específicas para varejo agressivo
        corretoras_agressivo = ['GENIAL', 'CM CAPITAL', 'NOVA FUTURA', 'SAFRA', 
                               'TORO', 'INTER', 'CLEAR', 'XP', 'BTG', 'AGORA']
        
        net_saldo_agressivo_varejo = sum(float(data['net_aggr']) 
                                       for data in brokers_data.values() 
                                       if data['name'] in corretoras_agressivo)
        
        net_saldo_varejo_contratos = net_saldo_passivo_varejo + net_saldo_agressivo_varejo
        
        # Formata o último preço, tratando caso seja None
        ultimo_preco_str = f"{int(market_data.ultimo_preco)}" if market_data.ultimo_preco is not None else "N/A"
        
        # Insere resultados
        self.resultado_treeview.insert('', 'end', values=[
            'Último preço WINJ25',
            ultimo_preco_str,
            ''
        ])
        
        # Insere net/saldo apenas se houver último preço
        if market_data.ultimo_preco is not None:
            self.resultado_treeview.insert('', 'end', values=[
                'Net/Saldo passivo líquido',
                f"{net_saldo_passivo_liquido:,.0f}",
                f"{int(self.calcular_financeiro(net_saldo_passivo_liquido, market_data.ultimo_preco)):,}"
            ])
            self.resultado_treeview.insert('', 'end', values=[
                'Net/Saldo passivo Varejo',
                f"{net_saldo_passivo_varejo:,.0f}",
                f"{int(self.calcular_financeiro(net_saldo_passivo_varejo, market_data.ultimo_preco)):,}"
            ])
            self.resultado_treeview.insert('', 'end', values=[
                'Net/Saldo Agressivo Varejo',
                f"{net_saldo_agressivo_varejo:,.0f}",
                f"{int(self.calcular_financeiro(net_saldo_agressivo_varejo, market_data.ultimo_preco)):,}"
            ])
            self.resultado_treeview.insert('', 'end', values=[
                'Net/Saldo Varejo',
                f"{net_saldo_varejo_contratos:,.0f}",
                f"{int(self.calcular_financeiro(net_saldo_varejo_contratos, market_data.ultimo_preco)):,}"
            ])
        
        # Usa o timestamp do último dado recebido
        latest_timestamp = max(d['timestamp'] for d in brokers_data.values())
        
        # Adicionar dados ao histórico apenas se houver último preço
        if market_data.ultimo_preco is not None:
            latest_timestamp = max(d['timestamp'] for d in brokers_data.values())
            
            self.historical_data.add_point(latest_timestamp, {
                'passive_liquido': self.calcular_financeiro(net_saldo_passivo_liquido, market_data.ultimo_preco),
                'passive_varejo': self.calcular_financeiro(net_saldo_passivo_varejo, market_data.ultimo_preco),
                'aggressive_varejo': self.calcular_financeiro(net_saldo_agressivo_varejo, market_data.ultimo_preco),
                'net_varejo': self.calcular_financeiro(net_saldo_varejo_contratos, market_data.ultimo_preco)
            })
            
            # Atualizar gráficos imediatamente após adicionar dados
            self.update_charts()

    def update_charts(self):
        """Atualiza os gráficos com dados históricos"""
        try:
            # Define os dados financeiros para cada gráfico
            chart_data_mapping = {
                'market_maker': 'passive_liquido',
                'provedor_liquidez_varejo': 'passive_varejo',
                'corporativo': 'aggressive_varejo',
                'exposicao_varejo': 'net_varejo'
            }

            for chart_name, data_key in chart_data_mapping.items():
                chart = self.charts[chart_name]
                data = getattr(self.historical_data, data_key, [])
                if hasattr(self.historical_data, 'timestamps') and len(self.historical_data.timestamps) > 0:
                    self.logger.debug(f"Atualizando gráfico {chart_name} com {len(data)} pontos")
                    # Copia os dados para evitar problemas de concorrência
                    timestamps = list(self.historical_data.timestamps)
                    values = list(data)
                    # Atualiza o gráfico com os dados correspondentes
                    self._update_single_chart(chart, timestamps, values)

        except Exception as e:
            self.logger.error(f"Erro ao atualizar gráficos: {e}", exc_info=True)

    def _update_single_chart(self, chart, timestamps, values):
        """Função auxiliar para atualizar um único gráfico"""
        try:
            chart.update(timestamps, values)
        except Exception as e:
            self.logger.error(f"Erro ao atualizar gráfico individual: {e}", exc_info=True)

    def calcular_financeiro(self, net_saldo, ultimo_preco):
        """Calcula o valor financeiro"""
        if ultimo_preco is not None and net_saldo is not None:
            try:
                # Retorna o valor em termos nominais (não em bilhões)
                return float(ultimo_preco) * 0.20 * float(net_saldo)  # Removido divisão por 1000
            except (ValueError, TypeError):
                logging.warning("Erro ao calcular valor financeiro")
                return 0
        return 0
