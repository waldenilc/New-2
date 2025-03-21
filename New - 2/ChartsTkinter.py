import tkinter as tk
from tkinter import ttk
import socket
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configurações do servidor
HOST = '127.0.0.1'
PORT = 557
BUFFER_SIZE = 65536
ENCODING = 'utf-8'

# Comando para iniciar a comunicação
INIT_COMMAND = 'OPENFAST'
# Separador de campos
FIELD_SEPARATOR = '\001'

# Dicionário para armazenar as corretoras e seus dados
brokers_data = {}

# Lista para armazenar o histórico do Financeiro
financeiro_history = []

# Variável para armazenar o último preço do ativo WINJ25
ultimo_preco_winj25 = None

# Função para criar uma conexão socket
def create_socket_connection(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

# Função para enviar comandos ao servidor
def send_command(sock, command):
    command += '\r\n'
    sock.sendall(command.encode(ENCODING))
    data = sock.recv(BUFFER_SIZE).decode(ENCODING)
    return data

# Função para solicitar o saldo das corretoras
def request_broker_balance(sock, asset, period):
    command = f'on{FIELD_SEPARATOR}BRKSLD{FIELD_SEPARATOR}{asset}{FIELD_SEPARATOR}{period}'
    return send_command(sock, command)

# Função para solicitar o último preço do ativo WINJ25
def request_last_price(sock, asset):
    command = f'on{FIELD_SEPARATOR}SQT{FIELD_SEPARATOR}{asset}{FIELD_SEPARATOR}LAST'
    return send_command(sock, command)

# Função para formatar valores com "." como separador de milhares
def format_value(value):
    try:
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except (ValueError, TypeError):
        return str(value)

# Função para calcular o valor financeiro do Net/Saldo
def calcular_valor_financeiro(net_saldo, ultimo_preco):
    if ultimo_preco is not None and net_saldo is not None:
        return float(ultimo_preco) * 0.20 * float(net_saldo) / 1000
    return 0

# Função para atualizar a interface gráfica
def update_gui():
    global sock, buffer, net_saldo_passivo_liquido, financeiro_history, ultimo_preco_winj25, net_saldo_passivo_varejo, net_saldo_agressivo_varejo
    try:
        data = sock.recv(BUFFER_SIZE).decode(ENCODING)
        if data:
            buffer += data

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)  
                print(f'Dados recebidos: {line}')

                if line.startswith('BRKSLD'):
                    fields = line.split(FIELD_SEPARATOR)
                    if len(fields) >= 25:
                        broker_code = fields[3]
                        broker_name = fields[4]
                        row = [
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            broker_name,
                            fields[5],
                            fields[7],
                            fields[8],
                            fields[9],
                            float(fields[8]) - float(fields[9]),
                            fields[15],
                            fields[16],
                        ]
                        brokers_data[broker_code] = row

                elif line.startswith('SQT'):
                    fields = line.split(FIELD_SEPARATOR)
                    if len(fields) >= 4 and fields[2] == 'LAST':
                        ultimo_preco_winj25 = fields[3]

            net_saldo_passivo_liquido = sum(float(row[7]) for row in brokers_data.values())
            net_saldo_passivo_varejo = sum(float(row[7]) for row in brokers_data.values() if row[1] in ['XP', 'BTG', 'CLEAR', 'CM CAPITAL', 'TORO', 'GENIAL'])
            net_saldo_agressivo_varejo = sum(float(row[6]) for row in brokers_data.values() if row[1] in ['XP', 'BTG', 'CLEAR', 'CM CAPITAL', 'TORO', 'GENIAL'])
            valor_financeiro = calcular_valor_financeiro(net_saldo_passivo_liquido, ultimo_preco_winj25)

            financeiro_history.append((datetime.now(), valor_financeiro))
            update_tables()
        else:
            print("Nenhum dado recebido do servidor.")
    except Exception as e:
        print(f'Erro ao atualizar a interface: {e}')
        sock.close()
        time.sleep(5)
        sock = create_socket_connection(HOST, PORT)
    finally:
        root.after(500, update_gui)

# Função para atualizar as tabelas
def update_tables():
    global net_saldo_passivo_liquido, ultimo_preco_winj25, net_saldo_passivo_varejo, net_saldo_agressivo_varejo

    for item in treeview.get_children():
        treeview.delete(item)

    for broker_code, row in brokers_data.items():
        treeview.insert('', 'end', values=row)

    for item in resultado_treeview.get_children():
        resultado_treeview.delete(item)

    # Adiciona os dados na tabela de resultados
    resultado_treeview.insert('', 'end', values=[
        'Último preço WINJ25',
        format_value(ultimo_preco_winj25),
        ''  # Coluna Financeiro vazia para esta linha
    ])
    resultado_treeview.insert('', 'end', values=[
        'Net/Saldo passivo líquido',
        format_value(net_saldo_passivo_liquido),
        format_value(calcular_valor_financeiro(net_saldo_passivo_liquido, ultimo_preco_winj25))
    ])
    resultado_treeview.insert('', 'end', values=[
        'Net/Saldo passivo Varejo',
        format_value(net_saldo_passivo_varejo),
        format_value(calcular_valor_financeiro(net_saldo_passivo_varejo, ultimo_preco_winj25))
    ])
    resultado_treeview.insert('', 'end', values=[
        'Net/Saldo Agressivo Varejo',
        format_value(net_saldo_agressivo_varejo),
        format_value(calcular_valor_financeiro(net_saldo_agressivo_varejo, ultimo_preco_winj25))
    ])

    # Nova linha: Net/Saldo Varejo
    net_saldo_varejo_contratos = net_saldo_passivo_varejo + net_saldo_agressivo_varejo
    resultado_treeview.insert('', 'end', values=[
        'Net/Saldo Varejo',
        format_value(net_saldo_varejo_contratos),
        format_value(calcular_valor_financeiro(net_saldo_varejo_contratos, ultimo_preco_winj25))
    ])
# Configuração da interface gráfica principal
root = tk.Tk()
root.title("Dados das Corretoras e Resultado")

# Criação da Treeview para exibir os dados das corretoras
columns = (
    "Timestamp", "Corretora", "Vol. Qtd (Saldo)", "Preço Médio", "Agr. Compra", "Agr. Venda",
    "Agressão Líquida", "Passivo líquido", "L/P Bruto"
)
treeview = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    treeview.heading(col, text=col)
treeview.pack(fill='both', expand=True)

# Criação da Treeview para exibir o Resultado
resultado_columns = ("Descrição", "Contratos", "Financeiro")
resultado_treeview = ttk.Treeview(root, columns=resultado_columns, show='headings')
for col in resultado_columns:
    resultado_treeview.heading(col, text=col)
resultado_treeview.pack(fill='both', expand=True)

# Conectar ao servidor
sock = create_socket_connection(HOST, PORT)

# Enviar comando inicial para iniciar a comunicação
print('Enviando comando inicial "OPENFAST"...')
api_version = send_command(sock, INIT_COMMAND)
print(f'Conectado ao Open Fast API Versão: {api_version}')

# Solicitar saldo das corretoras para o ativo WINJ25
asset = 'WINJ25'
period = 0        
print(f'Solicitando saldo das corretoras para o ativo {asset}...')
balance_response = request_broker_balance(sock, asset, period)
print(f'Resposta do saldo das corretoras: {balance_response}')

# Solicitar o último preço do ativo WINJ25
print(f'Solicitando último preço do ativo {asset}...')
last_price_response = request_last_price(sock, asset)
print(f'Resposta do último preço: {last_price_response}')

# Inicializa o buffer de dados
buffer = ""

# Iniciar a atualização da interface
update_gui()

# Executar a interface gráfica
root.mainloop()