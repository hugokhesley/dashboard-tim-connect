import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

st.set_page_config(page_title="TIM | Vendas Corporate", layout="wide", page_icon="🎯")

# 1. MAPEAMENTO TÉCNICO (image_b81348.png)
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

fuso_br = pytz.timezone('America/Sao_Paulo')
mes_atual = datetime.now(fuso_br).strftime('%m/%Y')

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
        meses_reais = sorted(df['mes_ref_ativa'].dropna().unique().tolist(), reverse=True)
        if mes_atual not in meses_reais: meses_reais.insert(0, mes_atual)
        mes_sel = st.selectbox("Mês de Análise", meses_reais, index=meses_reais.index(mes_atual) if mes_atual in meses_reais else 0)

    st.markdown(f"<div class='header-premium'><h1>🚀 PAINEL DE VENDAS CORPORATE</h1><div>📅 Safra: {mes_sel}</div></div>", unsafe_allow_html=True)
    
    # 🎯 BARRA DE META: Apenas o que ativou no mês de análise
    df_meta = df[(df['mes_ref_ativa'] == mes_sel) & (df['tipo de contratação'].str.contains('NOVO|ADITIVO', case=False, na=False)) & (df['fila atual'].str.upper() != 'CANCELADO')]
    v_real, r_real = df_meta['acessos'].sum(), df_meta['preço oferta'].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Volume Ativo", f"{int(v_real)} / 626", f"{(v_real/626):.1%}")
    m2.metric("Receita Ativa", f"R$ {r_real:,.2f} / R$ 21,760.00", f"{(r_real/21760):.1%}")

    st.divider()
    
    # 📊 KANBAN (A LÓGICA EXCEL): Ativados no Mês Selecionado + Vazios (Backlog)
    # TRAVA: Remove ativações de outros meses que não sejam o 'mes_sel'
    mask_safra = (df['mes_ref_ativa'] == mes_sel) | (df['data de ativação'].isna())
    mask_base = (df['fila atual'].str.upper() != 'CANCELADO') & (df['tipo de contratação'].str.contains('NOVO|ADITIVO', case=False, na=False))
    
    df_f = df[mask_safra & mask_base & (df['parceiro'].isin(parc_sel))]

    filas = [{"t":"PENDENTE","s":["PRÉ-VENDA"],"c":"header-pendente"},{"t":"ANÁLISE","s":["EM ANÁLISE","CRÉDITO"],"c":"header-analise"},{"t":"DEVOLVIDOS","s":["DEVOLVIDOS"],"c":"header-devolvido"},{"t":"ENTRANTES","s":["ENTRANTE"],"c":"header-entrante"}]
    cols = st.columns(4)
    for i, f in enumerate(filas):
        with cols[i]:
            df_fila = df_f[df_f['status_dash'].isin(f["s"])]
            st.markdown(f"<div class='column-header {f['c']}'>{f['t']}</div>", unsafe_allow_html=True)
            with st.expander(f"Σ {int(df_fila['acessos'].sum())} | R$ {df_fila['preço oferta'].sum():,.2f}", expanded=True):
                if not df_fila.empty:
                    st.dataframe(df_fila.groupby('razão social')[['acessos', 'preço oferta']].sum().reset_index().rename(columns={'acessos':'GROSS'}), hide_index=True)