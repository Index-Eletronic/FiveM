from __future__ import annotations

from datetime import datetime
from pathlib import Path
from random import shuffle, uniform
from time import monotonic, sleep

import keyboard
import pydirectinput


class AwayBot:
    """Automação de alimentação, hidratação e movimentação no FiveM."""

    # ================= CONTROLES =================

    TECLA_PAUSAR = "f6"
    TECLA_ENCERRAR = "f7"

    TECLA_COMER = "4"
    TECLA_BEBER = "5"

    TECLA_CORRER = ""

    # W = frente, S = trás, A = esquerda, D = direita
    TECLAS_MOVIMENTO = ["w", "a"]

    # ================= TEMPOS =================

    TEMPO_INICIALIZACAO = 5

    TEMPO_CICLO = 6 * 60
    INTERVALO_MOVIMENTO = 60

    TEMPO_USAR_ITEM = 5
    INTERVALO_ENTRE_ITENS = 1

    TEMPO_MINIMO_MOVIMENTO = 0.30
    TEMPO_MAXIMO_MOVIMENTO = 0.55
    INTERVALO_ENTRE_MOVIMENTOS = 0.20

    # ================= SALÁRIO =================

    TEMPO_SALARIO = 30 * 60
    VALOR_SALARIO = 2350.00

    # ================= ESTOQUE =================

    COMIDA_INICIAL = 30
    AGUA_INICIAL = 16

    # Para cada comida serão usadas duas águas.
    AGUAS_POR_COMIDA = 1

    # ================= ARQUIVOS =================

    ARQUIVO_LOG = Path(__file__).resolve().parent / "away_log.txt"

    def __init__(self) -> None:
        """Inicializa os contadores e o estado da automação."""
        self.rodando = True
        self.pausado = False
        self.saida_automatica = False

        self.contador_ciclos = 0
        self.contador_comidas = 0
        self.contador_aguas = 0
        self.contador_salarios = 0

        self.comidas_restantes = self.COMIDA_INICIAL
        self.aguas_restantes = self.AGUA_INICIAL

        self.total_ganho = 0.0

        self.inicio_execucao = monotonic()
        self.tempo_ativo_total = 0.0
        self.ultimo_instante_ativo = monotonic()

        self.tempo_desde_ultimo_salario = 0.0

        pydirectinput.PAUSE = 0.05

    # ============================================================
    # FORMATAÇÃO E LOG
    # ============================================================

    @staticmethod
    def formatar_tempo(segundos: float) -> str:
        """Converte segundos para o formato HH:MM:SS."""
        total = max(0, int(segundos))

        horas = total // 3600
        minutos = (total % 3600) // 60
        segundos_restantes = total % 60

        return f"{horas:02d}:{minutos:02d}:{segundos_restantes:02d}"

    @staticmethod
    def formatar_dinheiro(valor: float) -> str:
        """Converte um valor para o padrão monetário brasileiro."""
        formatado = f"{valor:,.2f}"
        formatado = formatado.replace(",", "X")
        formatado = formatado.replace(".", ",")
        formatado = formatado.replace("X", ".")

        return f"R$ {formatado}"

    def registrar_log(self, mensagem: str) -> None:
        """Registra uma ação no arquivo de histórico."""
        horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        linha = f"[{horario}] {mensagem}\n"

        try:
            with self.ARQUIVO_LOG.open(
                mode="a",
                encoding="utf-8",
            ) as arquivo:
                arquivo.write(linha)
        except OSError as erro:
            print(f"Não foi possível gravar o log: {erro}")

    # ============================================================
    # ESTADO E CONTADORES
    # ============================================================

    def ciclos_possiveis(self) -> int:
        """Calcula quantos ciclos completos ainda podem ser executados."""
        ciclos_por_comida = self.comidas_restantes
        ciclos_por_agua = self.aguas_restantes // self.AGUAS_POR_COMIDA

        return min(ciclos_por_comida, ciclos_por_agua)

    def estoque_suficiente(self) -> bool:
        """Verifica se existe estoque para outro ciclo completo."""
        return (
            self.comidas_restantes >= 1
            and self.aguas_restantes >= self.AGUAS_POR_COMIDA
        )

    def atualizar_tempo_ativo(self) -> None:
        """Atualiza o tempo ativo, desconsiderando períodos pausados."""
        agora = monotonic()

        if not self.pausado:
            tempo_decorrido = agora - self.ultimo_instante_ativo
            self.tempo_ativo_total += tempo_decorrido
            self.tempo_desde_ultimo_salario += tempo_decorrido

        self.ultimo_instante_ativo = agora

    # ============================================================
    # CONTROLES
    # ============================================================

    def alternar_pausa(self) -> None:
        """Pausa ou continua a automação utilizando F6."""
        self.atualizar_tempo_ativo()
        self.pausado = not self.pausado

        if self.pausado:
            mensagem = "Automação pausada."
        else:
            self.ultimo_instante_ativo = monotonic()
            mensagem = "Automação continuada."

        print(f"\n{mensagem}")
        self.registrar_log(mensagem)

    def encerrar_manualmente(self) -> None:
        """Encerra somente o script utilizando F7."""
        self.atualizar_tempo_ativo()
        self.rodando = False

        print("\nEncerramento manual solicitado.")
        self.registrar_log("Encerramento manual solicitado pelo usuário.")

    def aguardar_se_pausado(self) -> None:
        """Mantém o programa aguardando enquanto estiver pausado."""
        while self.pausado and self.rodando:
            self.ultimo_instante_ativo = monotonic()
            sleep(0.25)

    # ============================================================
    # TECLADO
    # ============================================================

    @staticmethod
    def pressionar(tecla: str, espera: float = 0.1) -> None:
        """Pressiona uma tecla e aguarda o tempo informado."""
        pydirectinput.press(tecla)
        sleep(espera)

    @staticmethod
    def escrever(texto: str) -> None:
        """Digita um texto usando o teclado."""
        pydirectinput.write(texto, interval=0.05)

    @staticmethod
    def liberar_teclas() -> None:
        """Garante que teclas de movimento não permaneçam pressionadas."""
        teclas = ["w", "a", "s", "d"]

        for tecla in teclas:
            try:
                pydirectinput.keyUp(tecla)
            except Exception:
                pass

    # ============================================================
    # MOVIMENTAÇÃO
    # ============================================================

    def movimentar_personagem(self) -> None:
        """Movimenta o personagem em diferentes direções com Shift."""
        movimentos = self.TECLAS_MOVIMENTO.copy()
        shuffle(movimentos)

        self.registrar_log(
            "Iniciada movimentação para manter personagem acordado."
        )

        try:
            for tecla in movimentos:
                if not self.rodando or self.pausado:
                    break

                duracao = uniform(
                    self.TEMPO_MINIMO_MOVIMENTO,
                    self.TEMPO_MAXIMO_MOVIMENTO,
                )

                pydirectinput.keyDown(self.TECLA_CORRER)
                pydirectinput.keyDown(tecla)

                sleep(duracao)

                pydirectinput.keyUp(tecla)
                pydirectinput.keyUp(self.TECLA_CORRER)

                sleep(self.INTERVALO_ENTRE_MOVIMENTOS)

        finally:
            self.liberar_teclas()

        self.registrar_log(
            "Movimentação para manter personagem acordado concluída."
        )

    # ============================================================
    # COMIDA E ÁGUA
    # ============================================================

    def comer(self) -> None:
        """Usa uma unidade de comida."""
        if self.comidas_restantes <= 0:
            return

        self.pressionar(
            self.TECLA_COMER,
            self.TEMPO_USAR_ITEM,
        )

        self.contador_comidas += 1
        self.comidas_restantes -= 1

        self.registrar_log(
            f"Comida utilizada. Restam {self.comidas_restantes}."
        )

    def beber(self) -> None:
        """Usa a quantidade de águas definida para cada comida."""
        for numero_agua in range(1, self.AGUAS_POR_COMIDA + 1):
            if not self.rodando or self.aguas_restantes <= 0:
                break

            self.pressionar(
                self.TECLA_BEBER,
                self.TEMPO_USAR_ITEM,
            )

            self.contador_aguas += 1
            self.aguas_restantes -= 1

            self.registrar_log(
                f"Água {numero_agua}/{self.AGUAS_POR_COMIDA} utilizada. "
                f"Restam {self.aguas_restantes}."
            )

            if numero_agua < self.AGUAS_POR_COMIDA:
                sleep(self.INTERVALO_ENTRE_ITENS)

    def executar_alimentacao(self) -> None:
        """Executa um ciclo completo de comida e água."""
        self.registrar_log(
            f"Iniciando ciclo {self.contador_ciclos + 1}."
        )

        self.comer()

        if not self.rodando:
            return

        sleep(self.INTERVALO_ENTRE_ITENS)

        self.beber()

        if not self.rodando:
            return

        self.contador_ciclos += 1

        self.registrar_log(
            f"Ciclo {self.contador_ciclos} concluído."
        )

        self.mostrar_resumo_ciclo()

    # ============================================================
    # SALÁRIO
    # ============================================================

    def verificar_salario(self) -> None:
        """Atualiza os salários conforme o tempo ativo."""
        while self.tempo_desde_ultimo_salario >= self.TEMPO_SALARIO:
            self.tempo_desde_ultimo_salario -= self.TEMPO_SALARIO

            self.contador_salarios += 1
            self.total_ganho += self.VALOR_SALARIO

            mensagem = (
                f"Salário {self.contador_salarios} recebido: "
                f"{self.formatar_dinheiro(self.VALOR_SALARIO)} | "
                f"Total: {self.formatar_dinheiro(self.total_ganho)}"
            )

            print(f"\n{mensagem}")
            self.registrar_log(mensagem)

    # ============================================================
    # ESPERA DO CICLO
    # ============================================================

    def aguardar_proximo_ciclo(self) -> None:
        """Aguarda o próximo ciclo e movimenta o personagem a cada minuto."""
        tempo_ciclo_ativo = 0.0
        tempo_desde_movimento = 0.0
        ultima_medicao = monotonic()

        while self.rodando and tempo_ciclo_ativo < self.TEMPO_CICLO:
            self.aguardar_se_pausado()

            if not self.rodando:
                return

            agora = monotonic()
            decorrido = agora - ultima_medicao
            ultima_medicao = agora

            tempo_ciclo_ativo += decorrido
            tempo_desde_movimento += decorrido

            self.atualizar_tempo_ativo()
            self.verificar_salario()

            if tempo_desde_movimento >= self.INTERVALO_MOVIMENTO:
                self.movimentar_personagem()
                tempo_desde_movimento = 0.0
                ultima_medicao = monotonic()

            sleep(0.25)

    # ============================================================
    # SAÍDA
    # ============================================================

    def sair_do_servidor(self) -> None:
        """Abre o F8, digita exit e confirma com Enter."""
        if self.saida_automatica:
            return

        self.saida_automatica = True

        print("\nEstoque finalizado.")
        print("Executando F8 -> exit -> Enter...")

        self.registrar_log(
            "Estoque finalizado. Executando F8 -> exit -> Enter."
        )

        self.liberar_teclas()

        pydirectinput.press("f8")
        sleep(1)

        self.escrever("exit")
        sleep(0.5)

        pydirectinput.press("enter")
        sleep(1)

        self.rodando = False

    # ============================================================
    # TERMINAL
    # ============================================================

    def mostrar_inicio(self) -> None:
        """Apresenta as configurações iniciais no terminal."""
        print("=" * 64)
        print("           AUTO COMER / BEBER - CAPITAL CITY")
        print("=" * 64)
        print(f"Comidas iniciais........: {self.comidas_restantes}")
        print(f"Águas iniciais..........: {self.aguas_restantes}")
        print(f"Proporção...............: 1 comida / {self.AGUAS_POR_COMIDA} águas")
        print(f"Ciclos possíveis........: {self.ciclos_possiveis()}")
        print(f"Intervalo dos ciclos....: {self.TEMPO_CICLO // 60} minutos")
        print(f"Movimentação............: a cada {self.INTERVALO_MOVIMENTO // 60} minuto")
        print(f"Salário.................: {self.formatar_dinheiro(self.VALOR_SALARIO)}")
        print(f"Intervalo do salário....: {self.TEMPO_SALARIO // 60} minutos")
        print("-" * 64)
        print(f"{self.TECLA_PAUSAR.upper()} = Pausar / Continuar")
        print(f"{self.TECLA_ENCERRAR.upper()} = Encerrar manualmente")
        print("=" * 64)
        print(
            f"Iniciando em {self.TEMPO_INICIALIZACAO} segundos. "
            "Deixe o FiveM em foco."
        )

    def mostrar_resumo_ciclo(self) -> None:
        """Mostra o resumo somente ao final de cada ciclo."""
        proximo_salario = max(
            0,
            self.TEMPO_SALARIO - self.tempo_desde_ultimo_salario,
        )

        print("\n" + "=" * 64)
        print(f"                 CICLO {self.contador_ciclos} CONCLUÍDO")
        print("=" * 64)
        print(
            f"Tempo ativo..............: "
            f"{self.formatar_tempo(self.tempo_ativo_total)}"
        )
        print(f"Comidas usadas...........: {self.contador_comidas}")
        print(f"Águas usadas.............: {self.contador_aguas}")
        print(f"Comidas restantes........: {self.comidas_restantes}")
        print(f"Águas restantes..........: {self.aguas_restantes}")
        print(f"Ciclos restantes.........: {self.ciclos_possiveis()}")
        print("-" * 64)
        print(f"Salários recebidos.......: {self.contador_salarios}")
        print(
            f"Total ganho..............: "
            f"{self.formatar_dinheiro(self.total_ganho)}"
        )
        print(
            f"Próximo salário..........: "
            f"{self.formatar_tempo(proximo_salario)}"
        )
        print("=" * 64)

    def mostrar_encerramento(self) -> None:
        """Apresenta o resumo final da execução."""
        print("\n" + "=" * 64)
        print("                    PROCESSO ENCERRADO")
        print("=" * 64)
        print(f"Ciclos executados........: {self.contador_ciclos}")
        print(f"Comidas usadas...........: {self.contador_comidas}")
        print(f"Águas usadas.............: {self.contador_aguas}")
        print(f"Comidas restantes........: {self.comidas_restantes}")
        print(f"Águas restantes..........: {self.aguas_restantes}")
        print(f"Salários recebidos.......: {self.contador_salarios}")
        print(
            f"Total ganho..............: "
            f"{self.formatar_dinheiro(self.total_ganho)}"
        )
        print(
            f"Tempo ativo..............: "
            f"{self.formatar_tempo(self.tempo_ativo_total)}"
        )
        print("=" * 64)

    # ============================================================
    # EXECUÇÃO PRINCIPAL
    # ============================================================

    def configurar_atalhos(self) -> None:
        """Registra os atalhos globais da aplicação."""
        keyboard.add_hotkey(
            self.TECLA_PAUSAR,
            self.alternar_pausa,
        )

        keyboard.add_hotkey(
            self.TECLA_ENCERRAR,
            self.encerrar_manualmente,
        )

    def executar(self) -> None:
        """Executa o ciclo principal da automação."""
        self.configurar_atalhos()
        self.mostrar_inicio()

        self.registrar_log(
            "Automação iniciada com "
            f"{self.comidas_restantes} comidas e "
            f"{self.aguas_restantes} águas."
        )

        sleep(self.TEMPO_INICIALIZACAO)

        self.inicio_execucao = monotonic()
        self.ultimo_instante_ativo = monotonic()

        try:
            while self.rodando:
                if not self.estoque_suficiente():
                    self.sair_do_servidor()
                    break

                self.aguardar_proximo_ciclo()

                if not self.rodando:
                    break

                if not self.estoque_suficiente():
                    self.sair_do_servidor()
                    break

                self.executar_alimentacao()

                if not self.estoque_suficiente():
                    self.sair_do_servidor()
                    break

        except KeyboardInterrupt:
            self.rodando = False
            self.registrar_log(
                "Automação interrompida pelo terminal."
            )

        except Exception as erro:
            self.rodando = False
            self.registrar_log(
                f"Erro inesperado: {type(erro).__name__}: {erro}"
            )

            print(
                f"\nErro inesperado: "
                f"{type(erro).__name__}: {erro}"
            )

        finally:
            self.atualizar_tempo_ativo()
            self.liberar_teclas()

            keyboard.unhook_all_hotkeys()

            self.registrar_log("Automação finalizada.")
            self.mostrar_encerramento()


if __name__ == "__main__":
    bot = AwayBot()
    bot.executar()