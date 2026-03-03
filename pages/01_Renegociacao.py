import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="TIM | Renegociação", layout="wide", page_icon="🔄")

# 2. CSS PREMIUM (Verde para Renegociação)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .header-reneg {
        background: linear-gradient(90deg, #065F46 0%, #059669 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 25px;
    }
    .update-tag {
        background-color: rgba(255,255,255,0.2);
        padding: 4px 12px; border-radius: 20px; font-size: 0.85em;
        display: inline-block; margin-top: 10px; border: 1px solid rgba(255,255,255,0.3);
    }
    .column-header {
        padding: 10px; border-radius: 8px 8px 0 0; text-align: center;
        font-weight: bold; color: white; font-size: 14px; text-transform: uppercase;
    }
    .header-pendente { background-color: #6366F1; }
    .header-analise { background-color: #F59E0B; }
    .header-devolvido { background-color: #EF4444; }
    .header-entrante { background-color: #10B981; }
    </style>
    """, unsafe_allow_html=True)

# 3. MAPEAMENTO DE STATUS
MAP_STATUS = {
    'CANCELADO': 'CANCELADO', 'DEVOLVIDOS': 'DEVOLVIDOS', 'FALTA APARELHO - TERMINAIS': 'DEVOLVIDOS',
    'REANÁLISE REPROVADA': 'DEVOLVIDOS', 'CONCLUÍDO': 'ENTRANTE', 'ENTREGA': 'ENTRANTE',
    'FIDELIZAÇÃO': 'ENTRANTE', 'AG. IMPR. DOCs/EXPEDIÇÃO': 'ENTRANTE', 'INCONSISTENCIA': 'ENTRANTE',
    'INSUCESSO VENDAS': 'ENTRANTE', 'PRÉ-ATIVAÇÃO-P2B': 'ENTRANTE', 'BATE/VOLTA - LOG': 'ENTRANTE',
    'FATURAMENTO': 'ENTRANTE', 'DOCUMENTAÇÃO': 'ENTRANTE', 'AG. ANALISE ANTI-FRAUDE': 'EM ANÁLISE',
    'ANÁLISE DE CADASTRO - CRÉDITO': 'CRÉDITO', 'CADASTRO': 'PRÉ-VENDA', 'AG. ACEITE DIGITAL': 'PRÉ-VENDA',
    'COMPROMISSO': 'META', 'AG. STATUS P2B': 'EM ANÁLISE', 'AG. ATIVAÇÃO': 'ENTRANTE', 
    'REANÁLISE APROVADA': 'CRÉDITO', 'REANÁLISE DE CRÉDITO': 'CRÉDITO', 'APROVAÇÃO P2B': 'EM ANÁLISE'
}

# 4. CÁLCULO DAS METAS RENEG (120% de 626 e TKM 60)
meta_vol_reneg = 626.0 * 1.2
meta_rec_reneg = meta_vol_reneg * 60.0

# 5. LÓGICA DE DADOS
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)
mes_atual_alvo = agora.strftime('%m/%Y')

arquivos_locais = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]

if arquivos_locais:
    dfs = [pd.read_excel(b).rename(columns=lambda x: x.strip().lower()) for b in arquivos_locais]
    df = pd.concat(dfs, ignore_index=True)
    
    # Tratamentos
    df['acessos'] = pd.to_numeric(df['acessos'], errors='coerce').fillna(0)
    df['preço oferta'] = pd.to_numeric(df['preço oferta'], errors='coerce').fillna(0)
    df['status_dash'] = df['fila atual'].map(MAP_STATUS).fillna('OUTROS')
    df['data de ativação'] = pd.to_datetime(df['data de ativação'], errors='coerce')
    df['mes_ref_ativa'] = df['data de ativação'].dt.strftime('%m/%Y')

    with st.sidebar:
        st.title("Filtros Reneg")
        lista_parceiros = sorted(df['parceiro'].dropna().unique().tolist())
        parc_sel = st.multiselect("Filtrar Parceiros", lista_parceiros, default=lista_parceiros)
        
        lista_meses = sorted(df['mes_ref_ativa'].dropna().unique().tolist(), reverse=True)
        idx_mes = lista_meses.index(mes_atual_alvo) if mes_atual_alvo in lista_meses else 0
        mes_sel = st.selectbox("Mês de Análise", lista_meses, index=idx_mes)

    # 6. HEADER
    st.markdown(f"<div class='header-reneg'><h1>🔄 GESTÃO DE RENEGOCIAÇÕES</h1><div class='update-tag'>📅 Ref: {mes_sel}</div></div>", unsafe_allow_html=True)

    # 7. METAS RENEG
    st.markdown("### 🎯 Atingimento da Meta de Renegociação")
    df_meta = df[(df['mes_ref_ativa'] == mes_sel) & (df['tipo de contratação'].str.upper() == 'RENEGOCIAÇÃO') & (df['status_dash'] != 'CANCELADO')].copy()
    v_real, r_real = df_meta['acessos'].sum(), df_meta['preço oferta'].sum()
    
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Volume Ativo (Reneg)", f"{int(v_real)} / {int(meta_vol_reneg)}", f"{(v_real/meta_vol_reneg):.1%}")
        st.progress(min(v_real/meta_vol_reneg, 1.0))
    with m2:
        st.metric("Receita Ativa (Reneg)", f"R$ {r_real:,.2f} / R$ {meta_rec_reneg:,.2f}", f"{(r_real/meta_rec_reneg):.1%}")
        st.progress(min(r_real/meta_rec_reneg, 1.0))

    # 8. KANBAN RENEG
    st.divider()
    mask_kanban = (df['mes_ref_ativa'] == mes_sel) | ((df['data de ativação'].isna()) & (df['status_dash'] != 'CANCELADO'))
    df_f = df[mask_kanban & (df['parceiro'].isin(parc_sel)) & (df['tipo de contratação'].str.upper() == 'RENEGOCIAÇÃO')].copy()

    st.subheader(f"📊 Fluxo de Tramitação: Renegociações {mes_sel}")
    filas = [{"t": "PENDENTE", "s": ["PRÉ-VENDA"], "cls": "header-pendente"}, {"t": "ANÁLISE", "s": ["EM ANÁLISE", "CRÉDITO"], "cls": "header-analise"}, {"t": "DEVOLVIDOS", "s": ["DEVOLVIDOS"], "cls": "header-devolvido"}, {"t": "ENTRANTES", "s": ["ENTRANTE"], "cls": "header-entrante"}]
    cols = st.columns(4)
    for i, f in enumerate(filas):
        with cols[i]:
            df_fila = df_f[df_f['status_dash'].isin(f["s"])]
            st.markdown(f"<div class='column-header {f['cls']}'>{f['t']}</div>", unsafe_allow_html=True)
            with st.expander(f"Σ {int(df_fila['acessos'].sum())} | R$ {df_fila['preço oferta'].sum():,.2f}"):
                if not df_fila.empty:
                    res = df_fila.groupby('razão social').agg({'acessos':'sum', 'preço oferta':'sum'}).reset_index().sort_values('acessos', ascending=False)
                    st.dataframe(res.rename(columns={'acessos':'GROSS', 'preço oferta':'R$'}), hide_index=True)