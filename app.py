import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os

st.set_page_config(page_title="TIM | Vendas Corporate", layout="wide", page_icon="🎯")

# 1. MAPEAMENTO TÉCNICO ATUALIZADO (Conforme image_b81348.png)
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
    'REANÁLISE APROVADA': 'CRÉDITO', 'REANÁLISE DE CRÉDITO': 'CRÉDITO',
    'CADASTRO': 'PRÉ-VENDA', 'AG. ACEITE DIGITAL': 'PRÉ-VENDA',
    'DEVOLVIDOS': 'DEVOLVIDOS', 'FALTA APARELHO - TERMINAIS': 'DEVOLVIDOS',
    'REANÁLISE REPROVADA': 'DEVOLVIDOS', 'CANCELADO': 'CANCELADO'
}

# CSS (Mantido o padrão premium)
st.markdown("<style>.stApp { background-color: #0E1117; } .header-premium { background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 25px; } .column-header { padding: 10px; border-radius: 8px 8px 0 0; text-align: center; font-weight: bold; color: white; font-size: 14px; text-transform: uppercase; } .header-pendente { background-color: #6366F1; } .header-analise { background-color: #F59E0B; } .header-devolvido { background-color: #EF4444; } .header-entrante { background-color: #10B981; }</style>", unsafe_allow_html=True)

# DADOS
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)
mes_atual_alvo = agora.strftime('%m/%Y')

arquivos_locais = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]

if arquivos_locais:
    dfs = [pd.read_excel(b).rename(columns=lambda x: x.strip().lower()) for b in arquivos_locais]
    df = pd.concat(dfs, ignore_index=True)
    
    df['acessos'] = pd.to_numeric(df['acessos'], errors='coerce').fillna(0)
    df['preço oferta'] = pd.to_numeric(df['preço oferta'], errors='coerce').fillna(0)
    df['status_dash'] = df['fila atual'].str.strip().str.upper().map(MAP_STATUS).fillna('OUTROS')
    df['data de ativação'] = pd.to_datetime(df['data de ativação'], errors='coerce')
    df['data de input'] = pd.to_datetime(df['data de input'], errors='coerce')
    df['mes_ref_ativa'] = df['data de ativação'].dt.strftime('%m/%Y')
    df['mes_ref_input'] = df['data de input'].dt.strftime('%m/%Y')

    with st.sidebar:
        st.title("Gestão de Vendas")
        lista_parceiros = sorted(df['parceiro'].dropna().unique().tolist())
        parc_sel = st.multiselect("Parceiros", lista_parceiros, default=lista_parceiros)
        
        # FILTRO DE DATA LIMPO (Apenas meses reais)
        meses_reais = sorted(list(set(df['mes_ref_ativa'].dropna().unique()) | set(df['mes_ref_input'].dropna().unique())), reverse=True)
        mes_sel = st.selectbox("Mês de Análise", meses_reais, index=meses_reais.index(mes_atual_alvo) if mes_atual_alvo in meses_reais else 0)

    # HEADER E METAS (Novo/Aditivo)
    st.markdown(f"<div class='header-premium'><h1>🚀 PAINEL DE VENDAS CORPORATE</h1><div style='margin-top:10px;'>📅 Safra: {mes_sel}</div></div>", unsafe_allow_html=True)
    
    # Meta fixa: 626 / 21760
    df_meta = df[(df['mes_ref_ativa'] == mes_sel) & (df['tipo de contratação'].str.contains('NOVO|ADITIVO', case=False, na=False)) & (df['status_dash'] != 'CANCELADO')]
    v_real, r_real = df_meta['acessos'].sum(), df_meta['preço oferta'].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Volume Ativo", f"{int(v_real)} / 626", f"{(v_real/626):.1%}")
    m2.metric("Receita Ativa", f"R$ {r_real:,.2f} / R$ 21,760.00", f"{(r_real/21760):.1%}")

    # KANBAN SAFRA + PIPELINE
    st.divider()
    # REGRA: Ativado no mês OU (Sem data AND Input no mês) E não cancelado
    mask_kanban = (
        (df['mes_ref_ativa'] == mes_sel) | 
        (df['data de ativação'].isna() & (df['mes_ref_input'] == mes_sel))
    ) & (df['status_dash'] != 'CANCELADO') & (df['tipo de contratação'].str.contains('NOVO|ADITIVO', case=False, na=False))
    
    df_f = df[mask_kanban & (df['parceiro'].isin(parc_sel))]
    
    filas = [{"t": "PENDENTE", "s": ["PRÉ-VENDA"]}, {"t": "ANÁLISE", "s": ["EM ANÁLISE", "CRÉDITO"]}, {"t": "DEVOLVIDOS", "s": ["DEVOLVIDOS"]}, {"t": "ENTRANTES", "s": ["ENTRANTE"]}]
    cols = st.columns(4)
    for i, f in enumerate(filas):
        with cols[i]:
            df_fila = df_f[df_f['status_dash'].isin(f["s"])]
            st.markdown(f"<div class='column-header header-{f['t'].lower()}'>{f['t']}</div>", unsafe_allow_html=True)
            with st.expander(f"Σ {int(df_fila['acessos'].sum())} | R$ {df_fila['preço oferta'].sum():,.2f}", expanded=True):
                if not df_fila.empty:
                    st.dataframe(df_fila.groupby('razão social')[['acessos', 'preço oferta']].sum().reset_index().rename(columns={'acessos':'GROSS'}), hide_index=True)
else:
    st.warning("Aguardando bases...")