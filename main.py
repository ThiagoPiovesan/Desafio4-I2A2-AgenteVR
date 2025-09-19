# ============================================================================
# Autor: Thiago Piovesan
# Descrição: Script principal para executar o processamento dos dados
# ============================================================================
# Libs importation:
import os
import argparse
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from src import config
from src.agente_dados import criar_agente_dados
from src.agente_calculo import criar_agente_analista

# ============================================================================
DATA_STORE = {}

# ============================================================================
def main(args):
    """
        Função principal que orquestra todo o processo de cálculo de VR.
    """
    print("--- Iniciando processo de cálculo de VR ---")
    
    # Load environment variables:
    load_dotenv()
    
    if args.llm == "openai":
        llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
    elif args.llm == "gemini":
        llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-1.5-flash-latest")
    else:
        raise ValueError("Modelo de linguagem não suportado. Use 'openai' ou 'gemini'.")
    
    llm_calc = ChatGoogleGenerativeAI(temperature=0, model="gemini-1.5-flash-latest")
    
    # ============================================================================
    # Passo 0: Garantir que o diretório de entrada existe e padronizar nomes de arquivos:
    
    list_files_standardized_1 = []
    list_files_standardized_2 = []
    for (filename_1, path_1), (filename_2, path_2) in zip(config.FILE_PATHS_1.items(), config.FILE_PATHS_2.items()):
        # dir_path = os.path.dirname(path)
        # ensure_directory_exists(dir_path)
        # standardize_filenames(dir_path)
        if os.path.exists(path_1):
           list_files_standardized_1.append(path_1)  # remove espaços e quebras de linha
        else:   
           print(f"Aviso: Arquivo não encontrado - {path_1}")

        if os.path.exists(path_2):
           list_files_standardized_2.append(path_2)  # remove espaços e quebras de linha
        else:   
           print(f"Aviso: Arquivo não encontrado - {path_2}")

    print(f"Arquivos padronizados 1: {list_files_standardized_1}")
    print(f"Arquivos padronizados 2: {list_files_standardized_2}")
    # ============================================================================
    # Passo 1: Instanciar o agente responsavel por carregar e limpar os arquivos:
    agente_dados, DATA_STORE = criar_agente_dados(llm)
    print("Agente 1# -> Agente responsável por carregar e limpar os arquivos dados criado com sucesso.")
    
    # instrucao = f"""
    # A lista de arquivos a ser processada é: {list_files_standardized}
    # O schema final para o DataFrame 'vr_unificado' deve ser a agrupação de todas as colunas únicas dos arquivos fornecidos.
    # """
    
    # Passo 1.1: Executar o agente para processar os arquivos e obter o DataFrame unificado:
    resultado_agente_dados_1 = agente_dados.invoke({'input': list_files_standardized_1})

    # print('--- Estado do DATA_STORE após o Agente 1 ---')
    # print(DATA_STORE.keys())
    # print(DATA_STORE['vr_unificado'].head())
    
    resultado_agente_dados_2 = agente_dados.invoke({'input': list_files_standardized_2})
    
    # TENTATIVA 1: Enviar a lista completa de arquivos de uma vez (pode ser muito longo)
    # arquivos_str = "\n".join(list_files_standardized)
    # resultado_agente_dados = agente_dados.invoke({
    #     "input": f"Aqui está a lista de arquivos a serem processados:\n{arquivos_str}",
    # })
    
    # TENTATIVA 2: Enviar os arquivos um por um (mais seguro para evitar estouro de contexto)
    # for path in list_files_standardized:
    #     print(f"Processando: {path}...")
    #     agente_dados.invoke({
    #         "input": f"Leia e execute os passos 1, 2, 3 e 4 para processar este arquivo: {path}"
    #     })

    # # quando terminar:
    # resultado_agente_dados = agente_dados.invoke({
    #     "input": "Agora una todos os DataFrames carregados, usando o passo 5."
    # })

    # ======================================================================
    # Passo 1.2: Exibe o resultado final
    print("\n" + "="*50)
    print("      RESULTADO FINAL DO AGENTE")
    print("="*50)
    print(resultado_agente_dados_1['output'])
    print("="*50)
    print(resultado_agente_dados_2['output'])
    print("="*50)

    print("# ESTADO FINAL DO DATA_STORE")
    print("="*50)
    print(DATA_STORE.keys())
    # print(DATA_STORE['vr_unificado'].head())
    print("="*50)
    
    # ==================================================================================
    # 1.4. Verifica o DataFrame unificado no nosso "data store"
    if 'vr_unificado' in DATA_STORE:
        print("\n\nDataFrame Unificado 'vr_unificado' criado com sucesso!")
        df_final = DATA_STORE['vr_unificado']
        print(df_final.head())
        
        print("\nInformações do DataFrame final:")
        df_final.info()
    else:
        df_final = pd.read_excel('data/output/vr_unificado.csv')
        DATA_STORE['vr_unificado'] = df_final
        print("\nO DataFrame final 'vr_unificado' não foi encontrado. Tentando ler de 'data/output/vr_unificado.csv'...")
        
    # ============================================================================
    # Save in CSV:
    # output_dir = "data/output"
    # ensure_directory_exists(output_dir)
    # output_path = os.path.join(output_dir, "vr_unificado.csv")
    # df_final.to_csv(output_path, index=False)
    
    # ============================================================================
     # --- EXECUÇÃO DO AGENTE 2 ---
    print("--- Iniciando Agente 2: Analista de Folha de Pagamento ---")
    
    list_files_calc_standardized = []
    for filename, path in config.CALC_PATHS.items():
        # dir_path = os.path.dirname(path)
        # ensure_directory_exists(dir_path)
        # standardize_filenames(dir_path)
        if os.path.exists(path):
           list_files_calc_standardized.append(path)
        else:
           print(f"Aviso: Arquivo não encontrado - {path}")
    
    agente_analista_executor = criar_agente_analista(llm=llm_calc, data_store=df_final)
    # Invoque o agente com o dicionário contendo APENAS a chave 'input'
    resultado_final = agente_analista_executor.invoke(
        {"input": list_files_calc_standardized}
    )
    
    print("\n" + "="*50)
    print("      RESULTADO FINAL DO AGENTE 2")
    print("="*50)
    print(resultado_final['output'])
    
    
# ============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processa dados de VR usando LLMs.")
    parser.add_argument("--llm", type=str, required=True, help="Modelo de linguagem a ser utilizado.", choices=["openai", "gemini"])
    args = parser.parse_args()

    main(args)  