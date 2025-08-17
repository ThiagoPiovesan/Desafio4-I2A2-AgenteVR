import pandas as pd
import numpy as np
import holidays

def calculate_payable_days(employee_row: pd.Series, month: int, year: int) -> int:
    """
    Calcula o número de dias de VR a serem pagos para um único colaborador.
    """
    start_of_month = pd.Timestamp(year, month, 1)
    end_of_month = start_of_month + pd.offsets.MonthEnd(0)

    # 1. Definir o calendário de feriados (exemplo para o Brasil, SP)
    # Isso deve ser parametrizado pelo sindicato/localidade do colaborador
    br_holidays = holidays.Brazil(state=employee_row.get('uf', None), city=employee_row.get('cidade', None))

    # 2. Calcular dias úteis no mês (Seg-Sex)
    business_days = pd.bdate_range(start=start_of_month, end=end_of_month)
    
    # 3. Remover feriados
    payable_days_list = [day for day in business_days if day not in br_holidays]

    # 4. Ajustar pela data de admissão
    if pd.notna(employee_row['data_admissao']) and employee_row['data_admissao'].month == month and employee_row['data_admissao'].year == year:
        payable_days_list = [day for day in payable_days_list if day >= employee_row['data_admissao']]

    # 5. Ajustar pela data de desligamento (com a regra do dia 15)
    if pd.notna(employee_row['data_desligamento']) and employee_row['data_desligamento'].month == month and employee_row['data_desligamento'].year == year:
        # Se comunicado OK até dia 15, não recebe nada no mês
        if employee_row.get('comunicado_desligamento_ok') == 'OK' and employee_row['data_desligamento'].day <= 15:
            return 0
        # Se não, recebe proporcionalmente até a data do desligamento
        else:
            payable_days_list = [day for day in payable_days_list if day <= employee_row['data_desligamento']]

    # 6. Subtrair dias de férias no mês
    # (Supondo que df_ferias tenha 'matricula', 'inicio_ferias', 'fim_ferias')
    # ... Lógica para remover dias de férias da payable_days_list ...

    # 7. Subtrair afastamentos
    # ... Lógica para remover dias de afastamento ...

    return len(payable_days_list)

def run_calculation(df: pd.DataFrame, month: int, year: int) -> pd.DataFrame:
    """
    Aplica o cálculo de dias e valores para todo o DataFrame.
    """
    df_result = df.copy()
    
    # Calcular dias a pagar para cada colaborador
    df_result['dias_a_pagar'] = df_result.apply(
        lambda row: calculate_payable_days(row, month, year),
        axis=1
    )

    # Calcular valores
    # Supondo que df_sindicato adicionou a coluna 'valor_vr_dia'
    df_result['valor_total_vr'] = df_result['dias_a_pagar'] * df_result['valor_vr_dia']
    df_result['custo_empresa'] = df_result['valor_total_vr'] * 0.80
    df_result['desconto_colaborador'] = df_result['valor_total_vr'] * 0.20

    return df_result
