import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da Página em modo Wide
st.set_page_config(
    page_title="CMM - Centro de Monitoramento da Manutenção",
    page_icon="🏭",
    layout="wide"
)

# Estilização CSS personalizada para simular o layout corporativo
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .stButton>button { width: 100%; border-radius: 4px; font-weight: bold; }
        .metric-card { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 5px solid #1b5e20; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# CARREGAMENTO E TRATAMENTO DOS DADOS
# -------------------------------------------------------------------------
@st.cache_data
def load_data(file):
    if file is not None:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            return df
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            return None
    else:
        # Base de dados simulada robusta para manter o layout idêntico ao modelo Usiminas
        data = {
            "Agrupamento Macro": ["Manutenção Corretiva", "Preventiva", "Esporádica", "Esporádica", "Corretiva", "Preventiva", "Esporádica", "Corretiva"],
            "Área Operacional": ["LAMINAÇÃO A FRIO", "LAMINAÇÃO A QUENTE", "ENERGIA E UTILIDADES", "REDUÇÃO", "ACIARIA", "LAMINAÇÃO A FRIO", "ENERGIA E UTILIDADES", "REDUÇÃO"],
            "Processo": ["Linha de Recozimento", "Laminação 01", "Geração Vapor", "Redução I", "Conversor A", "Linha de Zinco", "Subestação Principal", "Linha 02"],
            "Sub-Processo": ["Mecânica", "Elétrica", "Caldeira", "Forno", "Hidráulica", "Mecânica", "Alta Tensão", "Automação"],
            "Código ABC": ["A", "B", "A", "C", "B", "A", "C", "B"],
            "Lista": ["Lista Principal", "Lista Parada", "Lista Extra", "Lista Principal", "Lista Parada", "Lista Extra", "Lista Principal", "Lista Parada"],
            "Status": ["Aberta", "Encerrada", "Aberta", "Aberta", "Encerrada", "Aberta", "Aberta", "Encerrada"],
            "Equipamento": ["EQP-101", "EQP-102", "EQP-103", "EQP-104", "EQP-105", "EQP-101", "EQP-106", "EQP-107"],
            "Data Criacao": pd.to_datetime(["2026-05-10", "2026-04-12", "2026-06-01", "2026-06-15", "2026-03-20", "2026-07-01", "2026-07-05", "2026-02-10"]),
            "Data Encerramento": pd.to_datetime([pd.NaT, "2026-04-18", pd.NaT, pd.NaT, "2026-03-25", pd.NaT, pd.NaT, "2026-02-15"]),
            "Ano": [2026, 2026, 2026, 2026, 2026, 2026, 2026, 2026]
        }
        return pd.DataFrame(data)

# -------------------------------------------------------------------------
# BARRA LATERAL (FILTROS DA PLANTA & SLOGAN)
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🟢 **USIMINAS**")
    st.caption("Servidor interno / CMM")
    st.markdown("---")
    
    st.header("Filtros da Planta")
    
    uploaded_file = st.file_uploader("Carregar base de dados (XLSX, CSV)", type=["xlsx", "xls", "csv"])
    df = load_data(uploaded_file)
    
    if df is not None:
        # Garantir colunas essenciais caso o usuário envie arquivo próprio
        expected_cols = ["Agrupamento Macro", "Área Operacional", "Processo", "Sub-Processo", "Código ABC", "Lista", "Status", "Equipamento"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "Não Classificado"

        # Filtros interativos
        macro_opt = st.selectbox("Filtro por AGRUPAMENTO MACRO:", ["Todos"] + list(df["Agrupamento Macro"].dropna().unique()))
        area_opt = st.selectbox("Filtro por ÁREA OPERACIONAL:", ["Todos"] + list(df["Área Operacional"].dropna().unique()))
        proc_opt = st.selectbox("Filtro por PROCESSO:", ["Todos"] + list(df["Processo"].dropna().unique()))
        subproc_opt = st.selectbox("Filtro por SUB - PROCESSO:", ["Todos"] + list(df["Sub-Processo"].dropna().unique()))
        abc_opt = st.selectbox("Filtro por Código ABC:", ["Todos"] + list(df["Código ABC"].dropna().unique()))
        lista_opt = st.selectbox("Filtro por LISTA:", ["Todos"] + list(df["Lista"].dropna().unique()))
        
        search_query = st.text_input("🔍 Pesquisa Geral (Qualquer campo):", "")
        
        st.markdown("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            aplicar = st.button("Aplicar filtros", type="primary")
        with col_b2:
            limpar = st.button("Limpar Todos")

        st.markdown("<br><p style='font-size:11px; color:gray;'>Abra a lista e marque uma ou mais opções em cada filtro.</p>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# APLICANDO FILTROS NO DATAFRAME
# -------------------------------------------------------------------------
df_filtered = df.copy()

if macro_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Agrupamento Macro"] == macro_opt]
if area_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Área Operacional"] == area_opt]
if proc_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Processo"] == proc_opt]
if subproc_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Sub-Processo"] == subproc_opt]
if abc_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Código ABC"] == abc_opt]
if lista_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Lista"] == lista_opt]

if search_query:
    mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
    df_filtered = df_filtered[mask]

# -------------------------------------------------------------------------
# CABEÇALHO PRINCIPAL E METADADOS
# -------------------------------------------------------------------------
col_title, col_btn = st.columns([6, 1])
with col_title:
    st.markdown("## 📊 CMM - Centro de Monitoramento da Manutenção")
with col_btn:
    st.button("🔗 Compartilhar Dashboard")

base_name = uploaded_file.name if uploaded_file else "Base Simulada CMM (Usiminas - Gestão M8)"
now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Base:</b> \\\\uipawa03v\\sg$\\Files\\PRD\\PB\\PB\\Gateway\\Gestão da Manutenção\\CMM - Gestão\\Equipamentos Usina.xlsx &nbsp;|&nbsp; <b>Atualizado em:</b> {now_str} &nbsp;|&nbsp; <b>Linhas filtradas:</b> {len(df_filtered):,}</p>", unsafe_allow_html=True)

# Abas superiores
tab1, tab2 = st.tabs(["INVENTÁRIO E MONITORAMENTO", "GESTÃO DE NOTAS M8"])

with tab2:
    st.markdown("### 📌 Gestão de Notas M8")
    
    # -------------------------------------------------------------------------
    # KPIS DE DESTAQUE
    # -------------------------------------------------------------------------
    col_kpi1, col_kpi2 = st.columns(2)
    
    total_abertas = len(df_filtered[df_filtered["Status"].str.lower().str.contains("aberta", na=False)])
    equip_abertas = df_filtered[df_filtered["Status"].str.lower().str.contains("aberta", na=False)]["Equipamento"].nunique()
    
    with col_kpi1:
        st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Total de Notas Abertas</p>
                <h2 style="color: #1b5e20; margin: 0; font-size: 38px;">{total_abertas}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with col_kpi2:
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; border-left-color: #0288d1;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Equip. c/ Notas Abertas</p>
                <h2 style="color: #0288d1; margin: 0; font-size: 38px;">{equip_abertas}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Controles de Visão e Ano
    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        visao = st.radio("Visão das Notas M8:", ["Notas Abertas", "Notas Criadas", "Notas Encerradas"], horizontal=True)
    with col_ctrl2:
        ano_filtro = st.selectbox("Ano:", ["Todos", "2025", "2026"])

    st.markdown("---")

    # -------------------------------------------------------------------------
    # SEÇÃO DE GRÁFICOS (ROSCA E EVOLUÇÃO HISTÓRICA)
    # -------------------------------------------------------------------------
    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        st.markdown("##### 🚨 Notas Abertas por Área (%)")
        if not df_filtered.empty:
            df_abertas = df_filtered[df_filtered["Status"].str.lower().str.contains("aberta", na=False)]
            if not df_abertas.empty:
                area_counts = df_abertas["Área Operacional"].value_counts().reset_index()
                area_counts.columns = ["Área", "Quantidade"]
                
                fig_donut = px.pie(
                    area_counts, 
                    names="Área", 
                    values="Quantidade", 
                    hole=0.5,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_donut.update_traces(textinfo="percent+label", textfont_size=12)
                fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("Nenhuma nota aberta encontrada para os filtros selecionados.")
        else:
            st.info("Sem dados disponíveis.")

    with col_chart_right:
        st.markdown("##### 📈 Evolução Histórica")
        # Criando dados simulados consistentes para o gráfico temporal de colunas e linhas
        meses = ["Sep 2025", "Nov 2025", "Jan 2026", "Mar 2026", "May 2026", "Jul 2026"]
        criadas = [76, 91, 32, 45, 118, 40]
        encerradas = [76, 31, 32, 45, 106, 37]
        abertas_hist = [0, 0, 0, 0, 2, 41]

        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(name='Notas criadas', x=meses, y=criadas, marker_color='#81c784'))
        fig_hist.add_trace(go.Bar(name='Notas encerradas', x=meses, y=encerradas, marker_color='#388e3c'))
        fig_hist.add_trace(go.Scatter(name='Notas abertas', x=meses, y=abertas_hist, mode='lines+markers', line=dict(color='#d32f2f', width=3)))

        fig_hist.update_layout(
            barmode='group',
            margin=dict(t=10, b=10, l=10, r=10),
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Tabela Detalhada de Registros M8")
    st.dataframe(df_filtered, use_container_width=True)

with tab1:
    st.markdown("### 🔍 Inventário e Monitoramento de Equipamentos")
    st.info("Painel de inventário em tempo real conectado aos ativos da usina.")
    st.dataframe(df, use_container_width=True)
