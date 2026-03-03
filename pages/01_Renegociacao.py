import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

st.set_page_config(page_title="TIM | Análise de Renegociação", layout="wide")

# CSS para manter o padrão visual
st.markdown("<style>.stApp { background-color: #0E1117; }</style>", unsafe_allow_html=True)

st.title("🔄 Dashboard de Renegociações")
st.info("Esta aba é dedicada exclusivamente à análise de contratos de Renegociação.")

# Reutilizamos a lógica de busca de arquivos no GitHub
arquivos_locais = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]

if arquivos_locais:
    dfs = [pd.read_excel(f).rename(columns=lambda x: x.strip().lower()) for f in arquivos_locais]
    df = pd.concat(dfs, ignore_index=True)
    
    # Filtrar APENAS Renegociação
    df_reneg = df[df['tipo de contratação'].str.upper() == 'RENEGOCIAÇÃO'].copy()
    
    if not df_reneg.empty:
        # Aqui você pode colocar gráficos e tabelas específicos de Reneg
        st.metric("Total de Acessos Renegociados", int(df_reneg['acessos'].sum()))
        st.dataframe(df_reneg[['parceiro', 'responsável venda', 'razão social', 'acessos', 'preço oferta']])
    else:
        st.warning("Nenhuma renegociação encontrada nas bases atuais.")
else:
    st.error("Bases não encontradas.")