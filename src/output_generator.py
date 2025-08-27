# ------------------------------------------------------------
# Code developed by: Thiago Piovesan
# Created on: 2025-08-17
# ------------------------------------------------------------
# Libs:
import pandas as pd
import os
from src import config

# --- CÓDIGO REFERÊNCIA ---
def generate_report(df):
    """
    Gera a planilha final para a operadora de VR, usando o arquivo
    'VR MENSAL 05.2025.xlsx' como base para as colunas.
    """
    print("Iniciando geração do relatório final...")
    
    if df.empty:
        print("AVISO: DataFrame final está vazio. Nenhum relatório será gerado.")
        return

    try:
        # Carrega o template para obter a ordem e os nomes exatos das colunas
        template_df = pd.read_excel(config.FILE_PATHS["template_vr"], header=1)
        template_columns = template_df.columns.tolist()
    except Exception as e:
        print(f"ERRO: Falha ao ler o template '{config.FILE_PATHS['template_vr']}'. Usando colunas padrão. Erro: {e}")
        # Colunas de fallback caso o template não possa ser lido
        template_columns = ['Matricula', 'Nome Completo', 'Valor a ser creditado']

    # Cria um novo DataFrame para o output
    output_df = pd.DataFrame()

    # Mapeia as colunas do nosso df calculado para as colunas do template
    # (os nomes podem variar, então fazemos um mapeamento explícito)
    mapping = {
        'Matricula': config.MATRICULA_COL,
        # 'Nome Completo': 'NOME_COMPLETO', # Assumindo que este é o nome da coluna no df
        'Valor a ser creditado': 'VALOR_TOTAL_VR',
        'Custo empresa': 'CUSTO_EMPRESA',
        'Desconto profissional': 'CUSTO_COLABORADOR'
    }

    print("Mapeando colunas para o formato final...")
    for template_col, source_col in mapping.items():
        if source_col in df.columns:
            # Renomeia a coluna do nosso df para corresponder ao template
            output_df[template_col] = df[source_col]
        else:
            # Se a coluna de origem não existir, cria uma coluna vazia no output
            output_df[template_col] = None
            print(f"AVISO: Coluna de origem '{source_col}' não encontrada. Coluna '{template_col}' ficará vazia.")

    # Garante que todas as colunas do template existam no arquivo final, na ordem correta
    for col in template_columns:
        if col not in output_df.columns:
            output_df[col] = None
    
    output_df = output_df[template_columns]

    # Salva o arquivo final
    try:
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        print(f"Salvando relatório em '{config.OUTPUT_FILE}'...")
        output_df.to_excel(config.OUTPUT_FILE, index=False)
        print("Relatório final gerado com sucesso!")
    except Exception as e:
        print(f"ERRO: Falha ao salvar o relatório final: {e}")