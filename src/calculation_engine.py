# ------------------------------------------------------------
# Code developed by: Thiago Piovesan
# Created on: 2025-08-17
# ------------------------------------------------------------
# Libs:
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_experimental.tools import PythonAstREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor, create_react_agent

def run_calculations(processed_dfs: dict, llm_prompt: str) -> pd.DataFrame:
    """
    Executa os cálculos de negócio usando um agente autônomo.

    Args:
        processed_dfs: Dicionário com os dataframes processados.
        llm_prompt: O prompt detalhado com as regras de negócio.

    Returns:
        O dataframe final com os resultados.
    """
    print("--- Iniciando agente autônomo para cálculos ---")

    # 1. Carregar variáveis de ambiente (GOOGLE_API_KEY)
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY não encontrada no arquivo .env")

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # 2. Inicializar o LLM
    # llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    llm = ChatOpenAI(temperature=0, api_key=OPENAI_API_KEY, model='gpt-4o-mini')
    
    # 3. Criar a ferramenta Python REPL com acesso aos dataframes
    # O agente usará esta ferramenta para executar código Python e manipular os dataframes
    tool_locals = processed_dfs.copy()
    python_repl_tool = PythonAstREPLTool(locals=tool_locals)

    tools = [
        Tool(
            name="python_repl",
            description="Uma ferramenta para executar código Python. Use-a para manipular dataframes pandas, fazer cálculos e análises de dados. Os dataframes já estão carregados na variável 'tool_locals'. Você pode acessá-los diretamente pelos seus nomes (ex: ativos, ferias, etc.).",
            func=python_repl_tool.run,
        )
    ]

    # 4. Definir o template do prompt para o agente
    prompt_template = PromptTemplate.from_template(
        """
        Você é um assistente especialista em análise de dados com pandas.
        Sua tarefa é seguir as instruções passo a passo para calcular os valores de Vale Refeição (VR).

        Você tem acesso às seguintes ferramentas:
        {tools}

        Use o seguinte formato de pensamento/ação para resolver o problema:

        Thought: Você deve sempre pensar sobre qual é o próximo passo lógico para seguir as instruções.
        Action: A ação a ser tomada, que deve ser uma das ferramentas em [{tool_names}].
        Action Input: A entrada para a ação (o código Python a ser executado).
        Observation: O resultado da ação.
        ... (Este padrão de Thought/Action/Action Input/Observation pode se repetir várias vezes)

        **Exemplo de Uso:**
        Thought: O primeiro passo é ver as colunas do dataframe `funcionarios` para entender os dados.
        Action: python_repl
        Action Input: print(funcionarios.columns)
        Observation: (Saída com a lista de colunas)
        Thought: Agora que conheço as colunas, vou aplicar a próxima regra de negócio...
        Action: python_repl
        Action Input: (código pandas para a próxima etapa)
        Observation: (Resultado da execução do código)
        Thought: Eu completei todos os passos e agora tenho o dataframe final.
        Action: python_repl
        Action Input: (código para salvar o dataframe em um arquivo .csv)
        Final Answer: O dataframe final resultante de todos os cálculos.

        **Instruções Detalhadas:**
        {input}

        **Dataframes Disponíveis:**
        Os seguintes dataframes estão disponíveis para você na ferramenta `python_repl`:
        - {dataframe_names}

        **IMPORTANTE:** Ao final, sua resposta DEVE ser o dataframe final, e NADA MAIS. Salvar o dataframe final em um csv deve ser a última expressão avaliada no seu código para que seja retornado.

        Comece!

        {agent_scratchpad}
        """
    )

    # 5. Criar o agente
    agent = create_react_agent(llm, tools, prompt_template)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=25
    )

    # 6. Invocar o agente com o prompt e os nomes dos dataframes
    dataframe_names = ", ".join(processed_dfs.keys())
    full_prompt = llm_prompt.format(dataframe_names=dataframe_names)

    print("Invocando o agente... Isso pode levar alguns minutos.")
    response = agent_executor.invoke({
        "input": full_prompt,
        "dataframe_names": dataframe_names
    })

    print("--- Agente finalizou a execução ---")
    
    # O resultado final do agente deve ser o dataframe calculado
    # Tentamos extrair o resultado final da execução do agente.
    # A boa prática é o LLM retornar a variável que contém o DF final.
    final_df = None
    if 'output' in response:
        # O agente pode retornar uma string que representa o dataframe.
        # Neste caso, uma abordagem mais robusta seria o agente salvar o df
        # em uma variável e nós a recuperarmos do `tool_locals`.
        # Por simplicidade aqui, vamos assumir que o agente foi instruído
        # a deixar o resultado final em uma variável chamada 'final_df'.
        if 'final_df' in python_repl_tool.locals:
            final_df = python_repl_tool.locals['final_df']
            print("Dataframe final recuperado da variável 'final_df'.")

    if not isinstance(final_df, pd.DataFrame):
        print("AVISO: O agente não retornou um DataFrame do Pandas diretamente.")
        print("Tentando avaliar a saída como uma expressão Python.")
        try:
            # Tenta avaliar a saída como se fosse código Python que retorna o df
            final_df = eval(str(response['output']), {"pd": pd}, tool_locals)
        except Exception as e:
            print(f"Não foi possível converter a saída do agente em um DataFrame: {e}")
            print("Saída do agente:", response['output'])
            return pd.DataFrame() # Retorna DF vazio em caso de erro

    return final_df


# --- CÓDIGO REFERÊNCIA ---
# import numpy as np
# import re
# from src import config

# # Funções harmonize_sindicato_name e get_uf_from_sindicato permanecem as mesmas...
# def harmonize_sindicato_name(name):
#     if not isinstance(name, str): return ""
#     match = re.match(r'([A-Z\s]+)', name)
#     if match: return re.sub(r'[^A-Z]', '', match.group(1))
#     return re.sub(r'[^A-Z]', '', name.split('-')[0])

# def get_uf_from_sindicato(name):
#     if not isinstance(name, str): return None
#     match = re.search(r'\b([A-Z]{2})\b', name)
#     if match: return match.group(1)
#     return None

# def calculate_working_days(df, dataframes):
#     print("Iniciando cálculo de dias úteis...")
#     dias_uteis_df = dataframes.get("dias_uteis")
#     if dias_uteis_df is not None and not dias_uteis_df.empty:
#         df['SINDICATO_KEY'] = df['SINDICATO'].apply(harmonize_sindicato_name)
#         dias_uteis_df['SINDICATO_KEY'] = dias_uteis_df['SINDICATO'].apply(harmonize_sindicato_name)
#         df = pd.merge(df, dias_uteis_df[['SINDICATO_KEY', 'DIAS_UTEIS']], on="SINDICATO_KEY", how="left")
#         if 'DIAS_UTEIS' in df.columns:
#             df.rename(columns={'DIAS_UTEIS': 'DIAS_UTEIS_MES'}, inplace=True)
#             df.fillna({'DIAS_UTEIS_MES': 0}, inplace=True)
#         else:
#             df['DIAS_UTEIS_MES'] = 0
#     else:
#         df['DIAS_UTEIS_MES'] = 0
#     ferias_df = dataframes.get("ferias")
#     if ferias_df is not None and not ferias_df.empty:
#         ferias_df[config.MATRICULA_COL] = ferias_df[config.MATRICULA_COL].astype(str)
#         df[config.MATRICULA_COL] = df[config.MATRICULA_COL].astype(str)
#         ferias_agg = ferias_df.groupby(config.MATRICULA_COL)['DIAS_DE_F_RIAS'].sum().reset_index()
#         df = pd.merge(df, ferias_agg, on=config.MATRICULA_COL, how="left")
#         df.fillna({'DIAS_DE_F_RIAS': 0}, inplace=True)
#         df['DIAS_A_PAGAR'] = df['DIAS_UTEIS_MES'] - df['DIAS_DE_F_RIAS']
#         df['DIAS_A_PAGAR'] = df['DIAS_A_PAGAR'].apply(lambda x: max(x, 0))
#     else:
#         df['DIAS_A_PAGAR'] = df['DIAS_UTEIS_MES']
#     print("Cálculo de dias úteis concluído.")
#     return df

# def apply_proportional_rules(df):
#     print("Aplicando regras de pagamento proporcional...")
#     pay_period_start = pd.to_datetime('2025-04-16')
#     pay_period_end = pd.to_datetime('2025-05-15')

#     # Admissões
#     if 'ADMISSO' in df.columns:
#         df['ADMISSO'] = pd.to_datetime(df['ADMISSO'], errors='coerce')
#         admitidos_mask = (df['ADMISSO'].notna()) & (df['ADMISSO'] >= pay_period_start)
#         if admitidos_mask.any():
#             start_dates = np.array(df.loc[admitidos_mask, 'ADMISSO'], dtype='datetime64[D]')
#             end_date = np.datetime64(pay_period_end.date(), 'D')
#             df.loc[admitidos_mask, 'DIAS_A_PAGAR'] = np.busday_count(start_dates, end_date + np.timedelta64(1, 'D'))

#     # Desligamentos
#     if 'DATA_DEMISS_O' in df.columns:
#         desligados_mask = (df['DATA_DEMISS_O'].notna()) & (df['DATA_DEMISS_O'].dt.day > config.DIA_LIMITE_DESLIGAMENTO)
#         if desligados_mask.any():
#             start_date = np.datetime64(pay_period_start.date(), 'D')
#             end_dates = np.array(df.loc[desligados_mask, 'DATA_DEMISS_O'], dtype='datetime64[D]')
#             df.loc[desligados_mask, 'DIAS_A_PAGAR'] = np.busday_count(start_date, end_dates)

#     df['DIAS_A_PAGAR'] = df['DIAS_A_PAGAR'].apply(lambda x: max(x, 0))
#     print("Regras de proporcionalidade aplicadas.")
#     return df

# def apply_termination_rule(df, dataframes):
#     print("Aplicando regra de desligamento...")
#     desligados_df = dataframes.get("desligados")
#     if desligados_df is None or desligados_df.empty: return df
#     desligados_df[config.MATRICULA_COL] = desligados_df[config.MATRICULA_COL].astype(str)
#     df[config.MATRICULA_COL] = df[config.MATRICULA_COL].astype(str)
#     desligados_df['DATA_DEMISS_O'] = pd.to_datetime(desligados_df['DATA_DEMISS_O'], errors='coerce')
#     df = pd.merge(df, desligados_df[[config.MATRICULA_COL, 'DATA_DEMISS_O', 'COMUNICADO_DE_DESLIGAMENTO']], on=config.MATRICULA_COL, how="left")
#     condicao_nao_pagar = (df['COMUNICADO_DE_DESLIGAMENTO'].str.upper() == 'OK') & (df['DATA_DEMISS_O'].dt.day <= config.DIA_LIMITE_DESLIGAMENTO)
#     df.loc[condicao_nao_pagar, 'DIAS_A_PAGAR'] = 0
#     print(f"{condicao_nao_pagar.sum()} colaboradores tiveram o benefício zerado.")
#     return df

# def calculate_vr_value(df, dataframes):
#     print("Iniciando cálculo do valor do VR...")
#     sindicatos_df = dataframes.get("sindicatos")
#     if sindicatos_df is None or sindicatos_df.empty:
#         print("ERRO: Planilha de sindicatos não encontrada.")
#         df['VALOR_VR_DIARIO'] = 0
#     else:
#         df['UF'] = df['SINDICATO'].apply(get_uf_from_sindicato)
#         # Renomeia a coluna de estado na base de sindicatos para 'UF' para o merge
#         if 'ESTADO' in sindicatos_df.columns:
#             sindicatos_df.rename(columns={'ESTADO': 'UF'}, inplace=True)
#         df = pd.merge(df, sindicatos_df[['UF', 'VALOR']], on='UF', how='left')
#         df.rename(columns={'VALOR': 'VALOR_VR_DIARIO'}, inplace=True)
#         df.fillna({'VALOR_VR_DIARIO': 0}, inplace=True)
#         print("Valor do VR calculado com base na UF do sindicato.")
#     df['VALOR_TOTAL_VR'] = df['DIAS_A_PAGAR'] * df['VALOR_VR_DIARIO']
#     df['CUSTO_EMPRESA'] = df['VALOR_TOTAL_VR'] * config.PERCENTUAL_CUSTO_EMPRESA
#     df['CUSTO_COLABORADOR'] = df['VALOR_TOTAL_VR'] * config.PERCENTUAL_CUSTO_COLABORADOR
#     print("Cálculo do valor do VR concluído.")
#     return df

# def run_calculations_python(df, dataframes):
#     df = calculate_working_days(df, dataframes)
#     df = apply_termination_rule(df, dataframes)
#     df = apply_proportional_rules(df)
#     df = calculate_vr_value(df, dataframes)
#     return df