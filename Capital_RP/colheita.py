from time import sleep, time
import pyautogui
import pydirectinput
import cv2
import numpy as np


pyautogui.FAILSAFE = True


def detectar_triangulo_vermelho():
    screenshot = pyautogui.screenshot()

    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    altura_tela, largura_tela = frame.shape[:2]

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    vermelho_baixo1 = np.array([0, 80, 80])
    vermelho_alto1 = np.array([10, 255, 255])

    vermelho_baixo2 = np.array([170, 80, 80])
    vermelho_alto2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, vermelho_baixo1, vermelho_alto1)
    mask2 = cv2.inRange(hsv, vermelho_baixo2, vermelho_alto2)

    mask = cv2.bitwise_or(mask1, mask2)

    contornos, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    maior_area = 0
    melhor_contorno = None

    for contorno in contornos:
        area = cv2.contourArea(contorno)

        if area > maior_area:
            maior_area = area
            melhor_contorno = contorno

    if melhor_contorno is not None and maior_area > 1500:
        x, y, w, h = cv2.boundingRect(melhor_contorno)

        centro_x = x + w // 2
        centro_y = y + h // 2

        return {
            "encontrou": True,
            "centro_x": centro_x,
            "centro_y": centro_y,
            "largura_tela": largura_tela,
            "altura_tela": altura_tela,
            "area": maior_area
        }

    return {"encontrou": False}


def centralizar_no_triangulo():
    alvo = detectar_triangulo_vermelho()

    if not alvo["encontrou"]:
        return False

    centro_tela_x = alvo["largura_tela"] // 2
    centro_tela_y = alvo["altura_tela"] // 2

    erro_x = alvo["centro_x"] - centro_tela_x
    erro_y = alvo["centro_y"] - centro_tela_y

    tolerancia_x = 60
    tolerancia_y = 80

    print(f"Erro X={erro_x} | Erro Y={erro_y}")

    if erro_x < -tolerancia_x:
        pydirectinput.press("a")
        sleep(0.10)

    elif erro_x > tolerancia_x:
        pydirectinput.press("d")
        sleep(0.10)

    if erro_y < -tolerancia_y:
        pydirectinput.press("w")
        sleep(0.10)

    elif erro_y > tolerancia_y:
        pydirectinput.press("s")
        sleep(0.10)

    centralizado_x = abs(erro_x) <= tolerancia_x
    centralizado_y = abs(erro_y) <= tolerancia_y

    return centralizado_x and centralizado_y


def andar_ate_proximo_triangulo(tempo_maximo=25):
    print("Andando até encontrar o próximo alvo...")

    pydirectinput.keyDown("w")

    inicio = time()

    try:
        while True:
            alvo = detectar_triangulo_vermelho()

            if alvo["encontrou"]:
                print("Triângulo encontrado.")

                sleep(2)

                pydirectinput.keyUp("w")

                print("Parado no alvo.")
                return True

            if time() - inicio > tempo_maximo:
                print("Tempo máximo atingido.")
                pydirectinput.keyUp("w")
                return False

            sleep(0.2)

    except Exception as erro:
        pydirectinput.keyUp("w")
        print(f"Erro ao andar: {erro}")
        return False


print("Iniciando...")
sleep(3)


while True:
    try:
        alvo = detectar_triangulo_vermelho()

        if alvo["encontrou"]:
            print("Alvo localizado.")

            tentativas = 0

            while not centralizar_no_triangulo():
                tentativas += 1

                if tentativas > 20:
                    break

                sleep(0.2)

            print("Centralizado.")

            pydirectinput.press("e")

            print("Aguardando coleta...")
            sleep(8)

            andar_ate_proximo_triangulo()

            sleep(1)

        else:
            print("Nenhum alvo encontrado.")
            sleep(0.5)

    except Exception as erro:
        pydirectinput.keyUp("w")
        pydirectinput.keyUp("a")
        pydirectinput.keyUp("s")
        pydirectinput.keyUp("d")

        print(f"Erro: {erro}")
        sleep(2)