import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from time import sleep
import threading
import sqlite3
import json
import os
from datetime import datetime

import pyautogui
import keyboard
import pydirectinput

pyautogui.FAILSAFE = True
pydirectinput.FAILSAFE = True

DB_FILE = "bombeiros_fluxo.db"
CONFIG_FILE = "config_bombeiros.json"

VALOR_REANIMACAO = 12000
COMANDO_COBRAR = "cobrar {id} {valor}"
COMANDO_REANIMAR = "re;{id}"

executando = False

CONFIG_PADRAO = {
    "tecla_pegar_id": "f1",
    "tecla_reanimar": "f2",
    "tecla_prompt": "f8",
    "tecla_executar": "f9",
    "tecla_print": "alt+f1",
    "pasta_prints": "prints"
}


def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        salvar_config(CONFIG_PADRAO)
        return CONFIG_PADRAO.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as arquivo:
            config = json.load(arquivo)

        for chave, valor in CONFIG_PADRAO.items():
            if chave not in config:
                config[chave] = valor

        return config

    except Exception:
        salvar_config(CONFIG_PADRAO)
        return CONFIG_PADRAO.copy()


def salvar_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as arquivo:
        json.dump(config, arquivo, indent=4, ensure_ascii=False)


config_app = carregar_config()


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id TEXT NOT NULL,
            valor INTEGER NOT NULL,
            status_pagamento TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            comando_cobranca TEXT NOT NULL,
            comando_reanimacao TEXT,
            print_realizado INTEGER DEFAULT 0,
            caminho_print TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN caminho_print TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def logar(texto):
    print(texto)


def salvar_atendimento(
    paciente_id,
    valor,
    status,
    comando_cobranca,
    comando_reanimacao="",
    print_realizado=False,
    caminho_print=""
):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO atendimentos (
            paciente_id,
            valor,
            status_pagamento,
            data_hora,
            comando_cobranca,
            comando_reanimacao,
            print_realizado,
            caminho_print
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        paciente_id,
        valor,
        status,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        comando_cobranca,
        comando_reanimacao,
        1 if print_realizado else 0,
        caminho_print
    ))

    conn.commit()
    conn.close()


def carregar_grade():
    for item in tabela.get_children():
        tabela.delete(item)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT paciente_id, valor, status_pagamento, data_hora
        FROM atendimentos
        ORDER BY id DESC
        LIMIT 50
    """)

    registros = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM atendimentos
        WHERE status_pagamento = 'PAGO'
    """)
    total_pago = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM atendimentos
        WHERE status_pagamento = 'PAGO'
    """)
    total_salvamentos = cursor.fetchone()[0]

    conn.close()

    for paciente_id, valor, status, data_hora in registros:
        tabela.insert(
            "",
            tk.END,
            values=(paciente_id, moeda(valor), status, data_hora)
        )

    lbl_total.config(text=f"Total arrecadado: {moeda(total_pago)}")
    lbl_salvamentos.config(text=f"Total de salvamentos: {total_salvamentos}")


def set_status(texto, cor="#2e7d32"):
    lbl_status.config(text=texto, fg=cor)
    janela.update_idletasks()


def perguntar_sim_nao_threadsafe(titulo, mensagem):
    resposta = {"valor": False}
    evento = threading.Event()

    def perguntar():
        resposta["valor"] = messagebox.askyesno(titulo, mensagem)
        evento.set()

    janela.after(0, perguntar)
    evento.wait()

    return resposta["valor"]


def confirmar_pagamento():
    return perguntar_sim_nao_threadsafe(
        "Confirmação de pagamento",
        "O pagamento foi confirmado no FluxoRP?"
    )
    pyautogui.hotkey("alt", "tab")


def limpar_id():
    entrada_id.delete(0, tk.END)
    entrada_id.focus()
    set_status("Aguardando ID do paciente", "#1565c0")


def validar_id(id_paciente):
    if not id_paciente:
        messagebox.showwarning("ID obrigatório", "Digite o ID do paciente.")
        return False

    if not id_paciente.isdigit():
        messagebox.showerror("ID inválido", "O ID precisa conter apenas números.")
        return False

    return True


def pressionar_tecla(tecla):
    tecla = str(tecla).strip().lower()

    if not tecla:
        return

    if "+" in tecla:
        partes = [parte.strip() for parte in tecla.split("+") if parte.strip()]
        pyautogui.hotkey(*partes)
    else:
        pydirectinput.press(tecla)


def realizar_print(id_paciente):
    tecla_print = config_app.get("tecla_print", "alt+f1")
    pasta_prints = config_app.get("pasta_prints", "prints").strip() or "prints"

    os.makedirs(pasta_prints, exist_ok=True)

    pressionar_tecla(tecla_print)
    sleep(0.5)

    data_arquivo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"salvamento_{id_paciente}_{data_arquivo}.png"
    caminho_print = os.path.join(pasta_prints, nome_arquivo)

    imagem = pyautogui.screenshot()
    imagem.save(caminho_print)

    return caminho_print


def cobrar_e_reanimar(id_paciente):
    global executando

    executando = True
    btn_executar.config(state="disabled")

    valor = VALOR_REANIMACAO
    tecla_prompt = config_app.get("tecla_prompt", "f8")
    tecla_reanimar = config_app.get("tecla_reanimar", "f2")

    comando_cobranca = COMANDO_COBRAR.format(id=id_paciente, valor=valor)
    comando_reanimacao = COMANDO_REANIMAR.format(id=id_paciente)

    caminho_print = ""

    try:
        set_status("Executando cobrança...", "#ef6c00")

        sleep(2)

        if keyboard.is_pressed("esc"):
            logar("Operação cancelada pelo ESC.")
            return

        pressionar_tecla(tecla_prompt)
        sleep(0.8)

        pyautogui.write(comando_cobranca, interval=0.02)
        sleep(0.3)

        pyautogui.press("enter")
        sleep(0.8)

        pressionar_tecla(tecla_prompt)
        sleep(0.5)

        #pydirectinput.press("y")
        #sleep(0.4)

        pydirectinput.press("y")
        sleep(0.8)

        set_status("Aguardando confirmação de pagamento...", "#6a1b9a")

        if confirmar_pagamento():
            set_status("Reanimando paciente...", "#c62828")

            sleep(0.5)

            pyautogui.hotkey("alt", "tab")
            sleep(0.8)

            pressionar_tecla(tecla_reanimar)
            sleep(0.8)

            pressionar_tecla(tecla_prompt)
            sleep(0.5)

            pyautogui.write(comando_reanimacao, interval=0.02)
            sleep(0.4)

            pyautogui.press("enter")
            sleep(0.5)

            caminho_print = realizar_print(id_paciente)
            sleep(0.5)

            pressionar_tecla(tecla_prompt)
            sleep(1.5)

            salvar_atendimento(
                paciente_id=id_paciente,
                valor=valor,
                status="PAGO",
                comando_cobranca=comando_cobranca,
                comando_reanimacao=comando_reanimacao,
                print_realizado=True,
                caminho_print=caminho_print
            )

            janela.after(0, carregar_grade)
            set_status("Atendimento concluído", "#2e7d32")

        else:
            set_status("Pagamento não confirmado", "#b71c1c")

    except Exception as erro:
        logar(f"Erro: {erro}")
        set_status("Erro durante execução", "#b71c1c")
        janela.after(0, lambda: messagebox.showerror("Erro", str(erro)))

    finally:
        executando = False
        btn_executar.config(state="normal")
        janela.after(0, limpar_id)


def executar_fluxo():
    global executando

    if executando:
        return

    id_paciente = entrada_id.get().strip()

    if not validar_id(id_paciente):
        return

    thread = threading.Thread(
        target=cobrar_e_reanimar,
        args=(id_paciente,),
        daemon=True
    )
    thread.start()


def executar_hotkey():
    executar_fluxo()


def alterar_valor():
    global VALOR_REANIMACAO

    novo = entrada_valor.get().strip()

    if not novo.isdigit():
        messagebox.showerror("Erro", "Digite um valor válido.")
        return

    VALOR_REANIMACAO = int(novo)


def valor_rapido(valor):
    entrada_valor.delete(0, tk.END)
    entrada_valor.insert(0, str(valor))
    alterar_valor()


def limpar_bd():
    confirmar = messagebox.askyesno(
        "Limpar Banco de Dados",
        "Deseja realmente apagar todos os registros do banco de dados?"
    )

    if not confirmar:
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM atendimentos")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='atendimentos'")

    conn.commit()
    conn.close()

    carregar_grade()
    set_status("Banco de dados limpo", "#b71c1c")


def abrir_config():
    janela_config = tk.Toplevel(janela)
    janela_config.title("Configurações de Teclas")
    janela_config.geometry("520x410")
    janela_config.resizable(False, False)
    janela_config.grab_set()

    tk.Label(
        janela_config,
        text="Configuração de Binds",
        font=("Arial", 15, "bold")
    ).pack(pady=12)

    frame = tk.Frame(janela_config)
    frame.pack(pady=5)

    tk.Label(frame, text="Tecla para pegar ID:", anchor="w", width=24).grid(row=0, column=0, padx=5, pady=6)
    entrada_pegar_id = tk.Entry(frame, width=18, justify="center", font=("Arial", 11))
    entrada_pegar_id.grid(row=0, column=1, padx=5, pady=6)
    entrada_pegar_id.insert(0, config_app.get("tecla_pegar_id", "f1"))

    tk.Label(frame, text="Tecla para reanimar:", anchor="w", width=24).grid(row=1, column=0, padx=5, pady=6)
    entrada_reanimar = tk.Entry(frame, width=18, justify="center", font=("Arial", 11))
    entrada_reanimar.grid(row=1, column=1, padx=5, pady=6)
    entrada_reanimar.insert(0, config_app.get("tecla_reanimar", "f2"))

    tk.Label(frame, text="Tecla para abrir prompt:", anchor="w", width=24).grid(row=2, column=0, padx=5, pady=6)
    entrada_prompt = tk.Entry(frame, width=18, justify="center", font=("Arial", 11))
    entrada_prompt.grid(row=2, column=1, padx=5, pady=6)
    entrada_prompt.insert(0, config_app.get("tecla_prompt", "f8"))

    tk.Label(frame, text="Tecla para executar:", anchor="w", width=24).grid(row=3, column=0, padx=5, pady=6)
    entrada_executar = tk.Entry(frame, width=18, justify="center", font=("Arial", 11))
    entrada_executar.grid(row=3, column=1, padx=5, pady=6)
    entrada_executar.insert(0, config_app.get("tecla_executar", "f9"))

    tk.Label(frame, text="Tecla para print:", anchor="w", width=24).grid(row=4, column=0, padx=5, pady=6)
    entrada_print = tk.Entry(frame, width=18, justify="center", font=("Arial", 11))
    entrada_print.grid(row=4, column=1, padx=5, pady=6)
    entrada_print.insert(0, config_app.get("tecla_print", "alt+f1"))

    tk.Label(frame, text="Pasta dos prints:", anchor="w", width=24).grid(row=5, column=0, padx=5, pady=6)
    entrada_pasta = tk.Entry(frame, width=32, font=("Arial", 10))
    entrada_pasta.grid(row=5, column=1, padx=5, pady=6)
    entrada_pasta.insert(0, config_app.get("pasta_prints", "prints"))

    def escolher_pasta():
        pasta = filedialog.askdirectory(title="Escolher pasta para salvar prints")

        if pasta:
            entrada_pasta.delete(0, tk.END)
            entrada_pasta.insert(0, pasta)

    tk.Button(
        frame,
        text="Escolher",
        command=escolher_pasta,
        width=10
    ).grid(row=5, column=2, padx=5, pady=6)

    def salvar_novas_configuracoes():
        global config_app

        nova_config = {
            "tecla_pegar_id": entrada_pegar_id.get().strip().lower() or "f1",
            "tecla_reanimar": entrada_reanimar.get().strip().lower() or "f2",
            "tecla_prompt": entrada_prompt.get().strip().lower() or "f8",
            "tecla_executar": entrada_executar.get().strip().lower() or "f9",
            "tecla_print": entrada_print.get().strip().lower() or "alt+f1",
            "pasta_prints": entrada_pasta.get().strip() or "prints"
        }

        salvar_config(nova_config)
        config_app = nova_config

        iniciar_atalhos(recarregar=True)

        set_status("Configurações salvas", "#1565c0")
        janela_config.destroy()

    frame_botoes_config = tk.Frame(janela_config)
    frame_botoes_config.pack(pady=15)

    tk.Button(
        frame_botoes_config,
        text="Salvar",
        font=("Arial", 11, "bold"),
        bg="#2e7d32",
        fg="white",
        command=salvar_novas_configuracoes,
        width=12
    ).grid(row=0, column=0, padx=5)

    tk.Button(
        frame_botoes_config,
        text="Cancelar",
        font=("Arial", 11),
        command=janela_config.destroy,
        width=12
    ).grid(row=0, column=1, padx=5)


def iniciar_atalhos(recarregar=False):
    try:
        keyboard.unhook_all_hotkeys()
    except Exception:
        pass

    tecla_executar = config_app.get("tecla_executar", "f9")

    try:
        keyboard.add_hotkey(tecla_executar, executar_hotkey)
    except Exception as erro:
        logar(f"Erro ao configurar atalho: {erro}")


init_db()

janela = tk.Tk()
janela.title("Bombeiros - FluxoRP")
janela.geometry("500x700")
janela.resizable(False, False)

titulo = tk.Label(
    janela,
    text="🚒 Bombeiros - FluxoRP",
    font=("Arial", 20, "bold")
)
titulo.pack(pady=10)

lbl_status = tk.Label(
    janela,
    text="Aguardando ID do paciente",
    font=("Arial", 12, "bold"),
    fg="#1565c0"
)
lbl_status.pack(pady=3)

frame_id = tk.Frame(janela)
frame_id.pack(pady=8)

tk.Label(frame_id, text="ID do paciente:", font=("Arial", 11)).grid(row=0, column=0, padx=5)

entrada_id = tk.Entry(frame_id, font=("Arial", 16), width=15, justify="center")
entrada_id.grid(row=0, column=1, padx=5)
entrada_id.focus()
entrada_id.bind("<Return>", lambda event: executar_fluxo())

btn_executar = tk.Button(
    janela,
    text="Cobrar + Reanimar",
    font=("Arial", 14, "bold"),
    bg="#c62828",
    fg="white",
    command=executar_fluxo,
    width=28,
    height=2
)
btn_executar.pack(pady=10)

frame_config = tk.Frame(janela)
frame_config.pack(pady=2)

btn_config = tk.Button(
    frame_config,
    text="Config",
    font=("Arial", 11, "bold"),
    bg="#1565c0",
    fg="white",
    command=abrir_config,
    width=16
)
btn_config.grid(row=0, column=0, padx=5)

btn_limpar_bd = tk.Button(
    frame_config,
    text="Limpar BD",
    font=("Arial", 11, "bold"),
    bg="#424242",
    fg="white",
    command=limpar_bd,
    width=16
)
btn_limpar_bd.grid(row=0, column=1, padx=5)

frame_valor = tk.LabelFrame(janela, text="Valor do atendimento", padx=8, pady=8)
frame_valor.pack(pady=8)

tk.Label(frame_valor, text="Valor:").grid(row=0, column=0, padx=5)

entrada_valor = tk.Entry(frame_valor, font=("Arial", 12), width=10, justify="center")
entrada_valor.insert(0, str(VALOR_REANIMACAO))
entrada_valor.grid(row=0, column=1, padx=5)

btn_valor = tk.Button(
    frame_valor,
    text="Alterar",
    command=alterar_valor,
    width=10
)
btn_valor.grid(row=0, column=2, padx=5)

frame_valores_rapidos = tk.Frame(frame_valor)
frame_valores_rapidos.grid(row=1, column=0, columnspan=3, pady=8)

tk.Button(frame_valores_rapidos, text="8.000", width=8, command=lambda: valor_rapido(8000)).grid(row=0, column=0, padx=3)
tk.Button(frame_valores_rapidos, text="10.000", width=8, command=lambda: valor_rapido(10000)).grid(row=0, column=1, padx=3)
tk.Button(frame_valores_rapidos, text="12.000", width=8, command=lambda: valor_rapido(12000)).grid(row=0, column=2, padx=3)
tk.Button(frame_valores_rapidos, text="25.000", width=8, command=lambda: valor_rapido(25000)).grid(row=0, column=3, padx=3)

tk.Label(
    janela,
    text="Registros de Atendimento:",
    font=("Arial", 12, "bold")
).pack(pady=5)

colunas = ("paciente_id", "valor", "status", "data")

tabela = ttk.Treeview(
    janela,
    columns=colunas,
    show="headings",
    height=9
)

tabela.heading("paciente_id", text="Paciente ID")
tabela.heading("valor", text="Valor")
tabela.heading("status", text="Status")
tabela.heading("data", text="Data/Hora")

tabela.column("paciente_id", width=100, anchor="center")
tabela.column("valor", width=120, anchor="center")
tabela.column("status", width=90, anchor="center")
tabela.column("data", width=210, anchor="center")

tabela.pack(pady=5)

lbl_total = tk.Label(
    janela,
    text="Total arrecadado: R$ 0,00",
    font=("Arial", 12, "bold")
)
lbl_total.pack(pady=3)

lbl_salvamentos = tk.Label(
    janela,
    text="Total de salvamentos: 0",
    font=("Arial", 12, "bold"),
    fg="#2e7d32"
)
lbl_salvamentos.pack(pady=3)

carregar_grade()
iniciar_atalhos()

janela.mainloop()