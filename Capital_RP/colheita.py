from time import sleep, time

import cv2
import numpy as np
import pyautogui
import pydirectinput


pyautogui.FAILSAFE = True
pydirectinput.PAUSE = 0.05


# ============================================================
# CONFIGURAÇÕES
# ============================================================

AREA_MINIMA_DETECCAO = 1500

# Considera que chegou ao alvo quando uma destas condições ocorrer.
ALTURA_ALVO_PROXIMO = 370
AREA_ALVO_PROXIMO = 38000

# Tempo máximo andando até uma árvore.
TEMPO_MAXIMO_ATE_ALVO = 40

# Tempo aguardando após pressionar E.
TEMPO_COLETA = 5

# Movimento obrigatório para sair do alvo atual.
TEMPO_SAIDA = 2

# Quantidade de leituras sem alvo antes de parar.
LIMITE_ALVO_PERDIDO = 15


# ============================================================
# CONTROLE DAS TECLAS
# ============================================================

def soltar_teclas():
    for tecla in ("w", "a", "s", "d"):
        pydirectinput.keyUp(tecla)


# ============================================================
# DETECÇÃO DO TRIÂNGULO VERMELHO
# ============================================================

def detectar_triangulo_vermelho():
    screenshot = pyautogui.screenshot()

    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    altura_tela, largura_tela = frame.shape[:2]

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    vermelho_baixo1 = np.array([0, 90, 90])
    vermelho_alto1 = np.array([12, 255, 255])

    vermelho_baixo2 = np.array([168, 90, 90])
    vermelho_alto2 = np.array([180, 255, 255])

    mascara1 = cv2.inRange(
        hsv,
        vermelho_baixo1,
        vermelho_alto1
    )

    mascara2 = cv2.inRange(
        hsv,
        vermelho_baixo2,
        vermelho_alto2
    )

    mascara = cv2.bitwise_or(mascara1, mascara2)

    kernel = np.ones((5, 5), np.uint8)

    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_CLOSE,
        kernel
    )

    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_OPEN,
        kernel
    )

    contornos, _ = cv2.findContours(
        mascara,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidatos = []

    for contorno in contornos:
        area = cv2.contourArea(contorno)

        if area < AREA_MINIMA_DETECCAO:
            continue

        x, y, largura, altura = cv2.boundingRect(contorno)

        if largura < 20 or altura < 40:
            continue

        centro_x = x + largura // 2
        centro_y = y + altura // 2

        if centro_y < altura_tela * 0.15:
            continue

        candidatos.append(
            {
                "area": area,
                "x": x,
                "y": y,
                "largura": largura,
                "altura": altura,
                "centro_x": centro_x,
                "centro_y": centro_y,
                "largura_tela": largura_tela,
                "altura_tela": altura_tela
            }
        )

    if not candidatos:
        return {
            "encontrou": False,
            "largura_tela": largura_tela,
            "altura_tela": altura_tela
        }

    centro_tela_x = largura_tela // 2

    # Escolhe o alvo vermelho mais próximo do centro da tela.
    melhor_alvo = min(
        candidatos,
        key=lambda alvo: (
            abs(alvo["centro_x"] - centro_tela_x),
            -alvo["area"]
        )
    )

    melhor_alvo["encontrou"] = True

    return melhor_alvo


# ============================================================
# IR ATÉ O ALVO
# ============================================================

def ir_ate_alvo(tempo_maximo=TEMPO_MAXIMO_ATE_ALVO):
    print("Indo até o alvo...")

    inicio = time()
    alvo_perdido = 0

    pydirectinput.keyDown("w")

    try:
        while time() - inicio <= tempo_maximo:
            alvo = detectar_triangulo_vermelho()

            if not alvo["encontrou"]:
                alvo_perdido += 1

                print(
                    f"Alvo temporariamente perdido "
                    f"({alvo_perdido}/{LIMITE_ALVO_PERDIDO})"
                )

                if alvo_perdido >= LIMITE_ALVO_PERDIDO:
                    pydirectinput.keyUp("w")
                    print("Alvo perdido.")
                    return False

                sleep(0.10)
                continue

            alvo_perdido = 0

            altura = alvo["altura"]
            area = int(alvo["area"])

            print(
                f"Alvo detectado | "
                f"Altura={altura} | "
                f"Área={area}"
            )

            chegou = (
                altura >= ALTURA_ALVO_PROXIMO
                or area >= AREA_ALVO_PROXIMO
            )

            if chegou:
                pydirectinput.keyUp("w")

                print("Alvo alcançado.")
                sleep(0.5)

                return True

            sleep(0.10)

        pydirectinput.keyUp("w")
        print("Tempo máximo atingido.")
        return False

    except Exception as erro:
        pydirectinput.keyUp("w")
        print(f"Erro ao ir até o alvo: {erro}")
        return False


# ============================================================
# SAIR DO ALVO ATUAL
# ============================================================

def sair_do_alvo():
    print(f"Saindo do alvo por {TEMPO_SAIDA} segundos...")

    pydirectinput.keyDown("w")
    sleep(TEMPO_SAIDA)
    pydirectinput.keyUp("w")

    print("Procurando próximo alvo...")
    sleep(0.3)


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def executar():
    print("Iniciando em 3 segundos...")
    sleep(3)

    while True:
        try:
            alvo = detectar_triangulo_vermelho()

            if not alvo["encontrou"]:
                print("Nenhum alvo visível.")
                sleep(0.4)
                continue

            print(
                f"Alvo localizado | "
                f"X={alvo['centro_x']} | "
                f"Y={alvo['centro_y']} | "
                f"Altura={alvo['altura']} | "
                f"Área={int(alvo['area'])}"
            )

            chegou = ir_ate_alvo()

            if not chegou:
                sleep(0.5)
                continue

            # Garante que W está solto antes de interagir.
            pydirectinput.keyUp("w")
            sleep(0.3)

            print("Pressionando a tecla E...")
            pydirectinput.press("e")

            print(
                f"Tecla E pressionada. "
                f"Aguardando {TEMPO_COLETA} segundos..."
            )

            sleep(TEMPO_COLETA)

            sair_do_alvo()

        except KeyboardInterrupt:
            soltar_teclas()
            print("\nPrograma interrompido.")
            break

        except Exception as erro:
            soltar_teclas()
            print(f"Erro geral: {erro}")
            sleep(1)


if __name__ == "__main__":
    executar()