import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import os

# 1. CONFIGURAÇÃO DA PÁGINA (Ícone de dinheiro para Vendas)
st.set_page_config(page_title="TIM | Vendas Corporate", layout="wide", page_icon="💰")

# 2. CSS PREMIUM (UI/UX)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .header-premium {
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 25px;
    }
    .update-tag {
        background-color: rgba(255,255,255,0.2);
        padding: 4px 12px; border-radius: 20px; font-size: 0.85em;
        display: inline-block; margin-top: 10px; border: 1px solid rgba(255,255,255,0.3);
    }
    .kpi-card {
        background-color: #1A1C23; padding: 20px; border-radius: 12px;
        border: 1px solid #2D2E3A; text-align: center;
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

# 4. METAS CORPORATE FIXAS (626 / 21.760)
meta_vol_fixa = 626.0
meta_rec_fixa = 21760.0

# 5. LÓGICA DE DADOS
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)
mes_atual_alvo = agora.strftime('%m/%Y')

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/TIM_logo.svg/1200px-TIM_logo.svg.png", width=90)
    st.title("Gestão de Dados")
    arquivos_enviados = st.file_uploader("Atualizar Bases (.xlsx)", type=['xlsx'], accept_multiple_files=True)
    
    bases_processar = []
    if arquivos_enviados:
        bases_processar = arquivos_enviados
        origem, data_up = "Upload Manual", agora.strftime('%d/%m/%Y %H:%M:%S')
    else:
        arquivos_locais = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]
        if arquivos_locais:
            bases_processar = arquivos_locais
            origem = "GitHub (Auto)"
            mod_time = os.path.getmtime(arquivos_locais[0])
            data_up = datetime.fromtimestamp(mod_time, fuso_br).strftime('%d/%m/%Y %H:%M:%S')
        else:
            origem, data_up = "", ""

if bases_processar:
    dfs = [pd.read_excel(b).rename(columns=lambda x: x.strip().lower()) for b in bases_processar]
    df = pd.concat(dfs, ignore_index=True)

    if not df.empty:
        # Tratamentos de Tipagem e Nulos
        df['acessos'] = pd.to_numeric(df['acessos'], errors='coerce').fillna(0)
        df['preço oferta'] = pd.to_numeric(df['preço oferta'], errors='coerce').fillna(0)
        df['status_dash'] = df['fila atual'].map(MAP_STATUS).fillna('OUTROS')
        df['data de ativação'] = pd.to_datetime(df['data de ativação'], errors='coerce')
        df['data de input'] = pd.to_datetime(df['data de input'], errors='coerce')
        df['mes_ref_ativa'] = df['data de ativação'].dt.strftime('%m/%Y')
        df['mes_ref_input'] = df['data de input'].dt.strftime('%m/%Y')

        with st.sidebar:
            lista_parceiros = sorted(df['parceiro'].dropna().unique().tolist())
            parc_sel = st.multiselect("Filtrar Parceiros", lista_parceiros, default=lista_parceiros)
            
            lista_meses = sorted(df['mes_ref_ativa'].dropna().unique().tolist(), reverse=True)
            idx_mes = lista_meses.index(mes_atual_alvo) if mes_atual_alvo in lista_meses else 0
            mes_sel = st.selectbox("Mês de Análise", lista_meses, index=idx_mes)
            st.success(f"📌 {origem}\n🕒 {data_up}")

        # 6. HEADER
        st.markdown(f"""
            <div class='header-premium'>
                <h1>🚀 PAINEL DE VENDAS CORPORATE</h1>
                <div class='update-tag'>📅 Ref: {mes_sel} | 🕒 Atualizado: {data_up} via {origem}</div>
            </div>
        """, unsafe_allow_html=True)

        # 7. METAS (Apenas NOVO/ADITIVO para Março 2026)
        st.markdown("### 🎯 Atingimento Carta Meta")
        df_meta = df[(df['mes_ref_ativa'] == mes_sel) & 
                    (df['tipo de contratação'].str.upper().isin(['ADITIVO', 'NOVO'])) & 
                    (df['status_dash'] != 'CANCELADO')].copy()
        
        v_real, r_real = df_meta['acessos'].sum(), df_meta['preço oferta'].sum()
        
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Volume Ativo (Acessos)", f"{int(v_real)} / {int(meta_vol_fixa)}", f"{(v_real/meta_vol_fixa):.1%}")
            st.progress(min(v_real/meta_vol_fixa, 1.0))
        with m2:
            st.metric("Receita Ativa (Preço Oferta)", f"R$ {r_real:,.2f} / R$ {meta_rec_fixa:,.2f}", f"{(r_real/meta_rec_fixa):.1%}")
            st.progress(min(r_real/meta_rec_fixa, 1.0))

        # 8. KANBAN (Tramitação de Vendas)
        st.divider()
        mask_kanban = (df['mes_ref_ativa'] == mes_sel) | ((df['data de ativação'].isna()) & (df['status_dash'] != 'CANCELADO'))
        df_f = df[mask_kanban & (df['parceiro'].isin(parc_sel)) & (df['tipo de contratação'].str.upper().isin(['NOVO', 'ADITIVO']))].copy()

        st.subheader("📊 Fluxo de Tramitação (Novo/Aditivo)")
        filas = [
            {"t": "PENDENTE", "s": ["PRÉ-VENDA"], "cls": "header-pendente"},
            {"t": "ANÁLISE", "s": ["EM ANÁLISE", "CRÉDITO"], "cls": "header-analise"},
            {"t": "DEVOLVIDOS", "s": ["DEVOLVIDOS"], "cls": "header-devolvido"},
            {"t": "ENTRANTES", "s": ["ENTRANTE"], "cls": "header-entrante"}
        ]
        cols = st.columns(4)
        for i, f in enumerate(filas):
            with cols[i]:
                df_fila = df_f[df_f['status_dash'].isin(f["s"])]
                st.markdown(f"<div class='column-header {f['cls']}'>{f['t']}</div>", unsafe_allow_html=True)
                with st.expander(f"Σ {int(df_fila['acessos'].sum())} | R$ {df_fila['preço oferta'].sum():,.2f}", expanded=True):
                    if not df_fila.empty:
                        res = df_fila.groupby('razão social').agg({'acessos':'sum', 'preço oferta':'sum'}).reset_index().sort_values('acessos', ascending=False)
                        st.dataframe(res.rename(columns={'acessos':'GROSS', 'preço oferta':'R$'}), hide_index=True, use_container_width=True)

        # 9. CALENDÁRIO DE INPUTS
        st.divider()
        st.subheader(f"🗓️ Produtividade Diária (Inputs de {mes_sel})")
        df_cal = df_f[(df_f['mes_ref_input'] == mes_sel) & (df_f['status_dash'] != 'CANCELADO')].copy()
        if not df_cal.empty:
            df_cal['dia'] = df_cal['data de input'].dt.day.astype(int)
            cal = df_cal.pivot_table(index='responsável venda', columns='dia', values='acessos', aggfunc='sum').fillna(0)
            cal['Total'] = cal.sum(axis=1)
            def style_cal(val):
                if val > 0: return 'background-color: #064E3B; color: #10B981; font-weight: bold;'
                return 'background-color: #450A0A; color: #EF4444; opacity: 0.3;'
            st.dataframe(cal.sort_values('Total', ascending=False).style.applymap(style_cal, subset=pd.IndexSlice[:, cal.columns != 'Total']).format(precision=0), use_container_width=True)
        else:
            st.info(f"Nenhum input registrado para {mes_sel}")
else:
    st.warning("⚠️ Nenhuma base encontrada no GitHub. Por favor, faça o upload das planilhas.")