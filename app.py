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
# CONTROLE DE NAVEGAÇÃO ENTRE OS PAINÉIS
# -------------------------------------------------------------------------
if 'pagina_ativa' not in st.session_state:
    st.session_state.pagina_ativa = 'Esporadicas'

# -------------------------------------------------------------------------
# LEITOR INTELIGENTE AUTOMÁTICO DA PLANILHA (DETECTOR DE CABEÇALHO)
# -------------------------------------------------------------------------
@st.cache_data
def load_data_esporadicas(file):
    if file is not None:
        try:
            # 1. Lê a planilha crua sem cabeçalho para localizar a linha correta das colunas
            if file.name.endswith('.csv'):
                df_raw = pd.read_csv(file, header=None)
            else:
                df_raw = pd.read_excel(file, header=None)
            
            # 2. Procura nas primeiras 10 linhas qual delas contém os títulos reais
            header_row = 0
            for idx, row in df_raw.head(10).iterrows():
                row_str = " ".join([normalize_text(str(val)) for val in row.values])
                if 'NOTA' in row_str or 'EQUIP' in row_str or 'AREA' in row_str:
                    header_row = idx
                    break
            
            # 3. Faz a leitura definitiva usando a linha correta descoberta
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, header=header_row)
            else:
                df = pd.read_excel(file, header=header_row)
            
            df.columns = df.columns.astype(str).str.strip()
            
            # Mapeamento flexível das colunas
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
            if 'Mês' in df.columns:
                df['Mês'] = df['Mês'].ffill().fillna("Não Informado")
            
            df["ÁREA"] = df["ÁREA"].astype(str).str.strip().str.upper()
            df["Análise realizada?"] = df["Análise realizada?"].astype(str).str.strip().str.capitalize()
            df["Mês"] = df["Mês"].astype(str).str.strip()
            
            # Remove linhas vazias ou repetições do cabeçalho na tabela
            df = df.dropna(subset=["NOTAS"])
            df = df[df["NOTAS"].astype(str).str.upper() != "NOTAS"]
            
            return df
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            return None
    else:
        # Demonstração padrão
        return pd.DataFrame({
            "NOTAS": ["26161958", "26153640", "26173261", "26174250"],
            "EQUIPAMENTO": ["Redutor 1", "Correia C206", "Compressor 5", "Motor TC_02"],
            "ÁREA": ["SINTERIZAÇÃO", "PÁTIO DE CARVÃO", "PLANTA DE MOAGEM", "SINTERIZAÇÃO"],
            "Análise realizada?": ["Sim", "Sim", "Não", "Sim"],
            "Mês": ["Jan 2026", "Jan 2026", "Fev 2026", "Fev 2026"]
        })

@st.cache_data
def load_data_m4(file):
    return pd.DataFrame({
        "NOTAS M4": ["M4-901", "M4-902", "M4-903", "M4-904", "M4-905"],
        "EQUIPAMENTO": ["Turbina TRT", "Exaustor EG11", "Forno 5", "Caldeira B", "Ponte Rolante"],
        "ÁREA": ["ENERGIA", "REDUÇÃO", "REDUÇÃO", "ENERGIA", "ACIARIA"],
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
    col_b_esp, col_b_m4 = st.columns(2)
    with col_b_esp:
        if st.button("Esporádicas", type="primary" if st.session_state.pagina_ativa == 'Esporadicas' else "secondary"):
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
    
    with st.sidebar:
        if df is not None and not df.empty:
            st.markdown("---")
            area_opt = st.selectbox("Filtro por ÁREA:", ["Todos"] + sorted(list(df["ÁREA"].dropna().unique())))
            analise_opt = st.selectbox("Filtro por Análise realizada?:", ["Todos"] + sorted(list(df["Análise realizada?"].dropna().unique())))
            mes_opt = st.selectbox("Filtro por Mês:", ["Todos"] + sorted(list(df["Mês"].dropna().unique())))
            search_query = st.text_input("🔍 Pesquisa Geral (Qualquer campo):", "")
        else:
            area_opt, analise_opt, mes_opt, search_query = "Todos", "Todos", "Todos", ""

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

    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.markdown("## <span style='color: #1b5e20;'>📊 Gestão de Notas Esporádicas Redução/Energia</span>", unsafe_allow_html=True)
    with col_btn:
        st.button("🔗 Compartilhar")

    base_name = uploaded_file.name if uploaded_file else "Planilha Redução/Energia (Demonstração)"
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Base:</b> {base_name} &nbsp;|&nbsp; <b>Atualizado em:</b> {now_str} &nbsp;|&nbsp; <b>Linhas filtradas:</b> {len(df_filtered):,}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📌 NOTAS")
    
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

    col_chart_left, col_chart_right = st.columns(2)
    with col_chart_left:
        st.markdown("##### 🚨 Distribuição por Área (%)")
        if not df_filtered.empty:
            area_counts = df_filtered["ÁREA"].value_counts().reset_index()
            area_counts.columns = ["Área", "Quantidade"]
            fig_donut = px.pie(area_counts, names="Área", values="Quantidade", hole=0.5, color_discrete_sequence=px.colors.qualitative.Prism)
            fig_donut.update_traces(textposition='inside', textinfo="percent+label", textfont_size=10)
            fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    with col_chart_right:
        st.markdown("##### 📈 Notas por Mês")
        if not df_filtered.empty and "Mês" in df_filtered.columns:
            mes_counts = df_filtered.groupby("Mês", as_index=False).size()
            mes_counts.columns = ["Mês", "Quantidade"]
            fig_bar = px.bar(mes_counts, x="Mês", y="Quantidade", text="Quantidade", color="Mês", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_bar.update_traces(textposition='auto')
            fig_bar.update_layout(showlegend=False, margin=dict(t=20, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    st.markdown("---")
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtered, use_container_width=True)

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
