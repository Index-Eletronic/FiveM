from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import keyboard
import pydirectinput


# ============================================================
# CONFIGURAÇÕES
# ============================================================

TECLA_COMIDA = "4"
TECLA_AGUA = "5"

# Tempo entre os ciclos.
# 50 minutos é um intervalo conservador para não deixar
# fome e sede chegarem muito perto de níveis baixos.
INTERVALO_ENTRE_CICLOS_MINUTOS = 1

# Pequeno intervalo entre comer e beber.
INTERVALO_ENTRE_ACOES_SEGUNDOS = 5

# Tempo segurando cada tecla.
TEMPO_PRESSIONAMENTO_SEGUNDOS = 0.15

# Controles do programa.
TECLA_PAUSAR_CONTINUAR = "f6"
TECLA_ENCERRAR = "f7"


@dataclass
class EstadoAutomacao:
    comidas_restantes: int
    aguas_restantes: int
    ciclos_executados: int = 0
    comidas_usadas: int = 0
    aguas_usadas: int = 0
    pausado: bool = False
    encerrado: bool = False


def ler_quantidade(nome: str) -> int:
    """
    Solicita uma quantidade inteira maior ou igual a zero.
    """
    while True:
        valor = input(f"Quantidade de {nome} na mochila: ").strip()

        try:
            quantidade = int(valor)

            if quantidade < 0:
                print("Digite uma quantidade igual ou maior que zero.")
                continue

            return quantidade

        except ValueError:
            print("Digite apenas números inteiros.")


def formatar_tempo(segundos: int) -> str:
    """
    Converte segundos para o formato HH:MM:SS.
    """
    segundos = max(0, segundos)

    horas, resto = divmod(segundos, 3600)
    minutos, segundos_restantes = divmod(resto, 60)

    return f"{horas:02d}:{minutos:02d}:{segundos_restantes:02d}"


def pressionar_tecla(tecla: str) -> None:
    """
    Pressiona uma tecla utilizando pydirectinput.
    """
    pydirectinput.keyDown(tecla)
    time.sleep(TEMPO_PRESSIONAMENTO_SEGUNDOS)
    pydirectinput.keyUp(tecla)


def alternar_pausa(estado: EstadoAutomacao) -> None:
    """
    Alterna a automação entre pausada e ativa.
    """
    if estado.encerrado:
        return

    estado.pausado = not estado.pausado

    if estado.pausado:
        print("\n[PAUSADO] Automação pausada. Pressione F6 para continuar.")
    else:
        print("\n[CONTINUANDO] Automação retomada.")


def encerrar_automacao(estado: EstadoAutomacao) -> None:
    """
    Solicita o encerramento seguro da automação.
    """
    estado.encerrado = True
    print("\n[ENCERRANDO] Finalizando a automação...")


def aguardar_com_controle(
    estado: EstadoAutomacao,
    segundos: int,
) -> bool:
    """
    Aguarda o tempo solicitado, respeitando pausa e encerramento.

    Retorna False caso o programa seja encerrado.
    """
    tempo_restante = segundos

    while tempo_restante > 0:
        if estado.encerrado:
            return False

        if estado.pausado:
            time.sleep(0.25)
            continue

        time.sleep(1)
        tempo_restante -= 1

    return True


def executar_ciclo(estado: EstadoAutomacao) -> None:
    """
    Executa um ciclo de alimentação e hidratação.
    """
    usou_algum_item = False

    if estado.comidas_restantes > 0:
        pressionar_tecla(TECLA_COMIDA)

        estado.comidas_restantes -= 1
        estado.comidas_usadas += 1
        usou_algum_item = True

        if estado.aguas_restantes > 0:
            aguardar_com_controle(
                estado,
                INTERVALO_ENTRE_ACOES_SEGUNDOS,
            )

    if estado.encerrado:
        return

    if estado.aguas_restantes > 0:
        pressionar_tecla(TECLA_AGUA)

        estado.aguas_restantes -= 1
        estado.aguas_usadas += 1
        usou_algum_item = True

    if usou_algum_item:
        estado.ciclos_executados += 1

    ciclos_completos_restantes = min(
        estado.comidas_restantes,
        estado.aguas_restantes,
    )

    print("\n" + "=" * 60)
    print(f"CICLO {estado.ciclos_executados} FINALIZADO")
    print("=" * 60)
    print(f"Comidas usadas........: {estado.comidas_usadas}")
    print(f"Águas usadas..........: {estado.aguas_usadas}")
    print(f"Comidas restantes.....: {estado.comidas_restantes}")
    print(f"Águas restantes.......: {estado.aguas_restantes}")
    print(f"Ciclos completos......: {ciclos_completos_restantes}")

    if estado.comidas_restantes == 0:
        print("AVISO..................: A comida acabou.")

    if estado.aguas_restantes == 0:
        print("AVISO..................: A água acabou.")

    print("=" * 60)


def iniciar_atalhos(estado: EstadoAutomacao) -> None:
    """
    Registra os atalhos globais.
    """
    keyboard.add_hotkey(
        TECLA_PAUSAR_CONTINUAR,
        lambda: alternar_pausa(estado),
    )

    keyboard.add_hotkey(
        TECLA_ENCERRAR,
        lambda: encerrar_automacao(estado),
    )


def executar_automacao(estado: EstadoAutomacao) -> None:
    """
    Executa o loop principal da automação.
    """
    intervalo_segundos = INTERVALO_ENTRE_CICLOS_MINUTOS * 60

    print("\n" + "=" * 60)
    print("AUTO COMER / BEBER - CAPITAL RP")
    print("=" * 60)
    print("Deixe a janela do FiveM em foco.")
    print(f"Comida................: tecla {TECLA_COMIDA}")
    print(f"Água..................: tecla {TECLA_AGUA}")
    print(f"Intervalo.............: {INTERVALO_ENTRE_CICLOS_MINUTOS} minutos")
    print("F6....................: pausar ou continuar")
    print("F7....................: encerrar")
    print("=" * 60)
    print("\nO primeiro ciclo será executado após o intervalo configurado.")

    while not estado.encerrado:
        possui_comida = estado.comidas_restantes > 0
        possui_agua = estado.aguas_restantes > 0

        if not possui_comida and not possui_agua:
            print("\nTodos os itens acabaram. Automação finalizada.")
            estado.encerrado = True
            break

        conseguiu_aguardar = aguardar_com_controle(
            estado,
            intervalo_segundos,
        )

        if not conseguiu_aguardar:
            break

        if estado.encerrado:
            break

        executar_ciclo(estado)

    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    print(f"Ciclos executados.....: {estado.ciclos_executados}")
    print(f"Comidas usadas........: {estado.comidas_usadas}")
    print(f"Águas usadas..........: {estado.aguas_usadas}")
    print(f"Comidas restantes.....: {estado.comidas_restantes}")
    print(f"Águas restantes.......: {estado.aguas_restantes}")
    print("=" * 60)


def main() -> None:
    """
    Inicializa o programa.
    """
    print("=" * 60)
    print("CONFIGURAÇÃO DA MOCHILA")
    print("=" * 60)

    comidas = ler_quantidade("comidas")
    aguas = ler_quantidade("águas")

    if comidas == 0 and aguas == 0:
        print("\nNenhum item disponível. Programa encerrado.")
        return

    estado = EstadoAutomacao(
        comidas_restantes=comidas,
        aguas_restantes=aguas,
    )

    iniciar_atalhos(estado)

    thread_automacao = threading.Thread(
        target=executar_automacao,
        args=(estado,),
        daemon=False,
    )

    thread_automacao.start()
    thread_automacao.join()

    keyboard.unhook_all_hotkeys()


if __name__ == "__main__":
    main()