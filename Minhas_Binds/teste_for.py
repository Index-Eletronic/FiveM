import pyautogui
from time import sleep

print("=~= SISTEMA DE BINDS =~= ")

#pyautogui.hotkey('alt', 'tab')
enter = str(input("PRECIONE ENTER PARA COMEÇAR, E VOLTE PARA JANELA DO GAME"))
sleep(2)
unbind = [6,7,8,9,0]
bind = ["prg","revistar","apreender","painel","doors"]

for i in unbind:
  pyautogui.write(f'unbind keyboard"{i}"')
  pyautogui.press('enter')
  print(f'unbind keyboard"{i}"')
  sleep(1)
for i in bind:
    pyautogui.write(f'bind keyboard"{i}"')
    pyautogui.press('enter')
    print(f'bind keyboard"{i}"')
    sleep(1)

print("=~= FINALIZADO =~= ")
print("=~= develop SURICATA FURIOSA =~= ")