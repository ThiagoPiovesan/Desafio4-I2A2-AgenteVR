from src.data_loader import load_all_data, serialize_data_to_markdown
from src.data_processor import process_data
from src.calculation_engine import run_calculations
from src.output_generator import generate_report

from langchain.agents import Tool
from langchain.globals import set_debug
from langchain_core.prompts import PromptTemplate
from langchain_experimental.tools import PythonAstREPLTool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.language_models.chat_models import BaseChatModel

def main():
    """
    Função principal que orquestra todo o processo de cálculo de VR.
    """
    print("--- Iniciando processo de cálculo de VR ---")
    
    # 1. Carregar todos os dados
    all_dataframes = load_all_data()
    
    # 2. Consolidar, limpar e aplicar exclusões
    processed_dfs = process_data(all_dataframes)

    print(f"all_dataframes: {all_dataframes.keys()}")
    print(f"processed_df: {processed_dfs.keys()}")

    # 3. Executar os cálculos de negócio com o agente
    with open("llm_prompt.txt", "r", encoding="utf-8") as f:
        llm_prompt = f.read()

    # O agente receberá os dataframes já processados
    final_df = run_calculations(processed_dfs, llm_prompt)
    
    # 4. Gerar o relatório final
    if final_df is not None and not final_df.empty:
        print("--- Gerando relatório final ---")
        print(final_df.head())
        generate_report(final_df)
    else:
        print("--- Não foi possível gerar o relatório final, pois o dataframe resultante está vazio ou ocorreu um erro. ---")
    
    print("\n--- Processo finalizado ---")

if __name__ == "__main__":
    main()