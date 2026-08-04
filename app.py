import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(
    page_title="Gestão de Notas Esporádicas",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Painel de Gestão de Notas Esporádicas")
st.markdown("Painel interativo para monitoramento, análise de status e prioridades das notas de manutenção.")

# Painel Lateral para Upload e Filtros
st.sidebar.header("📁 Fonte de Dados")
uploaded_file = st.sidebar.file_uploader("Carregar planilha (Excel ou CSV)", type=["xlsx", "xls", "csv"])

# Função para carregar os dados (com suporte a dados padrão caso nenhum arquivo seja enviado)
@st.cache_data
def load_data(file):
    if file is not None:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    else:
        # Dados de exemplo para demonstração inicial e testes no Streamlit Cloud
        data = {
            "Nota": [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008],
            "Descrição": [
                "Vibração Anormal - Bomba PU152B", "Troca de Rolamento Motor", 
                "Vazamento de Óleo Redutor", "Inspeção Elétrica Painel", 
                "Revisão de Válvula de Controle", "Correção de Alinhamento", 
                "Substituição de Correia Ventilador", "Calibração de Instrumento"
            ],
            "Status": ["Aberta", "Concluída", "Em Andamento", "Aberta", "Concluída", "Aberta", "Em Andamento", "Concluída"],
            "Prioridade": ["Alta", "Média", "Urgente", "Baixa", "Média", "Alta", "Urgente", "Baixa"],
            "Data": pd.date_range(start="2026-01-01", periods=8, freq="W"),
            "Responsável": ["Carlos", "João", "Maria", "Carlos", "Ana", "João", "Maria", "Ana"]
        }
        return pd.DataFrame(data)

df = load_data(uploaded_file)

# Conversão da coluna de data se existir
if "Data" in df.columns:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# Filtros na Barra Lateral
st.sidebar.header("🔍 Filtros")
if "Status" in df.columns:
    status_options = df["Status"].dropna().unique().tolist()
    selected_status = st.sidebar.multiselect("Filtrar por Status", status_options, default=status_options)
    if selected_status:
        df_filtered = df[df["Status"].isin(selected_status)]
    else:
        df_filtered = df
else:
    df_filtered = df

if "Prioridade" in df.columns:
    prio_options = df["Prioridade"].dropna().unique().tolist()
    selected_prio = st.sidebar.multiselect("Filtrar por Prioridade", prio_options, default=prio_options)
    if selected_prio:
        df_filtered = df_filtered[df_filtered["Prioridade"].isin(selected_prio)]

# Exibição de Métricas Principais (KPIs)
st.markdown("### 📌 Indicadores Gerais")
col1, col2, col3, col4 = st.columns(4)

total_notas = len(df_filtered)
abertas = len(df_filtered[df_filtered["Status"] == "Aberta"]) if "Status" in df_filtered.columns else 0
em_andamento = len(df_filtered[df_filtered["Status"] == "Em Andamento"]) if "Status" in df_filtered.columns else 0
concluidas = len(df_filtered[df_filtered["Status"] == "Concluída"]) if "Status" in df_filtered.columns else 0

col1.metric("Total de Notas", total_notas)
col2.metric("Abertas", abertas)
col3.metric("Em Andamento", em_andamento)
col4.metric("Concluídas", concluidas)

st.markdown("---")

# Seção de Gráficos
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Distribuição por Status")
    if "Status" in df_filtered.columns and not df_filtered.empty:
        status_counts = df_filtered["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        fig_status = px.pie(
            status_counts, 
            names="Status", 
            values="Quantidade", 
            hole=0.4, 
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("Sem dados suficientes para exibir o gráfico de status.")

with col_chart2:
    st.subheader("Distribuição por Prioridade")
    if "Prioridade" in df_filtered.columns and not df_filtered.empty:
        prio_counts = df_filtered["Prioridade"].value_counts().reset_index()
        prio_counts.columns = ["Prioridade", "Quantidade"]
        fig_prio = px.bar(
            prio_counts, 
            x="Prioridade", 
            y="Quantidade", 
            color="Prioridade", 
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_prio, use_container_width=True)
    else:
        st.info("Sem dados suficientes para exibir o gráfico de prioridade.")

# Gráfico de Evolução Temporal
if "Data" in df_filtered.columns and not df_filtered["Data"].isna().all():
    st.subheader("📈 Evolução Temporal das Notas")
    df_timeline = df_filtered.groupby(df_filtered["Data"].dt.to_period("M")).size().reset_index(name="Quantidade")
    df_timeline["Data"] = df_timeline["Data"].astype(str)
    fig_time = px.line(
        df_timeline, 
        x="Data", 
        y="Quantidade", 
        markers=True, 
        line_shape="spline",
        labels={"Data": "Mês/Ano", "Quantidade": "Número de Notas"}
    )
    st.plotly_chart(fig_time, use_container_width=True)

st.markdown("---")

# Tabela Detalhada de Dados
st.subheader("📋 Detalhamento dos Registros")
st.dataframe(df_filtered, use_container_width=True)
