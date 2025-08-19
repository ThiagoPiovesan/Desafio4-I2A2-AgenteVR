# Arquivo de configuração para o projeto

# Caminhos para os arquivos de entrada
INPUT_DIR = "data/input"
FILE_PATHS = {
    "admissoes": f"{INPUT_DIR}/ADMISSÃO ABRIL.xlsx",
    "afastamentos": f"{INPUT_DIR}/AFASTAMENTOS.xlsx",
    "aprendizes": f"{INPUT_DIR}/APRENDIZ.xlsx",
    "ativos": f"{INPUT_DIR}/ATIVOS.xlsx",
    "dias_uteis": f"{INPUT_DIR}/Base dias uteis.xlsx",
    "sindicatos": f"{INPUT_DIR}/Base sindicato x valor.xlsx",
    "desligados": f"{INPUT_DIR}/DESLIGADOS.xlsx",
    "estagiarios": f"{INPUT_DIR}/ESTÁGIO.xlsx",
    "exterior": f"{INPUT_DIR}/EXTERIOR.xlsx",
    "ferias": f"{INPUT_DIR}/FÉRIAS.xlsx",
    "template_vr": f"{INPUT_DIR}/VR MENSAL 05.2025.xlsx",
}

# Caminho para o arquivo de saída
OUTPUT_DIR = "data/output"
OUTPUT_FILE = f"{OUTPUT_DIR}/VR_compra_calculado.xlsx"

# Colunas importantes (exemplo, pode precisar de ajuste)
MATRICULA_COL = "MATRICULA"

# Regras de negócio
PERCENTUAL_CUSTO_EMPRESA = 0.80
PERCENTUAL_CUSTO_COLABORADOR = 0.20
DIA_LIMITE_DESLIGAMENTO = 15

