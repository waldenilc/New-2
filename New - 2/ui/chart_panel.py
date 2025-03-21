import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from utils.logger import setup_logger
import matplotlib.ticker as ticker

class ChartPanel(tk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title = title
        self.logger = setup_logger(f"Chart_{title}")
        
        # Configura grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.setup_chart()
        self.timestamps = []
        self.values = []
        self.line = None
        self.zero_line = None
        self.value_text = None

    def setup_chart(self):
        """Configura o gráfico inicial"""
        self.figure = Figure(dpi=100)
        # Ajusta margens para maximizar área útil do gráfico
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        self.ax = self.figure.add_subplot(111)
        # Ajusta o título com tamanho de fonte menor
        self.ax.set_title(self.title, pad=10, fontsize=9)
        
        # Adiciona linha do zero destacada
        self.zero_line = self.ax.axhline(y=0, color='red', linestyle='-', linewidth=1.5, zorder=2)
        self.ax.grid(True, axis='y', which='both', zorder=1)
        
        # Configuração dos eixos
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_tick_params(rotation=0)
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x/1e9:.1f}B'))
        self.ax.yaxis.tick_right()
        self.ax.yaxis.set_label_position('right')
        
        # Configura o canvas usando grid
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

    def on_resize(self, event=None):
        """Ajusta o tamanho do gráfico quando a janela é redimensionada"""
        if not event:
            return
        try:
            # Calcula novas dimensões mantendo proporções
            w_inches = event.width / self.figure.dpi
            h_inches = event.height / self.figure.dpi
            
            # Atualiza tamanho da figura
            self.figure.set_size_inches(w_inches, h_inches, forward=True)
            self.canvas.draw()
        except Exception as e:
            self.logger.error(f"Erro ao redimensionar: {e}")

    def toggle_fullscreen(self, event=None):
        """Alterna entre tela cheia e normal"""
        self.fullscreen = not self.fullscreen
        root = self.winfo_toplevel()
        root.attributes('-fullscreen', self.fullscreen)

    def exit_fullscreen(self, event=None):
        """Sai do modo tela cheia"""
        self.fullscreen = False
        root = self.winfo_toplevel()
        root.attributes('-fullscreen', False)

    def update(self, timestamps, values):
        """Atualiza o gráfico com novos dados"""
        try:
            if not timestamps or not values:
                self.logger.warning(f"Dados vazios para gráfico {self.title}")
                return

            # Atualiza os dados
            self.timestamps = timestamps
            self.values = [float(v) for v in values]

            # Remove elementos anteriores
            if self.line:
                self.line.remove()
            if hasattr(self, 'value_text') and self.value_text:
                self.value_text.remove()
            
            # Plota nova linha com limites exatos
            self.line, = self.ax.plot(self.timestamps, self.values, '-', color='blue', zorder=3)
            
            # Garante que a linha do zero permaneça visível
            if self.zero_line not in self.ax.lines:
                self.zero_line = self.ax.axhline(y=0, color='red', linestyle='-', linewidth=1.5, zorder=2)
            
            # Define limites exatos para o eixo X
            if self.timestamps:
                time_delta = (self.timestamps[-1] - self.timestamps[0]) * 0.0001  # Margem mínima
                self.ax.set_xlim(
                    self.timestamps[0] - time_delta,  # Pequeno ajuste para tocar borda esquerda
                    self.timestamps[-1] + time_delta   # Pequeno ajuste para tocar borda direita
                )
            
            # Adiciona texto do valor atual
            if self.values:
                current_value = self.values[-1]
                self.value_text = self.ax.text(
                    1.02, current_value,
                    f'{current_value/1e9:.1f}B',
                    transform=self.ax.get_yaxis_transform(),
                    bbox=dict(
                        boxstyle='round,pad=0.5',
                        fc='white',
                        ec='gray',
                        alpha=1
                    ),
                    verticalalignment='center',
                    horizontalalignment='left',
                    zorder=5
                )
            
            # Ajusta limites Y sem alterar os limites X já definidos
            if self.values:
                ymin, ymax = min(self.values), max(self.values)
                margin = (ymax - ymin) * 0.1 if ymax != ymin else abs(ymax) * 0.1
                self.ax.set_ylim(min(ymin - margin, 0), max(ymax + margin, 0))

            # Atualiza o canvas
            if self.winfo_exists():
                self.canvas.draw()

        except Exception as e:
            self.logger.error(f"Erro ao atualizar gráfico: {e}", exc_info=True)
