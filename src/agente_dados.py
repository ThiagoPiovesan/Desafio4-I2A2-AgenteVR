# ============================================================================
# Autor: Thiago Piovesan
# Descrição: Agente responsável por carregar e limpar os dados
# ============================================================================
# Libs importation:
import os
import ast
import pandas as pd
from typing import List, Dict

from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent

# import config
# from src.agente_dados_tools import *
# ============================================================================
# --- 1. Gerenciamento de Dados ---
# Usaremos um dicionário simples para armazenar os DataFrames em memória.
# O agente irá operar nos nomes (chaves) dos DataFrames, não nos objetos em si.
DATA_STORE = {}

# --- 2. Criação das Ferramentas (Tools) ---
# O agente usará estas funções para interagir com os dados.
# As docstrings são MUITO importantes, pois o LLM as lê para entender o que cada ferramenta faz.

@tool
def clean_data_store() -> str:
    """
    Limpa o DATA_STORE, removendo todos os DataFrames armazenados.
    Útil para liberar memória entre diferentes etapas do processamento.
    """
    global DATA_STORE
    
    # Except vr_unificado, que deve ser preservado
    if 'vr_unificado' in DATA_STORE:
        df_vr_unificado = DATA_STORE['vr_unificado']
        DATA_STORE = {'vr_unificado': df_vr_unificado}
    else:
        DATA_STORE = {}
        
    return DATA_STORE

@tool
def ler_planilha_excel(caminho_arquivo: str) -> str:
    """
    Lê um arquivo Excel (.xlsx) e o carrega como um DataFrame do Pandas.
    O DataFrame é armazenado em um 'data store' em memória.
    Retorna uma string com o nome do DataFrame e um resumo dos dados.
    """
    try:
        if "\n" in caminho_arquivo:
            df_name = os.path.basename(caminho_arquivo.strip().split("\n")[0])
            df = pd.read_excel(caminho_arquivo.strip().split("\n")[0])
        else:
            df_name = os.path.basename(caminho_arquivo.strip())
            df = pd.read_excel(caminho_arquivo.strip())
        
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
        return DATA_STORE
    except Exception as e:
        print(f"Erro ao ler o arquivo {caminho_arquivo}: {e}")
        return DATA_STORE
    
@tool
def renomear_colunas(nome_df: str) -> str:
    """
    nome_df: str -> Nome do DataFrame no DATA_STORE.
    Renomeia as colunas de um DataFrame especificado.
    """
    
    print(f"-----------------------------------------------------------------")
    print(f"Renomear colunas chamado para o DataFrame: {nome_df}")
    print(f"Estado atual do DATA_STORE: {list(DATA_STORE.keys())}")
    
    if type(nome_df) is str:
        aux_var = ast.literal_eval(nome_df) if type(nome_df) is str and nome_df.startswith("{") else None
        if aux_var is not None:
            nome_df = str(list(aux_var.keys())[0]).strip()
        
        # remove quebras de linha se houver    
        if "\n" in nome_df:
            nome_df = str(nome_df.split("\n")[0])
        
        # remove aspas se houver
        nome_df = nome_df.replace("'", "").replace('"', '').strip()
        
        print(f"Nome do DataFrame após avaliação: {nome_df}")
        
        if nome_df not in DATA_STORE:
            if 'nome_df' in nome_df:
                nome_df = 'nome_df'
            else:
                print(f"Erro: DataFrame '{nome_df}' não encontrado.")

        df = DATA_STORE[nome_df]
    else:
        # convert nome_df que é um DataFrame em si
        df = pd.DataFrame(nome_df)

    try:
        colunas_atuais = df.columns.tolist()
        mapa_colunas = {}
        for col in colunas_atuais:
            col_lower = col.lower()
            col_no_accents = ''.join((c for c in col_lower if c.isalnum() or c.isspace())).replace(" ", "_")
            mapa_colunas[col] = col_no_accents
        
        df.rename(columns=mapa_colunas, inplace=True)
        
        print("-----------------------------------------------------------------")
        print(f"Renomeando colunas no DataFrame '{nome_df}'")
        print(f"Colunas antigas: {colunas_atuais}")
        print(f"Colunas novas: {df.columns.tolist()}")
        
        DATA_STORE[nome_df] = df
        return DATA_STORE
    except Exception as e:
        print(f"Erro ao renomear colunas em '{nome_df}': {e}")
        return DATA_STORE

@tool
def unificar_dataframes() -> str:
    """
    Concatena (une) uma lista de DataFrames em um único DataFrame final.
    Use esta ferramenta depois que todos os DataFrames tiverem suas colunas padronizadas.
    """
    print("-----------------------------------------------------------------")
    lista_nomes_df = [nome for nome in DATA_STORE.keys()]
    print(f"Unificando DataFrames: {lista_nomes_df}")
    dataframes_para_unir = []
    for nome_df in lista_nomes_df:
        if nome_df not in DATA_STORE:
            return f"Erro: DataFrame '{nome_df}' não encontrado para unificação."
        dataframes_para_unir.append(DATA_STORE[nome_df])
    
    try:
        df_unificado = pd.concat(dataframes_para_unir, ignore_index=True)
        DATA_STORE['vr_unificado'] = df_unificado
        
        return DATA_STORE
    except Exception as e:
        print(f"Erro ao unificar DataFrames: {e}")
        return DATA_STORE

# ============================================================================
def criar_agente_dados(llm, verbose: bool = False) -> AgentExecutor:
    modelo: str = llm.model_name if hasattr(llm, "model_name") else llm.model
    print(f"Usando modelo: {modelo}")
    
    # Carregar prompt específico para o modelo -> utils/prompt_agente_dados.txt
    # with open("utils/prompt_agente_dados.txt", "r", encoding="utf-8") as f:
    #     prompt_template = f.read()
    prompt_template = """
        Você é um assistente especialista em engenharia de dados. Seu objetivo é receber uma lista de arquivos Excel,
        analisá-los, padronizá-los e unificá-los em um único conjunto de dados limpo.
        
        Você tem acesso às seguintes ferramentas, onde cada uma delas é descrita detalhadamente:
        {tools}
        Os retornos das ferramentas são sempre o estado atualizado do DATA_STORE, um dicionário que armazena os DataFrames carregados.

        Para atingir seu objetivo, você deve seguir estes passos, carregando e processando cada arquivo da lista:
        1. Se o DATA_STORE estiver cheio ou com muitos dados, use a ferramenta 'clean_data_store' para limpá-lo.
        2. Itere sobre cada caminho da lista recebida. Para cada item, chame `ler_planilha_excel` usando o caminho EXATAMENTE como fornecido.
        3. Usar a ferramenta `renomear_colunas` para ajustar os nomes das colunas de cada DataFrame para que correspondam ao esquema final.
        4. Após padronizar TODOS os DataFrames, usar a ferramenta `unificar_dataframes` para criar um único DataFrame mestre chamado 'vr_unificado'.
        
        Durante o processo, você deve pensar cuidadosamente sobre cada passo, decidindo qual ferramenta usar e com quais argumentos.
        Sempre que precisar de informações sobre o estado atual dos dados, consulte o DATA_STORE.
        
        ---
        Thought: você deve sempre pensar sobre o que fazer
        Action: a ação a ser tomada, deve ser uma das [{tool_names}]
        Action Input: a entrada para a ação
        Observation: o resultado da ação
        ... (este Thought/Action/Action Input/Observation pode se repetir N vezes, até todos os arquivos serem processados)

        Exemplo de formato correto:
        Thought: Eu preciso ler o primeiro arquivo da lista.
        Action: ler_planilha_excel
        Action Input: data/input/FÉRIAS.xlsx
        
        Thought: Eu terminei a tarefa.
        Final Answer: A resposta final para o usuário, resumindo o que foi feito.
        
        **IMPORTANTE:** Quando a tarefa estiver concluída, você DEVE usar a tag "Final Answer:". Não escreva um resumo final sem ela.

        Input: Você recebeu a seguinte lista de arquivos:
        {input}
        Você deve processar **cada item da lista exatamente como está escrito**, sem modificar ou inventar nomes, e sem adicionar ou remover arquivos.

        Comece!

        {agent_scratchpad}
    """

    # print(f"Prompt carregado:\n{prompt_template}")
    prompt = PromptTemplate.from_template(prompt_template)

    tools = [clean_data_store, ler_planilha_excel, renomear_colunas, unificar_dataframes]
    tool_names = [tool.name for tool in tools]

    agente = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    agente_executor = AgentExecutor(agent=agente, tools=tools, max_iterations=20, verbose=verbose, handle_parsing_errors=True)

    return agente_executor, DATA_STORE