import streamlit as st
import pandas as pd
import os
from datetime import datetime

# CONFIGURAÇÃO DE PÁGINA
st.set_page_config(page_title="TIM | Renegociação", layout="wide", page_icon="🔄")

# MAPEAMENTO DE STATUS (Conforme image_b81348.png)
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

# ESTILO VISUAL
st.markdown("""<style>.stApp { background-color: #0E1117; } .header-reneg { background: linear-gradient(90deg, #065F46 0%, #059669 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px; } .column-header { padding: 10px; border-radius: 8px 8px 0 0; text-align: center; font-weight: bold; color: white; font-size: 14px; text-transform: uppercase; } .header-pendente { background-color: #6366F1; } .header-analise { background-color: #F59E0B; } .header-devolvido { background-color: #EF4444; } .header-entrante { background-color: #10B981; }</style>""", unsafe_allow_html=True)

# TRAVA NO PRESENTE
MES_ALVO = "03/2026"

arquivos_locais = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]

if arquivos_locais:
    # LER E TRATAR BASE
    df = pd.concat([pd.read_excel(b).rename(columns=lambda x: x.strip().lower()) for b in arquivos_locais], ignore_index=True)
    df['acessos'] = pd.to_numeric(df['acessos'], errors='coerce').fillna(0)
    df['preço oferta'] = pd.to_numeric(df['preço oferta'], errors='coerce').fillna(0)
    df['status_dash'] = df['fila atual'].str.strip().str.upper().map(MAP_STATUS).fillna('OUTROS')
    
    # TRATAR DATAS
    df['data de ativação'] = pd.to_datetime(df['data de ativação'], errors='coerce')
    df['mes_ref_ativa'] = df['data de ativação'].dt.strftime('%m/%Y')
    df['data de input'] = pd.to_datetime(df['data de input'], errors='coerce')
    df['mes_ref_input'] = df['data de input'].dt.strftime('%m/%Y')

    with st.sidebar:
        parc_sel = st.multiselect("Parceiros", sorted(df['parceiro'].dropna().unique()), default=df['parceiro'].dropna().unique())
        st.success(f"Renegociação: Safra {MES_ALVO}")

    # FILTRO RIGOROSO RENEG: Tipo RENEG + Não Cancelado + (Ativo em Março OU Vazio com Input em Março)
    mask_reneg = (
        (df['tipo de contratação'].str.contains('RENEG', case=False, na=False)) &
        (df['fila atual'].str.upper() != 'CANCELADO') &
        (df['parceiro'].isin(parc_sel)) &
        ((df['mes_ref_ativa'] == MES_ALVO) | (df['data de ativação'].isna() & (df['mes_ref_input'] == MES_ALVO)))
    )
    
    df_f = df[mask_reneg].copy()

    st.markdown(f"<div class='header-reneg'><h1>🔄 GESTÃO DE RENEGOCIAÇÕES</h1><div>📅 Período: {MES_ALVO}</div></div>", unsafe_allow_html=True)
    
    # ATINGIMENTO RENEG (Apenas Ativados Março)
    df_meta = df_f[df_f['mes_ref_ativa'] == MES_ALVO]
    v_real, r_real = df_meta['acessos'].sum(), df_meta['preço oferta'].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Volume Ativo", f"{int(v_real)} / 751")
    m2.metric("Receita Ativa", f"R$ {r_real:,.2f} / R$ 45,060.00")

    st.divider()
    
    # KANBAN RENEG
    filas = [{"t":"PENDENTE","s":["PRÉ-VENDA"],"c":"header-pendente"},{"t":"ANÁLISE","s":["EM ANÁLISE","CRÉDITO"],"c":"header-analise"},{"t":"DEVOLVIDOS","s":["DEVOLVIDOS"],"c":"header-devolvido"},{"t":"ENTRANTES","s":["ENTRANTE"],"c":"header-entrante"}]
    cols = st.columns(4)
    for i, f in enumerate(filas):
        with cols[i]:
            df_fila = df_f[df_f['status_dash'].isin(f["s"])]
            st.markdown(f"<div class='column-header {f['c']}'>{f['t']}</div>", unsafe_allow_html=True)
            with st.expander(f"Σ {int(df_fila['acessos'].sum())} | R$ {df_fila['preço oferta'].sum():,.2f}", expanded=True):
                if not df_fila.empty:
                    st.dataframe(df_fila.groupby('razão social')[['acessos', 'preço oferta']].sum().reset_index().rename(columns={'acessos':'GROSS'}), hide_index=True)
else:
    st.info("Aguardando dados de Renegociação para Março/2026...")