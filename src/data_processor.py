# ------------------------------------------------------------
# Code developed by: Thiago Piovesan
# Created on: 2025-08-17
# ------------------------------------------------------------
# Libs:
import pandas as pd
from src import config

# ------------------------------------------------------------
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
        # admissoes_df = admissoes_df.loc[:, ~admissoes_df.columns.str.startswith('Unnamed')]
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
    Remove diretores, estagiários, aprendizes, afastados e pessoal do exterior.
    """
    if df.empty:
        return df

    print("Aplicando regras de exclusão...")
    matriculas_a_excluir = set()
    
    # Lista de dataframes para verificar exclusões
    dfs_to_exclude = ["estagiarios", "aprendizes", "afastamentos", "exterior", 'ativos']
    
    # Lista de funcoes para verificar exclusão:
    funcoes_excluir = ["DIRETOR"] 
    
    for name in dfs_to_exclude:
        print(f"Verificando exclusões no DataFrame: {name}")
        df_excluir = dataframes.get(name)
        if name == 'ativos':
            # Verifica funções específicas para exclusão
            # Corrigido: verifica se algum valor da lista está nas colunas
            mask_cargo = df["TITULO_DO_CARGO"].isin(funcoes_excluir) if "TITULO_DO_CARGO" in df.columns else False
            mask_titulo = df["CARGO"].isin(funcoes_excluir) if "CARGO" in df.columns else False
            
            if (mask_cargo.any() if isinstance(mask_cargo, pd.Series) else mask_cargo) or \
               (mask_titulo.any() if isinstance(mask_titulo, pd.Series) else mask_titulo):
                # Filtra apenas os registros que atendem aos critérios de exclusão
                funcionarios_diretor = df[mask_cargo | mask_titulo] if isinstance(mask_cargo, pd.Series) and isinstance(mask_titulo, pd.Series) else df
                valid_matriculas = funcionarios_diretor[config.MATRICULA_COL].dropna().astype(str).unique()
                matriculas_a_excluir.update(valid_matriculas)
        else:
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
    
    # remove dataframes ativos + admissao and add the new one:
    dataframes.pop("ativos", None)
    dataframes.pop("admissoes", None)
    dataframes["funcionarios"] = cleaned_df

    print("Processamento de dados concluído.")
    return dataframes