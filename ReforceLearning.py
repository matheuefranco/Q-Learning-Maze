#Baseado em https://github.com/bvpsk/Reinforcement-learning.git
import numpy as np
import pygame
from time import time, sleep
from random import randint as r
import random
import pickle
import os
import argparse

parser_semente = argparse.ArgumentParser(add_help=False)
parser_semente.add_argument("--seed", type=int, help="semente para reproduzir o ambiente e o treinamento")
argumentos_semente, _ = parser_semente.parse_known_args()
if argumentos_semente.seed is not None:
    random.seed(argumentos_semente.seed)
    np.random.seed(argumentos_semente.seed)

# Inicializa o pygame para evitar problemas de display
pygame.init()
tamanho_grade = 7
largura_tela = tamanho_grade*100
altura_tela = tamanho_grade*100
cor_fundo = (51,51,51)
tela = pygame.display.set_mode((largura_tela,altura_tela))
pygame.display.set_caption("Q-Learning IFSULDEMINAS")

# Constantes de recompensa
RECOMPENSA_LIVRE = 0
RECOMPENSA_OBJETIVO = 10
RECOMPENSA_PAREDE = -10

# Constantes de hiperparâmetros
TAXA_APRENDIZADO = 0.1
FATOR_DESCONTO = 0.9
PROB_EXPLORACAO_INICIAL = 0.25
PROBABILIDADE_EXPLORACAO_MINIMA = 0.05
EPISODIOS_PADRAO = 1000

# Velocidade da demonstração (segundos de pausa por frame)
TEMPO_PAUSA_DEMO = 0.1


def objetivo_alcancavel(matriz_recompensa):
    """Verifica por BFS se existe caminho livre do início até o objetivo."""
    inicio = (0, 0)
    objetivo = (tamanho_grade - 1, tamanho_grade - 1)
    fila = [inicio]
    visitados = {inicio}

    while fila:
        linha, coluna = fila.pop(0)
        if (linha, coluna) == objetivo:
            return True

        vizinhos = (
            (linha - 1, coluna),
            (linha + 1, coluna),
            (linha, coluna - 1),
            (linha, coluna + 1),
        )
        for proxima_linha, proxima_coluna in vizinhos:
            proxima_posicao = (proxima_linha, proxima_coluna)
            if (
                0 <= proxima_linha < tamanho_grade
                and 0 <= proxima_coluna < tamanho_grade
                and matriz_recompensa[proxima_linha, proxima_coluna] != RECOMPENSA_PAREDE
                and proxima_posicao not in visitados
            ):
                visitados.add(proxima_posicao)
                fila.append(proxima_posicao)

    return False


def gerar_ambiente():
    """Gera paredes aleatórias e repete mapas sem caminho até o objetivo."""
    while True:
        matriz_recompensa = np.full((tamanho_grade, tamanho_grade), RECOMPENSA_LIVRE)
        cores_ambiente = [(51, 51, 51) for _ in range(tamanho_grade**2)]
        terminais = []
        posicoes_parede = [
            (i, j)
            for i in range(tamanho_grade)
            for j in range(tamanho_grade)
            if (i, j) not in ((0, 0), (tamanho_grade - 1, tamanho_grade - 1))
        ]

        for i, j in random.sample(posicoes_parede, 10):
            matriz_recompensa[i, j] = RECOMPENSA_PAREDE
            cores_ambiente[tamanho_grade * i + j] = (255, 0, 0)
            terminais.append(tamanho_grade * i + j)

        matriz_recompensa[tamanho_grade - 1, tamanho_grade - 1] = RECOMPENSA_OBJETIVO
        cores_ambiente[tamanho_grade**2 - 1] = (0, 255, 0)
        terminais.append(tamanho_grade**2 - 1)

        if objetivo_alcancavel(matriz_recompensa):
            return matriz_recompensa, cores_ambiente, terminais


# ------------------------------------------------------------
def carregar_imagem_agente(nome_arquivo="robot.png", tamanho=80):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho = os.path.join(base_dir, nome_arquivo)
        img = pygame.image.load(caminho).convert_alpha()
        img = pygame.transform.smoothscale(img, (tamanho, tamanho))
        return img
    except Exception as e:
        print(f"Imagem do agente não carregada ({nome_arquivo}): {e}. Usando círculo padrão.")
        return None

agente_img = carregar_imagem_agente()

# Inicialização do ambiente (cores, recompensas e terminais)
# Esquema de recompensas:
# - caminho livre: 0
# - objetivo (verde): +10
# - parede/obstáculo (vermelho): -10
recompensa, cores, estados_terminais = gerar_ambiente()

# Tabela Q inicial (pode ser substituída ao carregar de arquivo)
tabela_Q = np.zeros((tamanho_grade**2,4))
acoes = {"up": 0, "down": 1, "left": 2, "right": 3}
# Mapeamento inverso apenas para logs didáticos
acoes_inv = {v: k for k, v in acoes.items()}

estados = {}
k = 0
for i in range(tamanho_grade):
    for j in range(tamanho_grade):
        estados[(i,j)] = k
        k+=1
taxa_aprendizado = TAXA_APRENDIZADO
fator_desconto = FATOR_DESCONTO
posicao_atual = [0,0]
probabilidade_exploracao = PROB_EXPLORACAO_INICIAL

# ------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------
def layout():
    c = 0
    for i in range(0,largura_tela,100):
        for j in range(0,altura_tela,100):
            # Bordas
            pygame.draw.rect(tela,(255,255,255),(j,i,100,100),0)
            # Célula
            pygame.draw.rect(tela,cores[c],(j+3,i+3,94,94),0)
            c+=1

def selecionar_acao(estado_atual):
    """Seleciona ação e-greedy respeitando limites do grid.

    Retorna sempre um inteiro em {0,1,2,3} correspondente a up,down,left,right.
    """
    global posicao_atual, probabilidade_exploracao
    acoes_possiveis = []
    if np.random.uniform() <= probabilidade_exploracao:
        if posicao_atual[1] != 0:
            acoes_possiveis.append("left")
        if posicao_atual[1] != tamanho_grade-1:
            acoes_possiveis.append("right")
        if posicao_atual[0] != 0:
            acoes_possiveis.append("up")
        if posicao_atual[0] != tamanho_grade-1:
            acoes_possiveis.append("down")
        acao = acoes[acoes_possiveis[r(0,len(acoes_possiveis) - 1)]]
        return acao
    else:
        m = np.min(tabela_Q[estado_atual])
        if posicao_atual[0] != 0:
            acoes_possiveis.append(tabela_Q[estado_atual,0])
        else:
            acoes_possiveis.append(m - 100)
        if posicao_atual[0] != tamanho_grade-1:
            acoes_possiveis.append(tabela_Q[estado_atual,1])
        else:
            acoes_possiveis.append(m - 100)
        if posicao_atual[1] != 0:
            acoes_possiveis.append(tabela_Q[estado_atual,2])
        else:
            acoes_possiveis.append(m - 100)
        if posicao_atual[1] != tamanho_grade-1:
            acoes_possiveis.append(tabela_Q[estado_atual,3])
        else:
            acoes_possiveis.append(m - 100)
        # Desempate aleatório entre ações com mesmo Q-value (melhor que np.argmax simples)
        acao = random.choice([i for i,a in enumerate(acoes_possiveis) if a == max(acoes_possiveis)])
        return acao

def passo_q_learning():
    """Executa um passo de Q-Learning a partir da posicao_atual.

    Retorna (terminou, recompensa_da_transicao).
    """
    global posicao_atual, probabilidade_exploracao
    estado_atual = estados[(posicao_atual[0],posicao_atual[1])]
    acao = selecionar_acao(estado_atual)
    if acao == 0:
        posicao_atual[0] -= 1
    elif acao == 1:
        posicao_atual[0] += 1
    elif acao == 2:
        posicao_atual[1] -= 1
    elif acao == 3:
        posicao_atual[1] += 1
    novo_estado = estados[(posicao_atual[0],posicao_atual[1])]
    rwd = recompensa[posicao_atual[0],posicao_atual[1]]
    if novo_estado not in estados_terminais:
        tabela_Q[estado_atual,acao] += taxa_aprendizado*(rwd + fator_desconto*(np.max(tabela_Q[novo_estado])) - tabela_Q[estado_atual,acao])
        return False, rwd
    else:
        tabela_Q[estado_atual,acao] += taxa_aprendizado*(rwd - tabela_Q[estado_atual,acao])
        posicao_atual = [0,0]
        probabilidade_exploracao = max(PROBABILIDADE_EXPLORACAO_MINIMA, probabilidade_exploracao - 1e-3)
        return True, rwd


def treinar_q_learning(episodios=100):
    """Treina por N episódios até atingir um estado terminal em cada episódio."""
    global posicao_atual
    for ep in range(1, episodios+1):
        posicao_atual = [0,0]
        passos = 0
        terminou = False
        while not terminou:
            terminou, _ = passo_q_learning()
            passos += 1
            # Evita loops infinitos (por segurança)
            if passos > tamanho_grade * tamanho_grade * 4:
                break
        print(f"Episódio {ep:03d} concluído em {passos} passos. Probabilidade_exploracao={probabilidade_exploracao:.3f}")


def imprimir_tabela_q():
    """Imprime a tabela Q de forma didática."""
    np.set_printoptions(precision=3, suppress=True)
    print("\nTabela Q (estado x [up, down, left, right]):")
    print(tabela_Q)


def melhor_acao_permitida(estado_idx, pos):
    """Retorna a melhor ação (argmax Q) respeitando as bordas do grid."""
    valores = [-np.inf, -np.inf, -np.inf, -np.inf]
    # up
    if pos[0] != 0:
        valores[0] = tabela_Q[estado_idx, 0]
    # down
    if pos[0] != tamanho_grade-1:
        valores[1] = tabela_Q[estado_idx, 1]
    # left
    if pos[1] != 0:
        valores[2] = tabela_Q[estado_idx, 2]
    # right
    if pos[1] != tamanho_grade-1:
        valores[3] = tabela_Q[estado_idx, 3]
    # Desempate aleatório entre melhores
    max_val = max(valores)
    candidatos = [i for i, v in enumerate(valores) if v == max_val]
    return random.choice(candidatos)


def passo_guloso():
    """Executa um passo seguindo a melhor ação da tabela Q (sem atualizar Q)."""
    global posicao_atual
    estado_atual = estados[(posicao_atual[0], posicao_atual[1])]
    acao = melhor_acao_permitida(estado_atual, posicao_atual)
    if acao == 0:
        posicao_atual[0] -= 1
    elif acao == 1:
        posicao_atual[0] += 1
    elif acao == 2:
        posicao_atual[1] -= 1
    elif acao == 3:
        posicao_atual[1] += 1
    novo_estado = estados[(posicao_atual[0], posicao_atual[1])]
    rwd = recompensa[posicao_atual[0], posicao_atual[1]]
    terminou = (novo_estado in estados_terminais)
    return terminou, rwd, acao, (posicao_atual[0], posicao_atual[1])


# ------------------------------------------------------------
# Utilidades para salvar/carregar a Q-Table e o ambiente
# ------------------------------------------------------------
def salvar_q_e_ambiente(caminho="Q.txt"):
    """Salva Q-table e informações do ambiente para reuso futuro."""
    payload = {
        "Q": tabela_Q,
        "recompensa": recompensa,
        "estados_terminais": estados_terminais,
        "tamanho_grade": tamanho_grade,
    }
    with open(caminho, "wb") as f:
        pickle.dump(payload, f)


def carregar_q_e_ambiente(caminho="Q.txt"):
    """Carrega Q-table e, se disponível, o ambiente salvo.

    Retorna dict com possiveis chaves: Q, recompensa, estados_terminais, tamanho_grade
    ou None se não existir.
    """
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "rb") as f:
            obj = pickle.load(f)
        # Compatibilidade: pode ser apenas a matriz Q antiga
        if isinstance(obj, dict):
            return obj
        else:
            return {"Q": obj}
    except Exception as e:
        print(f"Falha ao carregar '{caminho}': {e}")
        return None


def recolorir_pelo_ambiente():
    """Atualiza as cores da grade com base na matriz de recompensa atual."""
    global cores
    cores = [(51,51,51) for _ in range(tamanho_grade**2)]
    for i in range(tamanho_grade):
        for j in range(tamanho_grade):
            idx = tamanho_grade*i + j
            if recompensa[i, j] < 0:  # parede
                cores[idx] = (255,0,0)
            elif recompensa[i, j] > 0:  # objetivo (ou outra recompensa positiva)
                cores[idx] = (0,255,0)


def escolher_modo():
    """Obtém o modo de execução via argumento ou pergunta interativa.

    Retorna (mode, episodios) onde mode in {"load", "train"}.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode", choices=["load", "train"], help="load: carrega Q.txt; train: treina e salva")
    parser.add_argument("--episodes", type=int, default=EPISODIOS_PADRAO, help="episódios para treinar (se --mode=train)")
    parser.add_argument("--seed", type=int, help="semente para reproduzir o ambiente e o treinamento")
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        # Em alguns ambientes (como notebooks), parse_known_args pode chamar SystemExit
        class A: pass
        args = A(); args.mode = None; args.episodes = EPISODIOS_PADRAO

    if args.mode:
        return args.mode, args.episodes

    # Interativo se não vier argumento
    resp = input("Carregar Q de 'Q.txt'? [s/N]: ").strip().lower()
    if resp in ("s", "y", "sim", "yes"):
        return "load", args.episodes
    else:
        # Pergunta opcional de episódios
        try:
            ep_in = input(f"Quantos episódios para treinar? [{EPISODIOS_PADRAO}]: ").strip()
            n_ep = int(ep_in) if ep_in else EPISODIOS_PADRAO
        except ValueError:
            n_ep = EPISODIOS_PADRAO
        return "train", n_ep


# ------------------------------------------------------------
# Fase 1: Treinamento da Q-Table (100 episódios)
# ------------------------------------------------------------
modo, n_episodios = escolher_modo()

if modo == "load":
    print("Modo: carregar Q e ambiente de 'Q.txt'")
    dados = carregar_q_e_ambiente("Q.txt")
    if dados is None or "Q" not in dados:
        print("Arquivo não encontrado ou inválido. Iniciando treinamento novo.")
        modo = "train"
    else:
        # Verifica compatibilidade de tamanho
        q_loaded = dados["Q"]
        if q_loaded.shape != tabela_Q.shape:
            print("Q carregada com dimensão diferente do grid atual. Iniciando treinamento novo.")
            modo = "train"
        else:
            tabela_Q = q_loaded
            # Se houver ambiente salvo, aplica
            if "recompensa" in dados and isinstance(dados["recompensa"], np.ndarray):
                # Garante que o tamanho bate
                if dados.get("tamanho_grade", tamanho_grade) == tamanho_grade and dados["recompensa"].shape == recompensa.shape:
                    recompensa = dados["recompensa"]
                    # Reconstroi terminais (ou usa do payload)
                    if "estados_terminais" in dados and isinstance(dados["estados_terminais"], list):
                        estados_terminais = dados["estados_terminais"]
                    else:
                        estados_terminais = []
                        for i in range(tamanho_grade):
                            for j in range(tamanho_grade):
                                if recompensa[i, j] != 0:
                                    estados_terminais.append(tamanho_grade*i + j)
                    recolorir_pelo_ambiente()
                else:
                    print("Ambiente salvo incompatível com o tamanho atual. Mantendo ambiente atual.")
            # Sem exploração durante a demonstração
            probabilidade_exploracao = 0.0
else:
    print(f"Iniciando treinamento por {n_episodios} episódios para formar a Tabela Q...")
    treinar_q_learning(episodios=n_episodios)
    # Após treinar, imprime e salva a tabela Q + ambiente
    imprimir_tabela_q()
    salvar_q_e_ambiente("Q.txt")
    # Demonstração com política gulosa
    probabilidade_exploracao = 0.0

# ------------------------------------------------------------
# Fase 2: Demonstração guiada pelo melhor caminho da Tabela Q
# - probabilidade_exploracao = 0 para seguir sempre a melhor ação
# - imprime penalidades, recompensas e acumulado
# ------------------------------------------------------------
probabilidade_exploracao = 0.0  # exploração desligada para a demonstração

print("\nIniciando demonstração do percurso seguindo a Tabela Q (política gulosa)...")
posicao_atual = [0,0]
recompensa_acumulada = 0.0
passos_demo = 0
limite_passos_demo = tamanho_grade * tamanho_grade * 4

executar = True
modo_demo = True

while executar:
    tela.fill(cor_fundo)
    layout()
    if agente_img:
        centro = (posicao_atual[1]*100 + 50, posicao_atual[0]*100 + 50)
        rect = agente_img.get_rect(center=centro)
        tela.blit(agente_img, rect)
    else:
        pygame.draw.circle(tela,(25,129,230),(posicao_atual[1]*100 + 50,posicao_atual[0]*100 + 50),30,0)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            executar = False
    pygame.display.flip()

    if modo_demo:
        terminou, rwd, acao, pos = passo_guloso()
        passos_demo += 1
        recompensa_acumulada += rwd
        estado_idx = estados[pos]
        # Classificação didática com base no valor da recompensa (esquema anterior)
        if rwd == RECOMPENSA_PAREDE:
            tipo = f"Parede ({RECOMPENSA_PAREDE})"
        elif rwd == RECOMPENSA_OBJETIVO:
            tipo = f"Objetivo (+{RECOMPENSA_OBJETIVO})"
        elif rwd == RECOMPENSA_LIVRE:
            tipo = f"Livre (+{RECOMPENSA_LIVRE})"
        else:
            tipo = f"Recompensa {rwd:+.0f}"
        print(f"Passo {passos_demo:03d} | Estado={estado_idx} Pos={pos} | Ação={acoes_inv[acao]} | r={rwd:+.0f} ({tipo}) | Acumulado={recompensa_acumulada:+.0f}")

        if terminou or passos_demo >= limite_passos_demo:
            if terminou:
                print("\nDemonstração concluída: estado terminal alcançado.")
            else:
                print("\nDemonstração encerrada por limite de passos (possível loop).")
            modo_demo = False
    else:
        # Após finalizar a demonstração, aguardamos a janela ser fechada
        pass

    sleep(TEMPO_PAUSA_DEMO)

pygame.quit()

print(f"Probabilidade de exploração final: {probabilidade_exploracao}")
# Salva Q + ambiente apenas se treinamos nesta execução
if modo == "train":
    salvar_q_e_ambiente("Q.txt")
