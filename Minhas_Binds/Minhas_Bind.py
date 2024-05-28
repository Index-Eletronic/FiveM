import pyautogui
from time import sleep

print("=~= SISTEMA DE BINDS PADRÃO =~= ")
print("==========================================================")
print(" ")

#pyautogui.hotkey('alt', 'tab')
enter = str(input("PRECIONE ENTER PARA COMEÇAR, E VOLTE PARA JANELA DO GAME"))
print("")
print("COMEÇANDO.. NÃO SAIDA DA TELA DO GAME")
print("")
sleep(6)
unbind = [6,7,8,9,0]
bind = ["e flexao","e abdominal","e malhar2","",""]

pyautogui.write('toogle')
pyautogui.press('enter')
sleep(1)
for i in unbind:
  pyautogui.write(f'unbind keyboard"{i}"')
  pyautogui.press('enter')
  print(f'LIMPANDO A TECLA: {i} ')
  sleep(1)
for i,n in zip(unbind, bind):
    pyautogui.write(f'bind keyboard"{i}""{n}"')
    pyautogui.press('enter')
    print(f'BIND PARA A TECLA: "{i}" "{n}"')
    sleep(1)

sleep(2)
print("=~= FINALIZADO =~= ")
sleep(2)
print("=~= develop SURICATA FURIOSA =~= ")
sleep(15)
