from pyautogui import *
from time import sleep

import pyautogui

id_user = 0


def reviver():
    global id_user

    sleep(2)
    #PEgar o id

    pyautogui.press('1')


def tratamento ():
    sleep(2)

def opcoes():
    global id_user

    print("ESCOLHA A OPÇÃO ABAIXO")
    print('[1] - REVIVER'
       ' | [2] - TRATAMENTO'
       ' | [3] - SAIR')
    choice = int(input(''))
    if choice == 1:
        print("Digite o ID do paciente: ")
        id_user = int(input())
        reviver
        print("Paciente vai querer tratamento:")
        choice2 = int(input(''),UPPER)
        if choice == "S":
            

    elif choice == 2:
        tratamento
    else:
        exit


opcoes()
