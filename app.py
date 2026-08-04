import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import unicodedata

# Configuração da Página em modo Wide
st.set_page_config(
    page_title="Gestão de Notas - CMM Usiminas",
    page_icon="🏭",
    layout="wide"
)

# Estilização CSS personalizada
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
# CONTROLE DE NAVEGAÇÃO ENTRE AS DASHBOARDS (ESTADO DOS BOTÕES)
# -------------------------------------------------------------------------
if 'pagina_ativa' not in st.session_state:
    st.session_state.pagina_ativa = 'Esporadicas'

# -------------------------------------------------------------------------
# CARREGAMENTO DE DADOS (Esporádicas e M4)
# -------------------------------------------------------------------------
@st.cache_data
def load_data_esporadicas(file):
    if file is not None:
        try:
            df = pd.read_excel(file, header=1) if not file.name.endswith('.csv') else pd.read_csv(file)
            df.columns = df.columns.astype(str).str.strip()
            # Mapeamento e limpeza...
            return df
        except:
            pass
    # Dados de exemplo Esporádicas
    return pd.DataFrame({
        "NOTAS": ["26161958", "26153640", "26173261", "26174250"],
        "EQUIPAMENTO": ["Redutor 1", "Correia C206", "Compressor 5", "Motor TC_02"],
        "ÁREA": ["SINTERIZAÇÃO", "PÁTIO DE CARVÃO", "PLANTA DE MOAGEM", "SINTERIZAÇÃO"],
        "Análise realizada?": ["Sim", "Sim", "Não", "Sim"],
        "Mês": ["Jan 2026", "Jan 2026", "Fev 2026", "Fev 2026"]
    })

@st.cache_data
def load_data_m4(file):
    if file is not None:
        try:
            df = pd.read_excel(file, header=1) if not file.name.endswith('.csv') else pd.read_csv(file)
            df.columns = df.columns.astype(str).str.strip()
            return df
        except:
            pass
    # Dados de exemplo específicos para M4
    return pd.DataFrame({
        "NOTAS M4": ["M4-901", "M4-902", "M4-903", "M4-904", "M4-905"],
        "EQUIPAMENTO": ["Turbina TRT", "Exaustor EG11", "Forno 5", "Caldeira B", "Ponte Rolante"],
        "ÁREA": ["ENERGIA", "REDUÇÃO", "REDUÇÃO", "ENERGIA", "ACIAARIA"],
        "Status M4": ["Pendente", "Concluído", "Em Andamento", "Pendente", "Concluído"],
        "Mês": ["Jan 2026", "Fev 2026", "Mar 2026", "Abr 2026", "Mai 2026"]
    })

# -------------------------------------------------------------------------
# BARRA LATERAL (BOTÕES DE NAVEGAÇÃO E FILTROS)
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### <span style='color: #1b5e20; font-size: 26px; font-weight: bold;'>🟢 USIMINAS</span>", unsafe_allow_html=True)
    st.caption("Servidor interno / CMM")
    st.markdown("---")
    
    st.markdown("### 🔀 Seleção de Painel")
    
    # Botões que alternam a tela ao serem apertados
    col_b_esp, col_b_m4 = st.columns(2)
    with col_b_esp:
        if st.button("Esporádicas"):
            st.session_state.pagina_ativa = 'Esporadicas'
            st.rerun()
    with col_b_m4:
        if st.button("Notas M4", type="primary" if st.session_state.pagina_ativa == 'M4' else "secondary"):
            st.session_state.pagina_ativa = 'M4'
            st.rerun()

    st.markdown("---")
    st.header("Filtros da Planta")
    uploaded_file = st.file_uploader("Carregar planilha (Excel ou CSV)", type=["xlsx", "xls", "csv"])

# -------------------------------------------------------------------------
# TELA 1: GESTÃO DE NOTAS ESPORÁDICAS
# -------------------------------------------------------------------------
if st.session_state.pagina_ativa == 'Esporadicas':
    df = load_data_esporadicas(uploaded_file)
    
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.markdown("## <span style='color: #1b5e20;'>📊 Gestão de Notas Esporádicas Redução/Energia</span>", unsafe_allow_html=True)
    with col_btn:
        st.button("🔗 Compartilhar")

    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel Ativo:</b> Notas Esporádicas &nbsp;|&nbsp; <b>Atualizado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # KPIs Esporádicas
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total de Notas", len(df))
    with k2:
        st.metric("Equipamentos Únicos", df["EQUIPAMENTO"].nunique() if "EQUIPAMENTO" in df.columns else 0)
    
    st.markdown("### 📋 Registros de Notas Esporádicas")
    st.dataframe(df, use_container_width=True)

# -------------------------------------------------------------------------
# TELA 2: GESTÃO DE NOTAS M4
# -------------------------------------------------------------------------
elif st.session_state.pagina_ativa == 'M4':
    df_m4 = load_data_m4(uploaded_file)
    
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.markdown("## <span style='color: #0288d1;'>📌 Gestão de Notas M4 (Manutenção)</span>", unsafe_allow_html=True)
    with col_btn:
        st.button("🔗 Compartilhar")

    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel Ativo:</b> Notas M4 &nbsp;|&nbsp; <b>Atualizado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # KPIs M4
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total de Notas M4", len(df_m4))
    with k2:
        pendentes = len(df_m4[df_m4["Status M4"].str.lower() == "pendente"]) if "Status M4" in df_m4.columns else 0
        st.metric("Notas Pendentes", pendentes)
    with k3:
        st.metric("Ativos M4", df_m4["EQUIPAMENTO"].nunique() if "EQUIPAMENTO" in df_m4.columns else 0)
    
    st.markdown("### 📋 Registros de Notas M4")
    st.dataframe(df_m4, use_container_width=True)
