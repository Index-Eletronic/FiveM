
from time import sleep
import pyautogui
import pydirectinput


def acordado():
    while True:
            sleep(2)
            pydirectinput.press("ctrl")
            sleep(2)
            pydirectinput.press("ctrl")
            sleep(60)

acordado()
