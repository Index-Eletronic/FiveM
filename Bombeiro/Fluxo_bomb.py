import tkinter as tk
from tkinter import messagebox, ttk
from time import sleep
import threading
import sqlite3
from datetime import datetime

import pyautogui
import keyboard
import pydirectinput

pyautogui.FAILSAFE = True
pydirectinput.FAILSAFE = True

VALOR_REANIMACAO = 12000
DB_FILE = "bombeiros_fluxo.db"


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
            print_realizado INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def salvar_atendimento(
    paciente_id,
    valor,
    status,
    comando_cobranca,
    comando_reanimacao="",
    print_realizado=False
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
            print_realizado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        paciente_id,
        valor,
        status,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        comando_cobranca,
        comando_reanimacao,
        1 if print_realizado else 0
    ))

    conn.commit()
    conn.close()


def carregar_grade():
    for item in tabela.get_children():
        tabela.delete(item)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT paciente_id, valor, data_hora
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

    conn.close()

    for registro in registros:
        paciente_id, valor, data_hora = registro

        tabela.insert(
            "",
            tk.END,
            values=(
                paciente_id,
                f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                data_hora
            )
        )

    lbl_total.config(
        text=f"Total arrecadado: R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


def logar(texto):
    txt_log.insert(tk.END, texto + "\n")
    txt_log.see(tk.END)
    janela.update_idletasks()


def confirmar_pagamento():
    return messagebox.askyesno(
        "Confirmação",
        "Pagamento confirmado?"
    )


def limpar_id():
    entrada_id.delete(0, tk.END)
    entrada_id.focus()
    logar("Pronto para próximo atendimento.")


def cobrar_e_reanimar(id_paciente):
    comando_cobranca = f"cobrar {id_paciente} {VALOR_REANIMACAO}"
    comando_reanimacao = f"re;{id_paciente}"

    logar("")
    logar(f"Paciente ID: {id_paciente}")
    logar(f"Comando: {comando_cobranca}")
    logar("Iniciando em 2 segundos...")

    sleep(2)

    pyautogui.press("f8")
    sleep(1)

    pyautogui.write(comando_cobranca, interval=0.02)
    sleep(0.5)

    pyautogui.press("enter")
    sleep(1)

    pyautogui.press("f8")
    sleep(0.7)

    pydirectinput.press("y")
    sleep(0.5)

    pydirectinput.press("y")
    sleep(1)

    if confirmar_pagamento():
        logar("Pagamento confirmado.")
        logar("Executando reanimação...")
        sleep(0.5)

        pyautogui.hotkey("alt", "tab")
        sleep(0.8)

        pydirectinput.press("f8")
        sleep(0.5)

        pyautogui.write(comando_reanimacao, interval=0.02)
        sleep(0.5)

        pyautogui.press("enter")
        sleep(0.5)

        pyautogui.hotkey("alt", "f1")
        sleep(0.5)

        pydirectinput.press("f8")
        sleep(3)

        salvar_atendimento(
            paciente_id=id_paciente,
            valor=VALOR_REANIMACAO,
            status="PAGO",
            comando_cobranca=comando_cobranca,
            comando_reanimacao=comando_reanimacao,
            print_realizado=True
        )

        janela.after(0, carregar_grade)

        logar("Paciente reanimado com sucesso.")

    else:
        logar("Pagamento não confirmado.")
        logar("Atendimento não registrado.")
        logar("Pulando para próximo atendimento.")

    janela.after(0, limpar_id)


def executar_fluxo():
    id_paciente = entrada_id.get().strip()

    if not id_paciente:
        messagebox.showwarning(
            "ID obrigatório",
            "Digite o ID do paciente."
        )
        return

    if not id_paciente.isdigit():
        messagebox.showerror(
            "ID inválido",
            "O ID precisa conter apenas números."
        )
        return

    thread = threading.Thread(
        target=cobrar_e_reanimar,
        args=(id_paciente,),
        daemon=True
    )
    thread.start()


def executar_f9():
    logar("F9 pressionado.")
    executar_fluxo()


def alterar_valor():
    global VALOR_REANIMACAO

    novo = entrada_valor.get().strip()

    if not novo.isdigit():
        messagebox.showerror("Erro", "Digite um valor válido.")
        return

    VALOR_REANIMACAO = int(novo)
    logar(f"Novo valor: {VALOR_REANIMACAO}")


def iniciar_atalho():
    keyboard.add_hotkey("f9", executar_f9)
    sleep(0.8)
    pyautogui.hotkey("alt", "tab")


init_db()

janela = tk.Tk()
janela.title("Bombeiros - Fluxo RP")
janela.geometry("500x700")
janela.resizable(False, False)

titulo = tk.Label(
    janela,
    text="🚒 Bombeiros - Fluxo RP",
    font=("Arial", 18, "bold")
)
titulo.pack(pady=10)

frame_id = tk.Frame(janela)
frame_id.pack(pady=5)

tk.Label(frame_id, text="ID do paciente:").grid(row=0, column=0, padx=5)

entrada_id = tk.Entry(frame_id, font=("Arial", 14), width=15)
entrada_id.grid(row=0, column=1, padx=5)
entrada_id.focus()

entrada_id.bind("<Return>", lambda event: executar_fluxo())

btn_executar = tk.Button(
    janela,
    text="F9 / Cobrar + Reanimar",
    font=("Arial", 13, "bold"),
    bg="#c62828",
    fg="white",
    command=executar_fluxo,
    width=25,
    height=2
)
btn_executar.pack(pady=10)

btn_limpar = tk.Button(
    janela,
    text="Limpar ID",
    font=("Arial", 11),
    command=limpar_id,
    width=25
)
btn_limpar.pack(pady=3)

frame_valor = tk.Frame(janela)
frame_valor.pack(pady=8)

tk.Label(frame_valor, text="Valor:").grid(row=0, column=0, padx=5)

entrada_valor = tk.Entry(frame_valor, font=("Arial", 12), width=10)
entrada_valor.insert(0, str(VALOR_REANIMACAO))
entrada_valor.grid(row=0, column=1, padx=5)

btn_valor = tk.Button(
    frame_valor,
    text="Alterar",
    command=alterar_valor
)
btn_valor.grid(row=0, column=2, padx=5)

tk.Label(
    janela,
    text="Registros de Atendimento:",
    font=("Arial", 11, "bold")
).pack(pady=5)

colunas = ("paciente_id", "valor", "data")

tabela = ttk.Treeview(
    janela,
    columns=colunas,
    show="headings",
    height=10
)

tabela.heading("paciente_id", text="Paciente ID")
tabela.heading("valor", text="Valor")
tabela.heading("data", text="Data/Hora")

tabela.column("paciente_id", width=100, anchor="center")
tabela.column("valor", width=170, anchor="center")
tabela.column("data", width=220, anchor="center")

tabela.pack(pady=5)

lbl_total = tk.Label(
    janela,
    text="Total arrecadado: R$ 0,00",
    font=("Arial", 11, "bold")
)
lbl_total.pack(pady=5)

tk.Label(
    janela,
    text="Log do sistema:",
    font=("Arial", 11, "bold")
).pack(pady=5)

txt_log = tk.Text(
    janela,
    height=8,
    width=68
)
txt_log.pack(pady=5)

carregar_grade()

logar("Sistema iniciado.")
logar("Modo FiveM ativado.")
logar("Banco de dados conectado.")
logar("Digite o ID.")
logar("ENTER ou F9 executam.")

iniciar_atalho()

janela.mainloop()