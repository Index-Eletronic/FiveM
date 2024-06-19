from pyautogui import *
from time import sleep

import pyautogui

#unbinds = [0,1,2,3,'f9']
# #binds =


'''
1 cobrança
digitar 1
f8 > cobrar id 6000
enter
f8
y 2 x
esperar confirmar, y ou n
caso seja n, repetir o processo 2 x


'''


id_user = 0


def reviver():
    global id_user
    tentativa = 0

    sleep(2)
    #PEgar o id
    pyautogui.press('1')
    sleep(2)
    pyautogui.press('1') #f8
    sleep(1)
    pyautogui.write(f'cobrar {id_user} 6000')
    sleep(3)
    pyautogui.press ('1') #enter
    sleep(1)
    pyautogui.press('1') #f8
    sleep(1)

    escolha = str(input("Paciente aceitou? [S] | [N]".upper().strip()))
    if escolha == "S" or escolha == "s":
        tratamento()
    if tentativa == 2:
        tentativa +=1
        reviver()
    else:
        opcoes()



def tratamento ():
    sleep(2)
    #PEgar o id
    pyautogui.press('1')
    sleep(2)
    pyautogui.press('1') #f8
    sleep(1)
    pyautogui.write(f'cobrar {id_user} 6000')
    sleep(3)
    pyautogui.press ('1') #enter
    sleep(1)
    pyautogui.press('1') #f8
    sleep(5)

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
        reviver()
        print("Paciente vai querer tratamento:")
        choice2 = str(input('').upper().strip())
        if choice2 == "S":
            tratamento()
        else:
            opcoes()

    elif choice == 2:
        tratamento
    else:
        exit


opcoes()
