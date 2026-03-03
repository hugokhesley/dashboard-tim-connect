import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

# CONFIGURAÇÃO DE PÁGINA FIXA
st.set_page_config(page_title="TIM | Vendas Corporate", layout="wide", page_icon="🎯")

# MAPEAMENTO DE STATUS (image_b81348.png)
MAP_STATUS = {
    'CONCLUÍDO': 'ENTRANTE', 'ENTREGA': 'ENTRANTE', 'FIDELIZAÇÃO': 'ENTRANTE',
    'AG. IMPR. DOCs/EXPEDIÇÃO': 'ENTRANTE', 'INCONSISTENCIA': 'ENTRANTE',
    'INSUCESSO VENDAS': 'ENTRANTE', 'PRÉ-ATIVAÇÃO-P2B': 'ENTRANTE',
    'BATE/VOLTA - LOG': 'ENTRANTE', 'BATE/VOLTA CONTROL TOWER': 'ENTRANTE',
    'FATURAMENTO': 'ENTRANTE', 'DOCUMENTAÇÃO': 'ENTRANTE',
    'REPRESAMENTO': 'ENTRANTE', 'REPROC. CORREÇÃO NFE': 'ENTRANTE',
    'REPROC. CRIAÇÃO ORDENS': 'ENTRANTE', 'APROVAÇÃO ÁREA DE ATUAÇÃO': 'ENTRANTE',
    'AG. ATIVAÇÃO': 'ENTRANTE', 'ATIVAÇÃO MANUAL': 'ENTRANTE', 'PRÉ-ATIVAÇÃO': 'ENTRANTE',
    'AG. ANALISE ANTI-FRAUDE': 'EM ANÁLISE', 'ANÁLISE DE CADASTRO - CRÉDITO': 'CRÉDITO',
    'CADASTRO': 'PRÉ-VENDA', 'DEVOLVIDOS': 'DEVOLVIDOS'
}

st.markdown("""<style>.stApp { background-color: #0E1117; } .header-premium { background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px; } .column-header { padding: 10px; border-radius: 8px 8px 0 0; text-align: center; font-weight: bold; color: white; font-size: 14px; text-transform: uppercase; } .header-pendente { background-color: #6366F1; } .header-analise { background-color: #F59E0B; } .header-devolvido { background-color: #EF4444; } .header-entrante { background-color: #10B981; }</style>""", unsafe_allow_html=True)

MES_PRESENTE = "03/2026" # TRAVA ABSOLUTA NO PRESENTE

arquivos_locais = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]

if arquivos_locais:
    df = pd.concat([pd.read_excel(b).rename(columns=lambda x: x.strip().lower()) for b in arquivos_locais], ignore_index=True)
    df['acessos'] = pd.to_numeric(df['acessos'], errors='coerce').fillna(0)
    df['preço oferta'] = pd.to_numeric(df['preço oferta'], errors='coerce').fillna(0)
    df['status_dash'] = df['fila atual'].str.strip().str.upper().map(MAP_STATUS).fillna('OUTROS')
    df['data de ativação'] = pd.to_datetime(df['data de ativação'], errors='coerce')
    df['mes_ref_ativa'] = df['data de ativação'].dt.strftime('%m/%Y')

    with st.sidebar:
        parc_sel = st.multiselect("Parceiros", sorted(df['parceiro'].dropna().unique()), default=df['parceiro'].dropna().unique())
        st.success(f"📌 Dashboard travado em: {MES_PRESENTE}")

    # FILTRO DO PRESENTE: (Ativado em Março OU Sem data) E NÃO Cancelado
    mask_presente = (
        (df['tipo de contratação'].str.contains('NOVO|ADITIVO', case=False, na=False)) &
        (df['fila atual'].str.upper() != 'CANCELADO') &
        ((df['mes_ref_ativa'] == MES_PRESENTE) | (df['data de ativação'].isna()))
    )
    
    df_f = df[mask_presente & (df['parceiro'].isin(parc_sel))]

    st.markdown(f"<div class='header-premium'><h1>🚀 PAINEL DE VENDAS CORPORATE</h1><div>📅 Período: {MES_PRESENTE}</div></div>", unsafe_allow_html=True)
    
    # META: Apenas Ativados em Março
    df_meta = df_f[df_f['mes_ref_ativa'] == MES_PRESENTE]
    v_real, r_real = df_meta['acessos'].sum(), df_meta['preço oferta'].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Volume Ativado", f"{int(v_real)} / 626", f"{(v_real/626):.1%}")
    m2.metric("Receita Ativa", f"R$ {r_real:,.2f} / R$ 21,760.00", f"{(r_real/21760):.1%}")

    st.divider()
    
    filas = [{"t":"PENDENTE","s":["PRÉ-VENDA"],"c":"header-pendente"},{"t":"ANÁLISE","s":["EM ANÁLISE","CRÉDITO"],"c":"header-analise"},{"t":"DEVOLVIDOS","s":["DEVOLVIDOS"],"c":"header-devolvido"},{"t":"ENTRANTES","s":["ENTRANTE"],"c":"header-entrante"}]
    cols = st.columns(4)
    for i, f in enumerate(filas):
        with cols[i]:
            df_fila = df_f[df_f['status_dash'].isin(f["s"])]
            st.markdown(f"<div class='column-header {f['c']}'>{f['t']}</div>", unsafe_allow_html=True)
            with st.expander(f"Σ {int(df_fila['acessos'].sum())} | R$ {df_fila['preço oferta'].sum():,.2f}", expanded=True):
                if not df_fila.empty:
                    st.dataframe(df_fila.groupby('razão social')[['acessos', 'preço oferta']].sum().reset_index().rename(columns={'acessos':'GROSS'}), hide_index=True)