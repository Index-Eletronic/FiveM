import pyautogui
from time import sleep

def correr(x):
    while True:
        if isinstance(x, str):
            pyautogui.press(run)
            sleep(34)

        elif print("DIGITE APENAS A HOTKEY: ex ( F9 )"):
            pergunta()
        else:
             break

def pergunta():
    global run

    run = str(input("DIGITE A HOTKEY DA MANA POTION: "))
    print(type(run))
    sleep(5)
    correr(run)



pergunta()


