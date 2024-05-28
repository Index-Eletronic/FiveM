import pyautogui
from time import sleep


sleep(3)
questoes = ['iniciar', 'Qual seu nome', 'Qual seu genero', 'Data de Nascimento', 'Como conheceu a Capital',
            'Qual Experiencia com Role Play?',
            'Criado de Conteudo?', 'Quais Cidades Realizou RP?', 'Já foi banido?', 'Quanto tempo faz RP?',
            '10 - ) Qual jornada na capital e por que deveriamos aceita-lo?',
            'Experiencia como ADM??', 'Ja fez Rp de policia, experiencia?', 'Ja fez Rp de hospital, experiencia?',
            'Ja fez Rp de mecanico, experiencia?', 'Regras pra um bom RP',
            'Regras desnecessarias para Bom RP', 'Segredo pra um bom RP',
            'Qual area? (policia, bombeiro, mecanica, ilegal, pista, livre)..', 'Player sugere que vão para o Discord',
            'Metagamming?, qual punição?', 'Encontra o Streamer qual a reação?', 'Qual histo do personagem']

resp10 = ("Inicialmente, acordaria na cidade despois de anos em coma. Homem de muitas habilidades, buscaria no jornal alguma oportunidade de emprego para ganhar a vida."
          "Player com experiencia em RP, nunca fui banido por nenhum motivo e sempre segui as regras da cidade buscando fazer o melhor RP.")

resp = [r'iniciar'
            ,'Filipe Tuon'
            ,'Masculino'
            ,'15/06/1987'
            ,'Atraves do YouTube com o canal do streamer Paulinho o Loko'
            ,'Minha experiência com RP é mais de 1 ano como Sub Tenente do Exercito Brasileiro na cidade de Paraisopolis'
            ,'2'
            ,'Realizei RP nas cidades de: Paraisopolis e Berlim'
            ,'Nunca foi banido.'
            ,'Faco RP há 2 anos.'
            ,resp10
            ,'Não tenho experiência como ADM, porem como programador.'
            ,'Sim, fui Sub Tenente do E.B. Experiência muito boa, tenho amigos ate hoje em Narnia.'
            ,'Sim. Primeiro emprego em RP. Experiencia de pouco tempo, mas muito boa.'
            ,'Como Mecanico, nunca fiz RP.'
            ,'Valorizar sua vida acima de tudo. Não matar ninguem a não ser que seja necessario. Ter comportamento condinzentes com a vida real'
            ,'Amor à vida, Anti Corrupcao, Ofensa desnecessaria, Meta Gaming.'
            ,'Ter iniciativa, evitar players toxicos, ter experiencia, ter amigos, ter uma profissao'
            ,'Possivelmente policia, porem depende da disponibilidade dos empregos nos jornais.'
            ,'Neste caso, se for em meio a imersão do game, eu diria que nao sei o que é. E talvez disconversaria para outro assunto ou resolver a questão ali mesmo'
            ,'E a utilizacao de informacoes externas para obter vantagens dentro do jogo. Neste caso, na minha opiniao é banimento.'
            ,'Sendo streamer uma profissao não existente na cidade. Minha reação seria "segue o RP", continuando a ocasião do momento',
            'Inicialmente, acordaria na cidade despois de anos em coma. Homem de muitas habilidades, buscaria no jornal alguma oportunidade de emprego para ganhar a vida. Conhencendo pessoas, fazendo amizades e inimigos...']
c2 = 0

sleep(3)
for r in resp:
    pyautogui.write(resp[c2])
    sleep(2)
    pyautogui.press('enter')
    c2 += 1
    #print(f'{resp[c2]}')
    sleep(3
          )








