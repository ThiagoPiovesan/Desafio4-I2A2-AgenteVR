import os
import pandas as pd
from dotenv import load_dotenv
from typing import Dict

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# (Você pode manter os imports e o DATA_STORE do script do Agente 1)
# Supondo que o DATA_STORE já existe e será usado para passar dados entre os agentes.
# Se este for um script separado, você precisará recriar o DATA_STORE.
DATA_STORE = {}

# --- 2. Ferramentas do Agente "Analista de Folha de Pagamento" ---
# @tool
# def obter_regras_de_negocio() -> Dict:
#     """
#     Retorna um dicionário com valores e regras de negócio fixas para o cálculo do VR.
#     Use esta ferramenta para obter constantes como valor diário do VR, percentual de desconto, etc.
#     """
#     # Em um cenário real, isso poderia vir de um banco de dados ou arquivo de configuração.
#     regras = {
#         "valor_dia_vr": 28.50,
#         "desconto_fixo_folha": 50.00,
#         "teto_maximo_vr": 800.00
#     }
#     return regras

@tool
def ler_planilha_excel(caminho_arquivo: str) -> str:
    """
    Lê um arquivo Excel (.xlsx) e o carrega como um DataFrame do Pandas.
    O DataFrame é armazenado em um 'data store' em memória.
    Retorna uma string com o nome do DataFrame e um resumo dos dados.
    """
    try:
        if "\n" in caminho_arquivo:
            filename = caminho_arquivo.strip().split("\n")[0]
            filename = filename.replace('"', '').replace("'", '').strip()
            
            df_name = os.path.basename(filename)
            df = pd.read_excel(filename)
        else:
            filename = caminho_arquivo.strip()
            filename = filename.replace('"', '').replace("'", '').strip()

            df_name = os.path.basename(filename)
            df = pd.read_excel(filename)

        for i in range(1, len(df.columns) + 1):
            if f'Unnamed: {i}' in df.columns:
                df.rename(columns={f'Unnamed: {i}': f'observacoes_{i}'}, inplace=True)
                # df.drop(columns=[f'Unnamed: {i}'], inplace=True)
        
        DATA_STORE[df_name] = df
        
        # Retorna um resumo para o LLM, não o DataFrame inteiro
        resumo = f"DataFrame '{df_name}' carregado com sucesso.\n"
        resumo += f"Colunas: {df.columns.tolist()}\n"
        resumo += f"Primeiras 5 linhas:\n{df.head().to_markdown()}"
        # print(resumo)
        
        print(f"DATA_STORE: {list(DATA_STORE.keys())}")
        return DATA_STORE
    except Exception as e:
        print(f"Erro ao ler o arquivo {caminho_arquivo}: {e}")
        return DATA_STORE

@tool
def executar_codigo_pandas(codigo: str) -> str:
    """
    codigo: str -> Código Python/Pandas a ser executado.
    
    Executa uma string de código Python/Pandas em um DataFrame específico.
    Use esta ferramenta para fazer todos os cálculos: criar novas colunas, aplicar fórmulas, etc.
    O DataFrame está disponível dentro do código com a variável 'df'.
    Exemplo de código: "df['nova_coluna'] = df['coluna_existente'] * 2"
    """
    
    nome_df = "vr_unificado"  # Nome fixo do DataFrame que o agente irá manipular

    if nome_df not in DATA_STORE:
        return f"Erro: DataFrame '{nome_df}' não encontrado."
    
    try:
        df = DATA_STORE[nome_df]
        # O 'exec' executa o código. Passamos um dicionário local para que ele tenha acesso ao 'df'.
        local_scope = {'df': df, 'pd': pd}
        exec(codigo, {}, local_scope)
        # Atualiza o DataFrame no DATA_STORE com as modificações
        DATA_STORE[nome_df] = local_scope['df']
        
        # Retorna um resumo para o LLM confirmar que a operação funcionou
        return f"Código executado com sucesso em '{nome_df}'. Primeiras 5 linhas do resultado:\n{DATA_STORE[nome_df].head().to_markdown()}"
    except Exception as e:
        return f"Erro ao executar o código em '{nome_df}': {e}"

@tool
def salvar_dataframe_em_excel(nome_df: str, caminho_arquivo: str) -> str:
    """
    Salva o DataFrame final em um arquivo Excel (.xlsx).
    Use esta ferramenta como a ETAPA FINAL para gerar o output do cálculo.
    """
    if nome_df not in DATA_STORE:
        return f"Erro: DataFrame '{nome_df}' não encontrado."
    try:
        df = DATA_STORE[nome_df]
        df.to_excel(caminho_arquivo, index=False)
        return f"DataFrame '{nome_df}' salvo com sucesso em '{caminho_arquivo}'."
    except Exception as e:
        return f"Erro ao salvar o arquivo: {e}"


# --- 3. Criação do Agente "Analista de Folha de Pagamento" ---

def criar_agente_analista(llm, data_store=DATA_STORE, verbose: bool = False) -> AgentExecutor:
    """
        Cria e retorna um agente especializado em análise de folha de pagamento.
        Este agente usará as ferramentas definidas acima para calcular o VR.
    """
    global DATA_STORE
    DATA_STORE["vr_unificado"] = data_store

    tools = [
        ler_planilha_excel,
        executar_codigo_pandas,
        salvar_dataframe_em_excel
    ]
    
    print(f'=============================================')
    print(f' DATA_STORE: {list(DATA_STORE.keys())}')
    print(f' DATA_STORE: {DATA_STORE["vr_unificado"].head()}')

    modelo: str = llm.model_name if hasattr(llm, "model_name") else llm.model
    print(f"Usando modelo: {modelo}")
    
    prompt_template = """
    
    Você é um especialista em análise de folha de pagamento. Sua tarefa é calcular o valor final do Vale Refeição (VR)
    para cada funcionário no DataFrame 'vr_unificado', seguindo as regras de negócio fornecidas.

    ---
    ## Regras de Negócio a Serem Aplicadas

    Você deve seguir ESTAS regras na ordem especificada.

    ### Passo 1: Base de Colaboradores Elegíveis
    A base de colaboradores elegíveis já foi pré-processada e está disponível no dataframe `vr_unificado`. 
    Mas algumas informações adicionais podem ser necessárias de outras tabelas, que você pode carregar conforme a lista recebida no {input}.
    
    1. Itere sobre cada caminho da lista recebida. Para cada item, chame `ler_planilha_excel` usando o caminho EXATAMENTE como fornecido.
    2. Após carregar todas as planilhas, você terá acesso a várias tabelas no `DATA_STORE`.

    Sua tarefa começa no Passo 2, utilizando o dataframe `vr_unificado` como ponto de partida, junto com as planilhas carregadas no passo 1.

    ### Passo 2: Calcular os Dias a Pagar para Cada Colaborador
    1.  **Dias Úteis Padrão:** Para cada colaborador, encontre seu sindicato na coluna `Sindicato`. Use a tabela `Dias Úteis por Sindicato` para determinar a quantidade de dias úteis do mês para ele. **Atenção:** Os nomes dos sindicatos podem não ser idênticos. Faça uma correspondência inteligente (ex: "SINDPD SP" na base de ativos deve corresponder a "SINDPD SP - SIND.TRAB.EM PROC DADOS..." na base de dias úteis).
    2.  **Subtrair Férias:** Se o colaborador estiver na tabela `Férias`, subtraia os `DIAS DE FÉRIAS` dos dias úteis padrão. O resultado nunca pode ser menor que zero.
    3.  **Aplicar Regra de Desligamento (Corte):** Se o colaborador estiver na tabela `Desligados` E o `COMUNICADO DE DESLIGAMENTO` for "OK" E o dia da `DATA DEMISSÃO` for **menor ou igual a 15**, então os dias a pagar para este colaborador são **ZERO**.
    4.  **Aplicar Regra de Proporcionalidade (Admissão):** Para colaboradores admitidos no período de cálculo (16/04/2025 a 15/05/2025), os dias a pagar devem ser o número de dias úteis entre a data de admissão e 15/05/2025. Ignore o cálculo de férias para eles.
    5.  **Aplicar Regra de Proporcionalidade (Desligamento):** Para colaboradores desligados APÓS o dia 15, os dias a pagar devem ser o número de dias úteis entre 16/04/2025 e a data de demissão.

    ### Passo 3: Calcular o Valor Final do VR
    1.  **Encontrar Valor Diário:** Para cada colaborador, extraia a sigla do estado (UF) do nome do seu `Sindicato` (ex: "SINDPPD RS" -> "RS"). Use essa UF para encontrar o `VALOR` diário na tabela `Valor do VR por Sindicato`.
    2.  **Calcular Valor Total:** `Valor Total VR` = (Dias a Pagar Finais) * (Valor Diário do VR).
    3.  **Dividir Custos:**
        *   `Custo Empresa` = `Valor Total VR` * 0.80 (80%)
        *   `Desconto Profissional` = `Valor Total VR` * 0.20 (20%)
    ---
    
    Seu processo deve ser:
    1.  Com base nas regras fornecidas acima e no dataframe que você obteve, escreva e execute código Pandas usando a ferramenta `executar_codigo_pandas`. Crie as colunas de cálculo passo a passo (ex: 'vr_bruto', 'descontos', 'vr_liquido').
    2.  Ao final de todos os cálculos, use a ferramenta `salvar_dataframe_em_excel` para salvar o DataFrame modificado em um arquivo chamado 'VR MENSAL 05.2025.xlsx'.

    As regras de negócio específicas para este cálculo estão no input abaixo. Interprete-as para construir sua lógica de cálculo.

    Você tem acesso às seguintes ferramentas:
    {tools}
    
    Thought: você deve sempre pensar sobre o que fazer
    Action: a ação a ser tomada, deve ser uma das [{tool_names}]
    Action Input: a entrada para a ação
    Observation: o resultado da ação
    ... (este Thought/Action/Action Input/Observation pode se repetir N vezes)
    Thought: Eu terminei a tarefa.
    Final Answer: A resposta final para o usuário, resumindo o que foi feito.
    
    **IMPORTANTE:** Quando a tarefa estiver concluída, você DEVE usar a tag "Final Answer:". Não escreva um resumo final sem ela.

    ## Tarefa Final

    Após aplicar todas as regras, sua tarefa é salvar essas informações no arquivo 'VR MENSAL 05.2025.xlsx'.

    Exemplo de formato correto:
    Thought: Eu preciso realizar o cálculo do VR.
    Action: executar_codigo_pandas
    Action Input: {{ "nome_df": "vr_unificado", "codigo": "df['vr_bruto'] = df['dias_trabalhados'] * 28.50 # Exemplo de código" }}

    Use o formato de resposta com Thought/Action/Action Input.

    Comece!

    Input: Você recebeu a seguinte lista de arquivos:
    {input}
    Você deve processar **cada item da lista exatamente como está escrito**, sem modificar ou inventar nomes.
    
    {agent_scratchpad}
    """
    
    tool_names = [tool.name for tool in tools]

    prompt = PromptTemplate.from_template(prompt_template)
    agente = create_react_agent(llm, tools, prompt)
    agente_executor = AgentExecutor(agent=agente, tools=tools, max_iterations=30, verbose=verbose, handle_parsing_errors=True)
    
    return agente_executor
