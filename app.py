import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="TIM | Intelligence & Metas", layout="wide", page_icon="📊")

# 2. CSS PREMIUM
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .header-premium {
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 20px; border-radius: 15px; color: white; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 20px;
    }
    .update-tag {
        background-color: rgba(255,255,255,0.2);
        padding: 4px 10px; border-radius: 20px; font-size: 0.8em;
        display: inline-block; margin-top: 10px;
    }
    .kpi-card {
        background-color: #1A1C23; padding: 15px; border-radius: 12px;
        border: 1px solid #2D2E3A; text-align: center;
    }
    .column-header {
        padding: 8px; border-radius: 8px 8px 0 0; text-align: center;
        font-weight: bold; color: white; font-size: 13px;
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

# 4. METAS CORPORATE (Mantém 626 / 21.760 até que você mude manualmente)
meta_vol = 626.0
meta_rec = 21760.0

# 5. LÓGICA DE DADOS E DATA ATUAL
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)
mes_atual_str = agora.strftime('%m/%Y') # Ex: "03/2026"

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/TIM_logo.svg/1200px-TIM_logo.svg.png", width=80)
    st.title("Gestão de Dados")
    arquivos_manuais = st.file_uploader("Upload Manual", type=['xlsx'], accept_multiple_files=True)
    
    bases_finais = []
    origem_dados, data_upload = "", ""

    if arquivos_manuais:
        bases_finais = arquivos_manuais
        origem_dados = "Upload Manual"
        data_upload = agora.strftime('%d/%m/%Y às %H:%M:%S')
    else:
        arquivos_locais = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]
        if arquivos_locais:
            bases_finais = arquivos_locais
            origem_dados = "GitHub (Auto)"
            mod_time = os.path.getmtime(arquivos_locais[0])
            data_upload = datetime.fromtimestamp(mod_time, fuso_br).strftime('%d/%m/%Y às %H:%M:%S')

if bases_finais:
    lista_dfs = [pd.read_excel(b).rename(columns=lambda x: x.strip().lower()) for b in bases_finais]
    df = pd.concat(lista_dfs, ignore_index=True)
    
    # Tratamentos básicos
    col_input, col_ativ, col_vendedor, col_tipo = 'data de input', 'data de ativação', 'responsável venda', 'tipo de contratação'
    df['acessos'] = pd.to_numeric(df['acessos'], errors='coerce').fillna(0)
    df['preço oferta'] = pd.to_numeric(df['preço oferta'], errors='coerce').fillna(0)
    df['status_dash'] = df['fila atual'].map(MAP_STATUS).fillna('OUTROS')
    df[col_input] = pd.to_datetime(df[col_input], errors='coerce')
    df[col_ativ] = pd.to_datetime(df[col_ativ], errors='coerce')
    df['mes_ref'] = df[col_ativ].dt.strftime('%m/%Y')

    with st.sidebar:
        # Lógica para o Mês de Referência abrir no mês ATUAL automaticamente
        meses_disponiveis = sorted(df['mes_ref'].dropna().unique().tolist(), reverse=True)
        
        # Se o mês atual estiver na base, ele é o padrão. Se não, pega o primeiro da lista.
        idx_padrao = meses_disponiveis.index(mes_atual_str) if mes_atual_str in meses_disponiveis else 0
        mes_sel = st.selectbox("Mês de Análise", meses_disponiveis, index=idx_padrao)
        
        parc_sel = st.multiselect("Parceiros", sorted(df['parceiro'].unique()), default=df['parceiro'].unique())
        
        st.divider()
        opcao_visao = st.radio("Visão Operacional:", ["Produtividade (NOVO/ADITIVO)", "Apenas RENEGOCIAÇÃO"])
        tipo_sel_operacional = ["NOVO", "ADITIVO"] if "Produtividade" in opcao_visao else ["RENEGOCIAÇÃO"]
        st.success(f"📌 {origem_dados}\n🕒 {data_upload}")

    # 6. HEADER
    st.markdown(f"<div class='header-premium'><h2>{mes_sel} - SMB PB</h2><div class='update-tag'>🕒 {origem_dados}: {data_upload}</div></div>", unsafe_allow_html=True)

    # 7. METAS (Fixas conforme solicitado)
    st.markdown("### 🎯 Atingimento Carta Meta (Corporate)")
    df_meta = df[(df['mes_ref'] == mes_sel) & (df[col_tipo].str.upper().isin(['ADITIVO', 'NOVO'])) & (df['status_dash'] != 'CANCELADO')].copy()
    real_vol, real_rec = df_meta['acessos'].sum(), df_meta['preço oferta'].sum()

    m1, m2 = st.columns(2)
    with m1:
        st.metric("Volume Ativo (Acessos)", f"{int(real_vol)} / {int(meta_vol)}", f"{(real_vol/meta_vol):.1%}")
        st.progress(min(real_vol/meta_vol, 1.0))
    with m2:
        st.metric("Receita Ativa (Preço Oferta)", f"R$ {real_rec:,.2f} / R$ {meta_rec:,.2f}", f"{(real_rec/meta_rec):.1%}")
        st.progress(min(real_rec/meta_rec, 1.0))

    # 8. KANBAN
    st.divider()
    # Mask para o Kanban: mostramos o que é do mês OU o que ainda não ativou (esteja em fila)
    mask_op = (df['mes_ref'] == mes_sel) | ((df[col_ativ].isna()) & (df['status_dash'] != 'CANCELADO'))
    df_f = df[mask_op & (df['parceiro'].isin(parc_sel)) & (df[col_tipo].str.upper().isin(tipo_sel_operacional))].copy()

    st.subheader(f"📊 Fluxo de Tramitação: {opcao_visao}")
    filas = [{"t": "PENDENTE", "s": ["PRÉ-VENDA"], "cls": "header-pendente"}, {"t": "ANÁLISE", "s": ["EM ANÁLISE", "CRÉDITO"], "cls": "header-analise"}, {"t": "DEVOLVIDOS", "s": ["DEVOLVIDOS"], "cls": "header-devolvido"}, {"t": "ENTRANTES", "s": ["ENTRANTE"], "cls": "header-entrante"}]
    cols = st.columns(4)
    for i, f in enumerate(filas):
        with cols[i]:
            df_fila = df_f[df_f['status_dash'].isin(f["s"])]
            st.markdown(f"<div class='column-header {f['cls']}'>{f['t']}</div>", unsafe_allow_html=True)
            with st.expander(f"Σ {int(df_fila['acessos'].sum())} | R$ {df_fila['preço oferta'].sum():,.2f}", expanded=True):
                if not df_fila.empty:
                    res = df_fila.groupby('razão social').agg({'acessos':'sum', 'preço oferta':'sum'}).reset_index().sort_values('acessos', ascending=False)
                    st.dataframe(res.rename(columns={'acessos':'GROSS', 'preço oferta':'R$'}), hide_index=True)

    # 9. CALENDÁRIO
    st.divider()
    st.subheader(f"🗓️ Produtividade Diária: {opcao_visao}")
    df_liq = df_f[df_f['status_dash'] != 'CANCELADO'].copy()
    if not df_liq.empty:
        df_liq['dia'] = df_liq[col_input].dt.day
        cal = df_liq.pivot_table(index=col_vendedor, columns='dia', values='acessos', aggfunc='sum').fillna(0)
        cal['Total'] = cal.sum(axis=1)
        def style_cal(val):
            if val > 0: return 'background-color: #064E3B; color: #10B981; font-weight: bold;'
            return 'background-color: #450A0A; color: #EF4444; opacity: 0.3;'
        st.dataframe(cal.sort_values('Total', ascending=False).style.applymap(style_cal, subset=pd.IndexSlice[:, cal.columns != 'Total']).format(precision=0), use_container_width=True)
else:
    st.warning("⚠️ Aguardando bases (.xlsx) no GitHub ou Upload.")