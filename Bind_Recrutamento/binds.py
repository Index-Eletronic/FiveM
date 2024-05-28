import pyautogui
from time import sleep


unbind = [6,7,8,9,0,"i"]
bind = ["e meditar2; e continencia",
         "e cruzar7",
         "e flexao",
          "e abdominal",
           "e malhar2","e roubar"]

acessorio = ["chapeu","oculos","mascara", "acessorios"]

unif_M = ["chapeu","mascara 0 0","jaqueta 22 0","blusa 15 0","maos 0 0","calca 46 0","sapatos 25 0","acessorios 0 0","oculos", "mochila 0 0", "colete 0 0"]
unif_F = ["chapeu","mascara 0 0","jaqueta 118 0","blusa 6 0","maos 15 0","calca 61 9","sapatos 25 0","acessorios 0 0","oculos", "mochila 0 0", "colete 0 0"]


print("=~= SISTEMA DE RECRUTAMENTO EXERCITO BRASILEIRO  - PARAISOPOLIS =~= ")
print("==========================================================")
print(" ")

#pyautogui.hotkey('alt', 'tab')

#enter = str(input("PRECIONE ENTER PARA COMEÇAR, E VOLTE PARA JANELA DO GAME"))
def unbinds():
    for i in unbind:
      pyautogui.write(f'unbind keyboard"{i}"')
      pyautogui.press('enter')
      print(f'LIMPANDO A TECLA: {i} ')
      sleep(2)


def abinds():
    for i,n in zip(unbind, bind):
        pyautogui.write(f'bind keyboard"{i}""{n}"')
        pyautogui.press('enter')
        print(f'BIND PARA A TECLA: "{i}" "{n}"')
        sleep(2)


def limpar():
    for i in acessorio:
        pyautogui.write(f"{i}")
        pyautogui.press('enter')
        print(f'REMOVENDO: {i}\n')
        sleep(6)

def cabecalho():
    print("")
    print("ATENÇÃO: VOLTE PARA O GAME -  APERTE 'F8', CLIQUE PARA DIGITAR. NÃO MEXA ATÈ FINALIZAR")
    print("")
    sleep(5)
    print(f'COMEÇANDO EM...VOLTE PARA O GAME: 10seg')

def final():
    pyautogui.write("FINALIZADO...")
    pyautogui.press('enter')
    pyautogui.write("Develop SURICATA FURIOSA.")
    pyautogui.press('enter')
    pyautogui.write("BRASIL ACIMA DE TODOS DEUS ACIMA DE NOS")

sexo = enter = str(input("QUAL SEU SEXO [[M]asculino / [F]eminino ]: ").strip().upper())

if sexo == "M" or sexo == "m":
        cabecalho()

        print("UNIFORME MASCULINO")
        for i in unif_M:
            pyautogui.write(f'{i}')
            sleep(4)
            pyautogui.press('enter')
        sleep(1)
        unbinds()
        sleep(1)
        abinds()
        final()
elif sexo == "F" or sexo == "f":
        cabecalho()
        print("UNIFORME FEMININO")
        pyautogui.write(unif_F)
        pyautogui.press('enter')
        sleep(3)
        #limpar()
        sleep(1)
        unbinds()
        sleep(1)
        abinds()
        final()
else:
    print('DIGITE SEU APENAS "H" para homem e "M" para Mulher: ')
    exit()


pyautogui.hotkey('alt', 'tab')

pyautogui.press('enter')
sleep(2)
print("=~= FINALIZADO =~= ")
sleep(2)
print("=~= develop SURICATA FURIOSA =~= ")
sleep(15)