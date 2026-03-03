import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="TIM | Intelligence & Metas", layout="wide", page_icon="📊")

# 2. CSS PREMIUM (UI/UX)
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

# 4. LÓGICA DE METAS (VOLUME = ACESSOS | RECEITA = PREÇO OFERTA)
try:
    meta_vol = st.secrets.get("META_VOL", 626.0)
    meta_rec = st.secrets.get("META_REC", 21760.0)
except Exception:
    meta_vol = 626.0
    meta_rec = 21760.0

# 5. SIDEBAR COM UPLOAD MÚLTIPLO
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/TIM_logo.svg/1200px-TIM_logo.svg.png", width=80)
    st.title("Gestão de Dados")
    
    # Habilitado accept_multiple_files=True
    arquivos_enviados = st.file_uploader("Upload Bases TIM (.xlsx)", type=['xlsx'], accept_multiple_files=True)
    
    fuso_br = pytz.timezone('America/Sao_Paulo')
    data_upload = datetime.now(fuso_br).strftime('%d/%m/%Y às %H:%M:%S')

if arquivos_enviados:
    lista_dfs = []
    for arquivo in arquivos_enviados:
        temp_df = pd.read_excel(arquivo)
        temp_df.columns = temp_df.columns.str.strip().str.lower()
        lista_dfs.append(temp_df)
    
    # Juntar todas as bases em uma só
    df = pd.concat(lista_dfs, ignore_index=True)
    
    # Colunas chave
    col_input, col_ativ = 'data de input', 'data de ativação'
    col_vendedor, col_tipo = 'responsável venda', 'tipo de contratação'
    
    # Tratamentos básicos
    df['acessos'] = pd.to_numeric(df['acessos'], errors='coerce').fillna(0)
    df['preço oferta'] = pd.to_numeric(df['preço oferta'], errors='coerce').fillna(0)
    df['status_dash'] = df['fila atual'].map(MAP_STATUS).fillna('OUTROS')
    df[col_input] = pd.to_datetime(df[col_input], errors='coerce')
    df[col_ativ] = pd.to_datetime(df[col_ativ], errors='coerce')
    df['mes_ref'] = df[col_ativ].dt.strftime('%m/%Y')

    with st.sidebar:
        meses = sorted([m for m in df['mes_ref'].dropna().unique()], reverse=True)
        mes_sel = st.selectbox("Mês de Análise", meses if meses else ["02/2026"])
        parc_sel = st.multiselect("Filtrar Parceiros", sorted(df['parceiro'].unique()), default=df['parceiro'].unique())
        
        tipos_disponiveis = sorted(df[col_tipo].dropna().unique().tolist())
        tipo_sel_lateral = st.multiselect("Filtro Operacional: Tipo Contratação", tipos_disponiveis, default=tipos_disponiveis)
        
        st.success(f"📌 {len(arquivos_enviados)} bases carregadas:\n{data_upload}")

    # 6. HEADER
    data_ref = df[col_input].max().date()
    data_ontem = data_ref - timedelta(days=1)
    df_hoje = df[df[col_input].dt.date == data_ref]
    df_ontem = df[df[col_input].dt.date == data_ontem]

    c_logo, c_d1, c_d0, c_title = st.columns([1, 2, 2, 4.5])
    with c_d1:
        st.markdown(f"<div class='kpi-card'><small>D-1 ({data_ontem.strftime('%d/%m')})</small><br><b>{int(df_ontem['acessos'].sum())}</b><br><small>R$ {df_ontem['preço oferta'].sum():,.2f}</small></div>", unsafe_allow_html=True)
    with c_d0:
        st.markdown(f"<div class='kpi-card'><small>IMPUTE ({data_ref.strftime('%d/%m')}) 🟢</small><br><b>{int(df_hoje['acessos'].sum())}</b><br><small>R$ {df_hoje['preço oferta'].sum():,.2f}</small></div>", unsafe_allow_html=True)
    with c_title:
        st.markdown(f"""
            <div class='header-premium'>
                <h2 style='margin:0;'>{mes_sel} - SMB PB</h2>
                <div class='update-tag'>🕒 Último Upload: {data_upload}</div>
            </div>
        """, unsafe_allow_html=True)

    # 7. SEÇÃO DE ATINGIMENTO (REGRA RÍGIDA CARTA META)
    st.markdown("### 🎯 Atingimento Carta Meta (Corporate)")
    df_meta_rigida = df[
        (df['mes_ref'] == mes_sel) & 
        (df[col_tipo].str.upper().isin(['ADITIVO', 'NOVO'])) &
        (df['status_dash'] != 'CANCELADO')
    ].copy()

    real_vol = df_meta_rigida['acessos'].sum()
    real_rec = df_meta_rigida['preço oferta'].sum()
    
    dia_atual = datetime.now(fuso_br).day if datetime.now(fuso_br).strftime('%m/%Y') == mes_sel else 28
    tendencia_vol = (real_vol / dia_atual) * 28 if dia_atual > 0 else 0

    m1, m2, m3 = st.columns(3)
    with m1:
        perc_vol = (real_vol / meta_vol)
        st.metric("Volume Ativado (Acessos)", f"{int(real_vol)} / {int(meta_vol)}", f"{perc_vol:.1%}")
        st.progress(min(perc_vol, 1.0))
    with m2:
        perc_rec = (real_rec / meta_rec)
        st.metric("Receita Ativa (Preço Oferta)", f"R$ {real_rec:,.2f} / R$ {meta_rec:,.2f}", f"{perc_rec:.1%}")
        st.progress(min(perc_rec, 1.0))
    with m3:
        cor_tend = "normal" if tendencia_vol >= meta_vol else "inverse"
        st.metric("Forecast Final (Acessos)", f"{int(tendencia_vol)} Acessos", f"{tendencia_vol - meta_vol:+.0f}", delta_color=cor_tend)

    # 8. FILAS KANBAN
    st.divider()
    mask_operacional = (df['mes_ref'] == mes_sel) | ((df[col_ativ].isna()) & (df['status_dash'] != 'CANCELADO'))
    df_f = df[mask_operacional & (df['parceiro'].isin(parc_sel)) & (df[col_tipo].isin(tipo_sel_lateral))].copy()

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
                    res = df_fila.groupby('razão social').agg({'acessos':'sum', 'preço oferta':'sum'}).reset_index()
                    res = res.sort_values('acessos', ascending=False).rename(columns={'acessos':'GROSS', 'preço oferta':'R$'})
                    res['R$'] = res['R$'].map('R$ {:,.2f}'.format)
                    st.dataframe(res, hide_index=True, use_container_width=True)

    # 9. CALENDÁRIO
    st.divider()
    st.subheader("🗓️ Produtividade Diária (Grupo Econômico)")
    df_liq = df_f[df_f['status_dash'] != 'CANCELADO'].copy()
    if not df_liq.empty:
        df_liq['dia'] = df_liq[col_input].dt.day
        cal = df_liq.pivot_table(index=col_vendedor, columns='dia', values='acessos', aggfunc='sum').fillna(0)
        cal['Total'] = cal.sum(axis=1)
        
        def style_cal(val):
            if val > 0: return 'background-color: #064E3B; color: #10B981; font-weight: bold;'
            return 'background-color: #450A0A; color: #EF4444; opacity: 0.3;'
        
        st.dataframe(cal.sort_values('Total', ascending=False).style.applymap(style_cal, subset=pd.IndexSlice[:, cal.columns != 'Total']).format(precision=0),
                     use_container_width=True, height=450)
else:
    st.info("💡 Arraste as bases dos dois parceiros simultaneamente.")