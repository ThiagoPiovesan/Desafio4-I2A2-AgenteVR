# Desafio 4: Agentes Autônomos para Cálculo de Vale Refeição (VR)

## Visão Geral

Este projeto utiliza agentes de IA para automatizar o complexo processo de cálculo do benefício de Vale Refeição (VR) para os colaboradores de uma empresa. A solução consolida dados de múltiplas planilhas, aplica um conjunto de regras de negócio e gera um relatório final unificado.

O núcleo do projeto é baseado em agentes autônomos que utilizam a API do Google Gemini para interpretar as regras de negócio e executar os cálculos necessários, demonstrando uma abordagem moderna para resolver desafios de lógica de negócio.

## Arquitetura dos Agentes

O sistema é orquestrado pelo `main.py` e opera com dois agentes principais:

1.  **Agente de Dados (`src/agente_dados.py`):**
    *   **Responsabilidade:** Localizar, carregar e consolidar as diversas planilhas de dados (colaboradores ativos, admissões, férias, etc.) localizadas em `data/input/`.
    *   **Ferramentas (`src/agente_dados.py`):** Utiliza um conjunto de ferramentas para ler e processar os arquivos, unificando-os em um único DataFrame para a próxima etapa.
    *   **Prompt (`utils/prompt_agente_dados.txt`):** Segue instruções específicas para realizar a carga e o pré-processamento dos dados.

2.  **Agente de Cálculo (`src/agente_calculo.py`):**
    *   **Responsabilidade:** Aplicar as regras de negócio complexas sobre os dados consolidados.
    *   **Lógica:** Interpreta as regras detalhadas no prompt principal para realizar cálculos de dias úteis, descontos de férias, proporcionalidade para admissões e desligamentos, e o valor final do benefício com base na localidade (UF).
    *   **Prompt (`utils/llm_prompt.txt`):** Contém o detalhamento completo de todas as regras de negócio que o agente deve seguir para executar os cálculos corretamente.

## Estrutura do Projeto

```
.
├── data/
│   ├── input/                     # Contém as planilhas de dados de entrada
│   └── output/                    # Onde o relatório final (VR MENSAL 05.2025.csv) é salvo
├── src/
│   ├── agente_calculo.py          # Agente que executa as regras de negócio e os cálculos
│   ├── agente_dados.py            # Agente responsável por carregar e preparar os dados
│   └── config.py                  # Configurações gerais e caminhos
├── utils/
│   ├── llm_prompt.txt             # Prompt com as regras de negócio para o agente de cálculo
│   └── prompt_agente_dados.txt    # Prompt de instruções para o agente de dados
├── .env                           # Arquivo para armazenar a GOOGLE_API_KEY (não versionado)
├── main.py                        # Ponto de entrada que orquestra os agentes
├── pyproject.toml                 # Definições do projeto e dependências
└── README.md                      # Este arquivo
```

## Como Configurar e Executar

### Pré-requisitos

*   Python 3.9+
*   Poetry (ou outro gerenciador de ambientes como UV)

### Passos

1.  **Clonar o Repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd Desafio4
    ```

2.  **Instalar Dependências:**
    Use o Poetry para criar um ambiente virtual e instalar as bibliotecas necessárias.
    ```bash
    poetry install
    ```

3.  **Configurar a Chave de API:**
    *   Crie um arquivo chamado `.env` na raiz do projeto.
    *   Adicione sua chave da API do Google Gemini neste arquivo:
        ```
        GOOGLE_API_KEY="SUA_CHAVE_DE_API_AQUI"
        ```

4.  **Adicionar os Dados de Entrada:**
    *   Coloque todas as planilhas Excel necessárias no diretório `data/input/`.

5.  **Executar o Projeto:**
    Ative o ambiente virtual e execute o script principal.
    ```bash
    poetry run python main.py
    ```
    Como alternativa:
    ```bash
    poetry shell
    python main.py
    ```

O processo pode levar alguns minutos para ser concluído. Ao final, o relatório `VR MENSAL 05.2025.csv` será gerado no diretório `data/output/`.