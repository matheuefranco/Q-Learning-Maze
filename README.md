# Q-Learning Gridworld (IFSULDEMINAS)

Projeto didático de Aprendizagem por Reforço com Q-Learning em um grid 2D (7x7) usando Pygame para visualização. O agente aprende uma política que o leva do início (canto superior esquerdo) até o objetivo (canto inferior direito), desviando de paredes.

- Recompensas (configuráveis no código):
  - Caminho livre: `0`
  - Objetivo: `+10`
  - Parede/obstáculo: `-10`
- A Q-Table e o ambiente (maze) podem ser salvos e carregados de `Q.txt`.
- Visualização em tempo real; opção de usar uma imagem de agente (robot.png) em vez do círculo.

## Pré-requisitos
- Windows
- Python 3.11 ou 3.12 instalado

## Instalação (Windows PowerShell)

Abra o PowerShell na pasta do projeto (`Q-Learning`). Em seguida:

### 1) Criar e ativar um ambiente virtual (venv)
Use o Python Launcher do Windows para escolher a versão:

```powershell
# Com Python 3.11
py -3.11 -m venv .venv

# OU com Python 3.12
py -3.12 -m venv .venv

# Ativar o venv
.\.venv\Scripts\Activate

# (opcional) Atualizar o pip
python -m pip install --upgrade pip
```

Dica: Se o PowerShell bloquear a execução do script de ativação, rode temporariamente:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2) Instalar dependências

```powershell
pip install -r requirements.txt
```

## Como executar

O script principal é `ReforceLearning.py`. Existem dois modos: `train` (treinar e salvar) e `load` (carregar e demonstrar).

### Treinar (gera a Q-Table e salva `Q.txt`)
```powershell
python .\ReforceLearning.py --mode train --episodes 100
```
- `--episodes` é opcional; se omitido, usa o padrão definido no código.
- Ao final do treino, a Q-Table é impressa e `Q.txt` é gravado com a tabela e o ambiente.

### Carregar e demonstrar (usa `Q.txt`)
```powershell
python .\ReforceLearning.py --mode load
```
- Se `Q.txt` for incompatível ou não existir, o programa cai automaticamente para o modo de treino.

## Controles e Visualização
- Uma janela do Pygame abre mostrando o grid:
  - Células vermelhas: paredes
  - Célula verde: objetivo
  - Cinza: caminho livre
  - Agente: círculo azul ou uma imagem (`robot.png`) se presente
- Feche a janela para encerrar.
- Durante a demonstração, o terminal mostra passo a passo: estado, ação, recompensa e acumulado.

## Personalizações rápidas
Os principais parâmetros estão no topo do arquivo `ReforceLearning.py`:

- Recompensas:
  - `RECOMPENSA_LIVRE`
  - `RECOMPENSA_OBJETIVO`
  - `RECOMPENSA_PAREDE`
- Hiperparâmetros:
  - `TAXA_APRENDIZADO`
  - `FATOR_DESCONTO`
  - `PROB_EXPLORACAO_INICIAL`
  - `EPISODIOS_PADRAO`
- Velocidade da demonstração:
  - `TEMPO_PAUSA_DEMO` (em segundos por frame)
- Imagem do agente (opcional):
  - Coloque `robot.png` na mesma pasta do script. O código tenta carregar e usar automaticamente.

## Estrutura do projeto
- `ReforceLearning.py`: código principal (ambiente, Q-Learning, visualização, salvar/carregar)
- `requirements.txt`: dependências Python
- `Q.txt`: arquivo binário gerado após o treino (Q-Table + ambiente)

## Visão geral do algoritmo
- Q-Learning tabular com política ε-greedy (exploração/exploração):
  - Atualização: `Q(s,a) ← Q(s,a) + α [ r + γ max_a' Q(s',a') − Q(s,a) ]`
  - `α`: taxa de aprendizagem; `γ`: fator de desconto; `r`: recompensa; `s'`: próximo estado
- Cada episódio inicia no estado inicial e termina ao atingir um estado terminal (parede/objetivo).

## Dicas
- Como o labirinto é gerado aleatoriamente, use `--mode load` para reproduzir a mesma política e ambiente salvos em `Q.txt`.
- Se quiser deixar o ambiente reproduzível, você pode fixar uma semente com `random.seed(...)` e `np.random.seed(...)` no início do script.

## Problemas comuns
- "pygame" não abre a janela: verifique se está rodando localmente (não por SSH) e se o Pygame foi instalado corretamente.
- Erro de ativação do venv no PowerShell: use o `Set-ExecutionPolicy` temporário conforme acima.
- Falha ao carregar `Q.txt`: o código retorna para o modo de treinamento e gera um novo arquivo.

---

Qualquer dúvida ou se quiser estender (por exemplo, setas da política no grid, modo cabeça-de-serpente, ou DQN), abra uma issue ou peça ajuda diretamente.