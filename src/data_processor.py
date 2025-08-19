import pandas as pd
from src import config

def consolidate_data(dataframes):
    """
    Consolida as bases de dados em um único DataFrame.
    A base principal é a de ATIVOS, à qual se anexa a de ADMISSÕES.
    """
    print("Iniciando consolidação dos dados...")
    
    ativos_df = dataframes.get("ativos", pd.DataFrame()).copy()
    if ativos_df.empty:
        print("ERRO: Base de ATIVOS está vazia. Não é possível continuar.")
        return pd.DataFrame()

    # Remover colunas que começam com "Unnamed"
    ativos_df = ativos_df.loc[:, ~ativos_df.columns.str.startswith('Unnamed')]

    admissoes_df = dataframes.get("admissoes", pd.DataFrame()).copy()
    if not admissoes_df.empty:
        admissoes_df = admissoes_df.loc[:, ~admissoes_df.columns.str.startswith('Unnamed')]
        # Garante que as colunas MATRICULA sejam do mesmo tipo para o concat
        ativos_df[config.MATRICULA_COL] = ativos_df[config.MATRICULA_COL].astype(str)
        admissoes_df[config.MATRICULA_COL] = admissoes_df[config.MATRICULA_COL].astype(str)
        
        base_final = pd.concat([ativos_df, admissoes_df], ignore_index=True)
    else:
        base_final = ativos_df
    
    # Remove duplicatas, mantendo a primeira ocorrência (caso um admitido já esteja em ativos)
    base_final.drop_duplicates(subset=[config.MATRICULA_COL], keep='first', inplace=True)
    
    print(f"Base consolidada com {len(base_final)} registros únicos.")
    return base_final

def apply_exclusions(df, dataframes):
    """
    Aplica as regras de exclusão na base de dados consolidada.
    Remove estagiários, aprendizes, afastados e pessoal do exterior.
    """
    if df.empty:
        return df

    print("Aplicando regras de exclusão...")
    
    matriculas_a_excluir = set()
    
    # Lista de dataframes para verificar exclusões
    dfs_to_exclude = ["estagiarios", "aprendizes", "afastamentos", "exterior"]
    
    for name in dfs_to_exclude:
        df_excluir = dataframes.get(name)
        if df_excluir is not None and not df_excluir.empty:
            # Garante que a coluna de matrícula existe
            if config.MATRICULA_COL in df_excluir.columns:
                # Limpa valores nulos e converte para string antes de adicionar ao set
                valid_matriculas = df_excluir[config.MATRICULA_COL].dropna().astype(str).unique()
                matriculas_a_excluir.update(valid_matriculas)
            else:
                print(f"AVISO: Coluna '{config.MATRICULA_COL}' não encontrada no arquivo '{name}'.")

    print(f"Encontradas {len(matriculas_a_excluir)} matrículas únicas para excluir.")
    
    # Garante que a coluna de matrícula no DF principal também seja string para comparação
    df[config.MATRICULA_COL] = df[config.MATRICULA_COL].astype(str)
    
    df_filtrado = df[~df[config.MATRICULA_COL].isin(matriculas_a_excluir)]
    
    print(f"Base após exclusões com {len(df_filtrado)} registros.")
    return df_filtrado

def clean_data(df):
    """
    Realiza a limpeza e validação dos dados.
    (Placeholder para lógicas futuras)
    """
    print("Iniciando limpeza e validação dos dados...")
    # Ex: df['Data Admissão'] = pd.to_datetime(df['Data Admissão'], errors='coerce')
    
    return df

def process_data(dataframes):
    """
    Orquestra o processo de consolidação, exclusão e limpeza.
    """
    consolidated_df = consolidate_data(dataframes)
    excluded_df = apply_exclusions(consolidated_df, dataframes)
    cleaned_df = clean_data(excluded_df)
    
    print("Processamento de dados concluído.")
    return cleaned_df