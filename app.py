import streamlit as st
import pandas as pd
from src.data_processor import load_and_consolidate_data
from src.calculation_engine import run_calculation
# from src.report_generator import generate_final_report # Supondo que esta função exista
import os
import zipfile
import io

st.set_page_config(layout="wide")
st.title("🤖 Agente Autônomo para Cálculo de Vale Refeição (VR)")

st.info("**Objetivo:** Automatizar o processo mensal de compra de VR, garantindo precisão e eficiência.")

# --- 1. Inputs do Usuário ---
st.header("1. Carregue as planilhas do mês")

col1, col2 = st.columns(2)
with col1:
    mes_referencia = st.number_input("Mês de Referência", min_value=1, max_value=12, value=5)
with col2:
    ano_referencia = st.number_input("Ano de Referência", min_value=2020, max_value=2030, value=2025)

uploaded_zip = st.file_uploader(
    "Carregue um arquivo .zip contendo as 5 planilhas (Ativos, Férias, Desligados, Admitidos, Sindicato)",
    type=['zip']
)

# --- 2. Processamento ---
if st.button("▶️ Executar Cálculo Automatizado"):
    if uploaded_zip is None:
        st.error("Por favor, carregue o arquivo .zip com as planilhas.")
    else:
        with st.spinner("O agente está trabalhando... Lendo e consolidando dados..."):
            try:
                file_streams = {} # Dicionário para armazenar os arquivos em memória
                # Mapeia palavras-chave nos nomes dos arquivos para chaves padronizadas
                keyword_map = {
                    'ativos': 'ativos',
                    'admissão': 'admitidos',
                    'admissao': 'admitidos',
                    'férias': 'ferias',
                    'ferias': 'ferias',
                    'desligados': 'desligados',
                    'sindicato': 'sindicato',
                    'afastamentos': 'afastamentos',
                    'aprendiz': 'aprendiz',
                    'estágio': 'estagio',
                    'estagio': 'estagio',
                    'exterior': 'exterior',
                }
                expected_keys = ['ativos', 'admitidos', 'ferias', 'desligados', 'sindicato', 'afastamentos', 'aprendiz', 'estagio', 'exterior']
                
                with zipfile.ZipFile(uploaded_zip) as z:
                    # Mapeia os arquivos dentro do ZIP para os nomes esperados
                    for filename in z.namelist():
                        # Ignora arquivos de sistema do macOS
                        if filename.startswith("__MACOSX/") or ".DS_Store" in filename:
                            continue
                        
                        file_lower = filename.lower()
                        for keyword, key in keyword_map.items():
                            if keyword in file_lower:
                                file_streams[key] = io.BytesIO(z.read(filename))
                                break

                # Validação: verifica se todos os arquivos foram encontrados
                if not all(key in file_streams for key in expected_keys):
                    missing = set(expected_keys) - set(file_streams.keys())
                    st.error(f"Erro no arquivo ZIP: Não foi possível encontrar as seguintes planilhas: {', '.join(missing)}. Verifique os nomes dos arquivos dentro do ZIP.")
                else:
                    df_consolidado = load_and_consolidate_data(file_streams)
                    st.success("Dados consolidados e limpos com sucesso!")
                    st.write("Amostra dos dados consolidados:")
                    st.dataframe(df_consolidado.head())

                    with st.spinner("Calculando benefícios... Aplicando regras de negócio..."):
                        df_final = run_calculation(df_consolidado, mes_referencia, ano_referencia)
                        st.success("Cálculo de benefícios finalizado!")

                    # --- 3. Resultados ---
                    st.header("3. Resultados do Cálculo")
                    st.dataframe(df_final)

                    # Gerar arquivo para download em memória
                    output_stream = io.BytesIO()
                    df_final.to_excel(output_stream, index=False, engine='openpyxl')
                    output_stream.seek(0) # Volta para o início do stream

                    st.download_button(
                        label="📥 Baixar Relatório Final para Fornecedor",
                        data=output_stream,
                        file_name=f"VR_MENSAL_{mes_referencia:02d}_{ano_referencia}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except zipfile.BadZipFile:
                st.error("O arquivo carregado não é um ZIP válido.")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado durante o processamento: {e}")