import logging
import tkinter as tk
from config import ServerConfig, AppConfig
from network import MarketConnection
from ui.main_window import MainWindow

def main():
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='app.log'
    )

    try:
        # Inicializar configurações e conexão
        server_config = ServerConfig()
        app_config = AppConfig()
        market = MarketConnection(server_config)
        
        # Iniciar interface gráfica
        root = tk.Tk()
        app = MainWindow(root, market, app_config)
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Erro na aplicação: {e}")
        raise

if __name__ == "__main__":
    main()
