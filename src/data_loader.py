import pandas as pd
from src import config
import re

def clean_column_names(df):
    """
    Limpa e padroniza os nomes das colunas de um DataFrame:
    - Converte para string.
    - Remove espaços extras no início e no fim.
    - Substitui espaços e caracteres especiais por um underscore.
    - Converte para maiúsculas.
    """
    new_columns = {}
    for col in df.columns:
        col_str = str(col)
        # Remove espaços no início/fim
        new_col = col_str.strip()
        # Substitui espaços e caracteres não alfanuméricos por _
        new_col = re.sub(r'\\s+', '_', new_col)
        new_col = re.sub(r'[^a-zA-Z0-9_]', '_', new_col)
        # Remove múltiplos underscores
        new_col = re.sub(r'_+', '_', new_col)
        # Converte para maiúsculas para padronização
        new_col = new_col.upper()
        new_columns[col] = new_col
    df.rename(columns=new_columns, inplace=True)
    return df

def load_all_data():
    """
    Carrega todos os arquivos Excel, limpa os nomes das colunas e padroniza
    colunas importantes.
    """
    dataframes = {}
    for name, path in config.FILE_PATHS.items():
        try:
            header_row = 0
            if name == "dias_uteis":
                header_row = 1
            
            df = pd.read_excel(path, header=header_row)
            df = clean_column_names(df)
            
            # Renomeações específicas pós-limpeza
            if name == "exterior" and "CADASTRO" in df.columns:
                df.rename(columns={"CADASTRO": config.MATRICULA_COL}, inplace=True)
            if name == "dias_uteis" and "SINDICADO" in df.columns:
                df.rename(columns={"SINDICADO": "SINDICATO"}, inplace=True)

            dataframes[name] = df
            print(f"Arquivo '{path}' carregado e limpo com sucesso.")

        except FileNotFoundError:
            print(f"AVISO: Arquivo não encontrado em '{path}'. Ignorando.")
            dataframes[name] = pd.DataFrame()
        except Exception as e:
            print(f"ERRO: Falha ao carregar o arquivo '{path}': {e}")
            dataframes[name] = pd.DataFrame()
            
    return dataframes

if __name__ == '__main__':
    all_data = load_all_data()
    for name, df in all_data.items():
        if not df.empty:
            print(f"\n--- DataFrame: {name} ---")
            print("Colunas:", df.columns.tolist())
            print(df.head())
