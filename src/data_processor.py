import pandas as pd

def load_and_consolidate_data(file_streams: dict) -> pd.DataFrame:
    """
    Carrega, consolida e limpa os dados de várias planilhas.
    Usa arquivos dedicados para as regras de exclusão.
    
    Args:
        file_streams (dict): Dicionário com os streams de bytes dos arquivos.
                             Ex: {'ativos': BytesIO, 'ferias': BytesIO, ...}

    Returns:
        pd.DataFrame: Um DataFrame consolidado e limpo.
    """
    # Carregar as bases de dados
    df_ativos = pd.read_excel(file_streams['ativos'])
    df_admitidos = pd.read_excel(file_streams['admitidos'])
    df_ferias = pd.read_excel(file_streams['ferias'])
    df_desligados = pd.read_excel(file_streams['desligados'])
    df_sindicato = pd.read_excel(file_streams['sindicato'])

    # Carregar bases para exclusão
    df_aprendiz = pd.read_excel(file_streams['aprendiz'])
    df_estagio = pd.read_excel(file_streams['estagio'])
    df_exterior = pd.read_excel(file_streams['exterior'])
    df_afastados = pd.read_excel(file_streams['afastamentos'])

    # --- 1. Consolidação da base principal ---
    df_main = pd.concat([df_ativos, df_admitidos], ignore_index=True).drop_duplicates(subset=['matricula'])

    # --- 2. Regras de Exclusão (baseado em arquivos) ---
    # Coleta todas as matrículas que devem ser excluídas
    matriculas_excluir = set()
    # Adicione mais colunas de matrícula se os nomes forem diferentes nos arquivos
    for df_excluir in [df_aprendiz, df_estagio, df_exterior, df_afastados]:
        if 'matricula' in df_excluir.columns:
            matriculas_excluir.update(df_excluir['matricula'])

    # Aplica o filtro de exclusão por matrícula
    df_main = df_main[~df_main['matricula'].isin(matriculas_excluir)]

    # Exclusão adicional por cargo (Diretores), conforme regra original
    cargos_excluir = ['DIRETOR']
    df_main = df_main[~df_main['cargo'].str.upper().isin(cargos_excluir)]

    # --- 3. Enriquecimento dos Dados ---
    # Juntar informações do sindicato para obter o valor do benefício
    df_main = pd.merge(df_main, df_sindicato, on='sindicato', how='left')
    
    # Juntar informações de desligados para regras de cálculo
    df_main = pd.merge(df_main, df_desligados[['matricula', 'data_desligamento', 'comunicado_desligamento_ok']], on='matricula', how='left')

    # --- Limpeza e Validação ---
    # Converter colunas de data para o formato datetime
    for col in ['data_admissao', 'data_desligamento']:
        if col in df_main.columns:
            df_main[col] = pd.to_datetime(df_main[col], errors='coerce')

    # --- Regras de Exclusão ---
    # Remover cargos específicos
    cargos_excluir = ['DIRETOR', 'ESTAGIARIO', 'APRENDIZ']
    df_main = df_main[~df_main['cargo'].str.upper().isin(cargos_excluir)]

    # Remover afastados (ex: licença maternidade)
    # Supondo que haja uma coluna 'status' ou 'afastamento'
    df_main = df_main[df_main['status'] != 'AFASTADO']
    
    # Remover quem atua no exterior
    df_main = df_main[df_main['local_trabalho'] != 'EXTERIOR']

    # Adicionar informações de férias ao DataFrame principal
    # (Esta lógica pode ser complexa, envolvendo merge e tratamento de datas)
    # ... Lógica para integrar dados de férias ...

    return df_main
