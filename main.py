from src.data_loader import load_all_data
from src.data_processor import process_data
from src.calculation_engine import run_calculations
from src.output_generator import generate_report

def main():
    """
    Função principal que orquestra todo o processo de cálculo de VR.
    """
    print("--- Iniciando processo de cálculo de VR ---")
    
    # 1. Carregar todos os dados
    all_dataframes = load_all_data()
    
    # 2. Consolidar, limpar e aplicar exclusões
    processed_df = process_data(all_dataframes)
    
    # 3. Executar os cálculos de negócio
    final_df = run_calculations(processed_df, all_dataframes)
    
    # 4. Gerar o relatório final
    generate_report(final_df)
    
    print("\n--- Processo finalizado ---")

if __name__ == "__main__":
    main()