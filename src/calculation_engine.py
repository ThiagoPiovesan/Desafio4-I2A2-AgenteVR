import pandas as pd
from src import config
import numpy as np
import re

# Funções harmonize_sindicato_name e get_uf_from_sindicato permanecem as mesmas...
def harmonize_sindicato_name(name):
    if not isinstance(name, str): return ""
    match = re.match(r'([A-Z\s]+)', name)
    if match: return re.sub(r'[^A-Z]', '', match.group(1))
    return re.sub(r'[^A-Z]', '', name.split('-')[0])

def get_uf_from_sindicato(name):
    if not isinstance(name, str): return None
    match = re.search(r'\b([A-Z]{2})\b', name)
    if match: return match.group(1)
    return None

def calculate_working_days(df, dataframes):
    print("Iniciando cálculo de dias úteis...")
    dias_uteis_df = dataframes.get("dias_uteis")
    if dias_uteis_df is not None and not dias_uteis_df.empty:
        df['SINDICATO_KEY'] = df['SINDICATO'].apply(harmonize_sindicato_name)
        dias_uteis_df['SINDICATO_KEY'] = dias_uteis_df['SINDICATO'].apply(harmonize_sindicato_name)
        df = pd.merge(df, dias_uteis_df[['SINDICATO_KEY', 'DIAS_UTEIS']], on="SINDICATO_KEY", how="left")
        if 'DIAS_UTEIS' in df.columns:
            df.rename(columns={'DIAS_UTEIS': 'DIAS_UTEIS_MES'}, inplace=True)
            df.fillna({'DIAS_UTEIS_MES': 0}, inplace=True)
        else:
            df['DIAS_UTEIS_MES'] = 0
    else:
        df['DIAS_UTEIS_MES'] = 0
    ferias_df = dataframes.get("ferias")
    if ferias_df is not None and not ferias_df.empty:
        ferias_df[config.MATRICULA_COL] = ferias_df[config.MATRICULA_COL].astype(str)
        df[config.MATRICULA_COL] = df[config.MATRICULA_COL].astype(str)
        ferias_agg = ferias_df.groupby(config.MATRICULA_COL)['DIAS_DE_F_RIAS'].sum().reset_index()
        df = pd.merge(df, ferias_agg, on=config.MATRICULA_COL, how="left")
        df.fillna({'DIAS_DE_F_RIAS': 0}, inplace=True)
        df['DIAS_A_PAGAR'] = df['DIAS_UTEIS_MES'] - df['DIAS_DE_F_RIAS']
        df['DIAS_A_PAGAR'] = df['DIAS_A_PAGAR'].apply(lambda x: max(x, 0))
    else:
        df['DIAS_A_PAGAR'] = df['DIAS_UTEIS_MES']
    print("Cálculo de dias úteis concluído.")
    return df

def apply_proportional_rules(df):
    print("Aplicando regras de pagamento proporcional...")
    pay_period_start = pd.to_datetime('2025-04-16')
    pay_period_end = pd.to_datetime('2025-05-15')

    # Admissões
    if 'ADMISSO' in df.columns:
        df['ADMISSO'] = pd.to_datetime(df['ADMISSO'], errors='coerce')
        admitidos_mask = (df['ADMISSO'].notna()) & (df['ADMISSO'] >= pay_period_start)
        if admitidos_mask.any():
            start_dates = np.array(df.loc[admitidos_mask, 'ADMISSO'], dtype='datetime64[D]')
            end_date = np.datetime64(pay_period_end.date(), 'D')
            df.loc[admitidos_mask, 'DIAS_A_PAGAR'] = np.busday_count(start_dates, end_date + np.timedelta64(1, 'D'))

    # Desligamentos
    if 'DATA_DEMISS_O' in df.columns:
        desligados_mask = (df['DATA_DEMISS_O'].notna()) & (df['DATA_DEMISS_O'].dt.day > config.DIA_LIMITE_DESLIGAMENTO)
        if desligados_mask.any():
            start_date = np.datetime64(pay_period_start.date(), 'D')
            end_dates = np.array(df.loc[desligados_mask, 'DATA_DEMISS_O'], dtype='datetime64[D]')
            df.loc[desligados_mask, 'DIAS_A_PAGAR'] = np.busday_count(start_date, end_dates)

    df['DIAS_A_PAGAR'] = df['DIAS_A_PAGAR'].apply(lambda x: max(x, 0))
    print("Regras de proporcionalidade aplicadas.")
    return df

def apply_termination_rule(df, dataframes):
    print("Aplicando regra de desligamento...")
    desligados_df = dataframes.get("desligados")
    if desligados_df is None or desligados_df.empty: return df
    desligados_df[config.MATRICULA_COL] = desligados_df[config.MATRICULA_COL].astype(str)
    df[config.MATRICULA_COL] = df[config.MATRICULA_COL].astype(str)
    desligados_df['DATA_DEMISS_O'] = pd.to_datetime(desligados_df['DATA_DEMISS_O'], errors='coerce')
    df = pd.merge(df, desligados_df[[config.MATRICULA_COL, 'DATA_DEMISS_O', 'COMUNICADO_DE_DESLIGAMENTO']], on=config.MATRICULA_COL, how="left")
    condicao_nao_pagar = (df['COMUNICADO_DE_DESLIGAMENTO'].str.upper() == 'OK') & (df['DATA_DEMISS_O'].dt.day <= config.DIA_LIMITE_DESLIGAMENTO)
    df.loc[condicao_nao_pagar, 'DIAS_A_PAGAR'] = 0
    print(f"{condicao_nao_pagar.sum()} colaboradores tiveram o benefício zerado.")
    return df

def calculate_vr_value(df, dataframes):
    print("Iniciando cálculo do valor do VR...")
    sindicatos_df = dataframes.get("sindicatos")
    if sindicatos_df is None or sindicatos_df.empty:
        print("ERRO: Planilha de sindicatos não encontrada.")
        df['VALOR_VR_DIARIO'] = 0
    else:
        df['UF'] = df['SINDICATO'].apply(get_uf_from_sindicato)
        # Renomeia a coluna de estado na base de sindicatos para 'UF' para o merge
        if 'ESTADO' in sindicatos_df.columns:
            sindicatos_df.rename(columns={'ESTADO': 'UF'}, inplace=True)
        df = pd.merge(df, sindicatos_df[['UF', 'VALOR']], on='UF', how='left')
        df.rename(columns={'VALOR': 'VALOR_VR_DIARIO'}, inplace=True)
        df.fillna({'VALOR_VR_DIARIO': 0}, inplace=True)
        print("Valor do VR calculado com base na UF do sindicato.")
    df['VALOR_TOTAL_VR'] = df['DIAS_A_PAGAR'] * df['VALOR_VR_DIARIO']
    df['CUSTO_EMPRESA'] = df['VALOR_TOTAL_VR'] * config.PERCENTUAL_CUSTO_EMPRESA
    df['CUSTO_COLABORADOR'] = df['VALOR_TOTAL_VR'] * config.PERCENTUAL_CUSTO_COLABORADOR
    print("Cálculo do valor do VR concluído.")
    return df

def run_calculations(df, dataframes):
    df = calculate_working_days(df, dataframes)
    df = apply_termination_rule(df, dataframes)
    df = apply_proportional_rules(df)
    df = calculate_vr_value(df, dataframes)
    return df
