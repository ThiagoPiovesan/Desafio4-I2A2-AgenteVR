# Desafio 4 - Automação de Cálculo de Vale Refeição (VR)

## Visão Geral

Este projeto automatiza o processo de cálculo do benefício de Vale Refeição (VR) para os colaboradores de uma empresa. Ele consolida dados de diversas fontes (planilhas Excel), aplica um conjunto complexo de regras de negócio e gera um relatório final pronto para ser enviado à operadora do benefício.

O núcleo do projeto utiliza um agente de IA (através da biblioteca LangChain e da API do Google Gemini) para interpretar as regras de negócio e executar os cálculos de forma autônoma, demonstrando uma abordagem moderna para resolver problemas de lógica de negócio complexa.

## Fluxo do Processo

O sistema segue um pipeline de dados bem definido:

1.  **Carregamento de Dados (`data_loader.py`):** O processo inicia carregando múltiplas planilhas Excel a partir do diretório `data/input/`. Cada planilha representa uma faceta dos dados dos colaboradores (ativos, admissões, férias, desligamentos, etc.). Os nomes das colunas são padronizados nesta etapa.

2.  **Processamento e Limpeza (`data_processor.py`):**
    *   **Consolidação:** As bases de colaboradores `ativos` e `admissões` são unificadas.
    *   **Aplicação de Exclusões:** Colaboradores que não são elegíveis ao benefício são removidos da base principal. Isso inclui estagiários, aprendizes, diretores, funcionários em afastamento ou alocados no exterior.

3.  **Motor de Cálculo (`calculation_engine.py`):**
    *   Este é o componente central que orquestra a lógica de negócio.
    *   Um **agente de IA** é inicializado com acesso a um ambiente Python (REPL) e aos dados já processados.
    *   O agente recebe um prompt detalhado (`llm_prompt.txt`) contendo todas as regras de negócio, como:
        *   Cálculo de dias úteis com base no sindicato.
        *   Desconto de dias de férias.
        *   Regras de pagamento proporcional para recém-admitidos.
        *   Regras de corte ou pagamento proporcional para desligados.
        *   Cálculo do valor total do benefício com base no estado (UF) do sindicato.
    *   O agente executa o código Python passo a passo para aplicar essas regras e produz um DataFrame final com os resultados.

## Estrutura do Projeto

```
.
├── data/
│   ├── input/         # Contém as planilhas de dados de entrada
│   └── output/        # Onde o relatório final é salvo
├── src/
│   ├── __init__.py
│   ├── config.py      # Configurações de caminhos e regras de negócio
│   ├── data_loader.py # Módulo para carregar e limpar dados
│   ├── data_processor.py # Módulo para consolidar e filtrar dados
│   └── calculation_engine.py # Orquestra o agente de IA para os cálculos
├── .env               # Arquivo para armazenar a GOOGLE_API_KEY (não versionado)
├── .gitignore
├── llm_prompt.txt     # O prompt com as instruções para o agente de IA
├── main.py            # Ponto de entrada da aplicação
├── pyproject.toml     # Definições do projeto e dependências
└── README.md          # Este arquivo
```

## Como Configurar e Executar

### Pré-requisitos

*   Python 3.13 ou superior
*   Poetry (para gerenciamento de dependências)

### Passos

1.  **Clonar o Repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd <nome-do-repositorio>
    ```

2.  **Instalar Dependências:**
    Use o Poetry ou UV para criar um ambiente virtual e instalar as bibliotecas listadas no `pyproject.toml`.
    ```bash
    poetry install
    uv sync
    ```

3.  **Configurar a Chave de API:**
    *   Crie um arquivo chamado `.env` na raiz do projeto.
    *   Dentro deste arquivo, adicione sua chave da API do Google Gemini:
        ```
        GOOGLE_API_KEY="SUA_CHAVE_DE_API_AQUI" ou OPENAI
        ```

4.  **Adicionar os Dados de Entrada:**
    *   Certifique-se de que todas as planilhas Excel necessárias estejam presentes no diretório `data/input/`.

5.  **Executar o Projeto:**
    Execute o script principal para iniciar todo o processo.
    ```bash
    poetry run python main.py
    uv run main.py
    ```
    Ou, ativando o ambiente virtual primeiro:
    ```bash
    poetry shell
    uv venv
    python main.py
    ```

O processo pode levar alguns minutos, pois envolve chamadas de API para o modelo de linguagem. Ao final, o relatório `VR_compra_calculado.xlsx` será gerado no diretório `data/output/`.
