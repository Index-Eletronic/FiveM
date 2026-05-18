import pyautogui
from time import sleep


fardas_masc = ["mascara 239 0; maos 31 0; chapeu 104 20; jaqueta 562 0; colete 82 0; acessorios 215 0; calca 210 0; sapatos 24 0; oculos 25 4",
               "acessorios 14; calca 210; jaqueta 562 0; mascara 170 0; chapeu 107 20; sapatos 24 0; maos 17 0; COLETE 89",
               "jaqueta 516 3; calca 87 3; blusa 210 0; sapatos 36 0; oculos -1 -1; acessorio 14 1; chapeu 104 5; colete 0 0; mascara 0 0; maos 38 1;"]

unbind = [6,7,8,9,0,"i"]
bind = ["e cruzar7",
         "e continencia",
         "e deitar",
          "e rastejar",
           "e pose23"]

acessorio = ["chapeu","oculos","mascara", "acessorios"]


def unbinds():
    for i in unbind:
      pyautogui.write(f'unbind keyboard"{i}"')
      pyautogui.press('enter')
      print(f'LIMPANDO A TECLA: {i} ')
      sleep(2)


def binds():
    for i,n in zip(unbind, bind):
        pyautogui.write(f'bind keyboard"{i}""{n}"')
        pyautogui.press('enter')
        print(f'BIND PARA A TECLA: "{i}" "{n}"')
        sleep(2)

def roupas():
    print(f'FARDAMENTO 1: BAC OPERACIONAL  - FARDAMENTO 2: ALUNO BAC  -  FARDAMENTO 3: CAATINGA \n')
    op = int(input("OPÇÃO: "))
    if op == 1:
        #print(fardas_masc[0])
        pyautogui.write(fardas_masc[0])
        sleep(1)
        pyautogui.press("enter")
    elif op == 2:
        pyautogui.write(fardas_masc[1])
        sleep(1)
        pyautogui.press("enter")
    elif op == 3:
        pyautogui.write(fardas_masc[2])
        sleep(1)
        pyautogui.press("enter")
    else:
        cabecalho(op)


def cabecalho():
    print(f"OPÇÕES: [1] - LIMPAR BINDS\n [2] - COLOCAR BINDS\n [3] - FARDAMENTO")
    while True:
        def op1():
            print(f"OPÇÕES: [1] - LIMPAR BINDS")
            unbinds()
        def op2():
            print(f"[2] - COLOCAR BINDS")
            binds()
        def op3():
            print(f"[3] - FARDAMENTO")
            roupas()
    else:
        pass



cabecalho()