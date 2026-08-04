import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import unicodedata

# Configuração da Página em modo Wide
st.set_page_config(
    page_title="Gestão de Notas Esporádicas Redução/Energia",
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

# Função para remover acentos e padronizar textos das colunas
def normalize_text(text):
    if not isinstance(text, str):
        text = str(text)
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).upper().strip()

# -------------------------------------------------------------------------
# CARREGAMENTO E LEITOR INTELIGENTE DA PLANILHA
# -------------------------------------------------------------------------
@st.cache_data
def load_data(file):
    if file is not None:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file, header=1)
            
            df.columns = df.columns.astype(str).str.strip()
            
            rename_dict = {}
            for col in df.columns:
                norm_col = normalize_text(col)
                if 'NOTA' in norm_col:
                    rename_dict[col] = 'NOTAS'
                elif 'EQUIP' in norm_col:
                    rename_dict[col] = 'EQUIPAMENTO'
                elif 'ARE' in norm_col:
                    rename_dict[col] = 'ÁREA'
                elif 'ANALIS' in norm_col:
                    rename_dict[col] = 'Análise realizada?'
                elif 'MES' in norm_col:
                    rename_dict[col] = 'Mês'
            
            df = df.rename(columns=rename_dict)
            
            expected_cols = ["NOTAS", "EQUIPAMENTO", "ÁREA", "Análise realizada?", "Mês"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = "Não Classificado"
            
            # Preencher células vazias na coluna Mês (células mescladas do Excel)
            df['Mês'] = df['Mês'].ffill().fillna("Não Informado")
            
            df["ÁREA"] = df["ÁREA"].astype(str).str.strip().str.upper()
            df["Análise realizada?"] = df["Análise realizada?"].astype(str).str.strip().str.capitalize()
            df["Mês"] = df["Mês"].astype(str).str.strip()
            
            df = df.dropna(subset=["NOTAS"])
            
            return df
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            return None
    else:
        data = {
            "NOTAS": ["26161958", "26153640", "26173261", "26174250", "26174646", "28802523"],
            "EQUIPAMENTO": ["redutor ac. travasso", "correia transportadora C206", "COMPRESSOR 5", "motor da TC_02", "CT B-202.1", "RECEBIMENTO E ENVIO"],
            "ÁREA": ["SINTERIZAÇÃO", "PÁTIO DE CARVÃO", "PLANTA DE MOAGEM", "PLANTA DE MOAGEM", "SINTERIZAÇÃO", "PATIO DE CARVÃO"],
            "Análise realizada?": ["Sim", "Sim", "Sim", "Sim", "Sim", "Sim"],
            "Mês": ["Jan 2026", "Jan 2026", "Fev 2026", "Fev 2026", "Mar 2026", "Out 2025"]
        }
        return pd.DataFrame(data)

# -------------------------------------------------------------------------
# BARRA LATERAL (FILTROS)
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🟢 **USIMINAS**")
    st.caption("Servidor interno / CMM")
    st.markdown("---")
    
    st.header("Filtros da Planta")
    
    uploaded_file = st.file_uploader("Carregar planilha (Excel ou CSV)", type=["xlsx", "xls", "csv"])
    df = load_data(uploaded_file)
    
    if df is not None:
        area_opt = st.selectbox("Filtro por ÁREA:", ["Todos"] + sorted(list(df["ÁREA"].dropna().unique())))
        analise_opt = st.selectbox("Filtro por Análise realizada?:", ["Todos"] + sorted(list(df["Análise realizada?"].dropna().unique())))
        mes_opt = st.selectbox("Filtro por Mês:", ["Todos"] + sorted(list(df["Mês"].dropna().unique())))
        
        search_query = st.text_input("🔍 Pesquisa Geral (Qualquer campo):", "")
        
        st.markdown("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.button("Aplicar filtros", type="primary")
        with col_b2:
            st.button("Limpar Todos")

# -------------------------------------------------------------------------
# APLICANDO FILTROS NO DATAFRAME
# -------------------------------------------------------------------------
df_filtered = df.copy()

if area_opt != "Todos":
    df_filtered = df_filtered[df_filtered["ÁREA"] == area_opt]
if analise_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Análise realizada?"] == analise_opt]
if mes_opt != "Todos":
    df_filtered = df_filtered[df_filtered["Mês"] == mes_opt]

if search_query:
    mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
    df_filtered = df_filtered[mask]

# -------------------------------------------------------------------------
# CABEÇALHO PRINCIPAL E METADADOS
# -------------------------------------------------------------------------
col_title, col_btn = st.columns([6, 1])
with col_title:
    st.markdown("## 📊 Gestão de Notas Esporádicas Redução/Energia")
with col_btn:
    st.button("🔗 Compartilhar Dashboard")

base_name = uploaded_file.name if uploaded_file else "Planilha Redução/Energia (Demonstração)"
now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Base:</b> {base_name} &nbsp;|&nbsp; <b>Atualizado em:</b> {now_str} &nbsp;|&nbsp; <b>Linhas filtradas:</b> {len(df_filtered):,}</p>", unsafe_allow_html=True)

# Abas superiores
tab1, tab2 = st.tabs(["INVENTÁRIO E MONITORAMENTO", "NOTAS"])

with tab2:
    st.markdown("### 📌 NOTAS")
    
    # -------------------------------------------------------------------------
    # KPIS DE DESTAQUE
    # -------------------------------------------------------------------------
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    total_notas = len(df_filtered)
    total_analisadas = len(df_filtered[df_filtered["Análise realizada?"].str.lower().str.contains("sim", na=False)])
    total_equipamentos = df_filtered["EQUIPAMENTO"].nunique() if "EQUIPAMENTO" in df_filtered.columns else 0
    
    with col_kpi1:
        st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Total de Notas</p>
                <h2 style="color: #1b5e20; margin: 0; font-size: 38px;">{total_notas}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    with col_kpi2:
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; border-left-color: #0288d1;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Análises Realizadas</p>
                <h2 style="color: #0288d1; margin: 0; font-size: 38px;">{total_analisadas}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; border-left-color: #f57c00;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Equipamentos Únicos</p>
                <h2 style="color: #f57c00; margin: 0; font-size: 38px;">{total_equipamentos}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SEÇÃO DE GRÁFICOS (PIZZA E COLUNAS)
    # -------------------------------------------------------------------------
    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        st.markdown("##### 🚨 Distribuição por Área (%)")
        if not df_filtered.empty:
            area_counts = df_filtered["ÁREA"].value_counts().reset_index()
            area_counts.columns = ["Área", "Quantidade"]
            
            fig_donut = px.pie(
                area_counts, 
                names="Área", 
                values="Quantidade", 
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_donut.update_traces(textposition='inside', textinfo="percent+label", textfont_size=10)
            fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    with col_chart_right:
        st.markdown("##### 📈 Notas por Mês")
        if not df_filtered.empty and "Mês" in df_filtered.columns:
            # Agrupamento correto por contagem exata de notas por mês
            mes_counts = df_filtered.groupby("Mês", as_index=False).size()
            mes_counts.columns = ["Mês", "Quantidade"]
            
            fig_bar = px.bar(
                mes_counts,
                x="Mês",
                y="Quantidade",
                text="Quantidade",
                color="Mês",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_bar.update_traces(textposition='auto')
            fig_bar.update_layout(showlegend=False, margin=dict(t=20, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    st.markdown("---")
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtered, use_container_width=True)

with tab1:
    st.markdown("### 🔍 Inventário e Monitoramento Geral")
    st.dataframe(df, use_container_width=True)
