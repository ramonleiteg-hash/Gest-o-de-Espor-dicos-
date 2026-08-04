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
# CONTROLE DE NAVEGAÇÃO E ESTADO DOS DADOS
# -------------------------------------------------------------------------
if 'pagina_ativa' not in st.session_state:
    st.session_state.pagina_ativa = 'Esporadicas'

# -------------------------------------------------------------------------
# LEITOR INTELIGENTE AUTOMÁTICO (USADO PARA AMBAS AS PLANILHAS)
# -------------------------------------------------------------------------
def ler_planilha_inteligente(file, tipo="esporadica"):
    if file is not None:
        try:
            if file.name.endswith('.csv'):
                df_raw = pd.read_csv(file, header=None)
            else:
                df_raw = pd.read_excel(file, header=None)
            
            # Aumentado para procurar nas 15 primeiras linhas
            header_row = 0
            for idx, row in df_raw.head(15).iterrows():
                row_str = " ".join([normalize_text(str(val)) for val in row.values])
                # Palavras-chave expandidas para garantir que ache a linha correta
                if any(kw in row_str for kw in ['NOTA', 'EQUIP', 'AREA', 'M4', 'STATUS', 'SITUA']):
                    header_row = idx
                    break
            
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, header=header_row)
            else:
                df = pd.read_excel(file, header=header_row)
            
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
                elif 'STATUS' in norm_col or 'SITUA' in norm_col:
                    rename_dict[col] = 'Status M4'
                elif 'MES' in norm_col:
                    rename_dict[col] = 'Mês'
            
            df = df.rename(columns=rename_dict)
            
            if tipo == "esporadica":
                expected_cols = ["NOTAS", "EQUIPAMENTO", "ÁREA", "Análise realizada?", "Mês"]
            else:
                expected_cols = ["NOTAS", "EQUIPAMENTO", "ÁREA", "Status M4", "Mês"]

            for col in expected_cols:
                if col not in df.columns:
                    df[col] = "Não Classificado"
            
            if 'Mês' in df.columns:
                df['Mês'] = df['Mês'].ffill().fillna("Não Informado")
                
            df["ÁREA"] = df["ÁREA"].astype(str).str.strip().str.upper()
            df["Mês"] = df["Mês"].astype(str).str.strip()
            
            if "Análise realizada?" in df.columns:
                df["Análise realizada?"] = df["Análise realizada?"].astype(str).str.strip().str.capitalize()

            if "NOTAS" in df.columns:
                df = df.dropna(subset=["NOTAS"])
                df = df[df["NOTAS"].astype(str).str.upper() != "NOTAS"]
                
            return df
        except Exception as e:
            st.error("⚠️ Ocorreu um desvio no padrão da planilha, mas a aplicação foi mantida no ar.")
            return None # Tratado de forma segura mais abaixo
    else:
        # Dados de Demonstração padrão
        if tipo == "esporadica":
            return pd.DataFrame({
                "NOTAS": ["26161958", "26153640", "26173261", "26174250"],
                "EQUIPAMENTO": ["Redutor 1", "Correia C206", "Compressor 5", "Motor TC_02"],
                "ÁREA": ["SINTERIZAÇÃO", "PÁTIO DE CARVÃO", "PLANTA DE MOAGEM", "SINTERIZAÇÃO"],
                "Análise realizada?": ["Sim", "Sim", "Não", "Sim"],
                "Mês": ["Jan 2026", "Jan 2026", "Fev 2026", "Fev 2026"]
            })
        else:
            return pd.DataFrame({
                "NOTAS": ["M4-901", "M4-902", "M4-903", "M4-904", "M4-905"],
                "EQUIPAMENTO": ["Turbina TRT", "Exaustor EG11", "Forno 5", "Caldeira B", "Ponte Rolante"],
                "ÁREA": ["ENERGIA", "REDUÇÃO", "REDUÇÃO", "ENERGIA", "ACIARIA"],
                "Status M4": ["Pendente", "Concluído", "Em Andamento", "Pendente", "Concluído"],
                "Mês": ["Jan 2026", "Fev 2026", "Mar 2026", "Abr 2026", "Mai 2026"]
            })

# -------------------------------------------------------------------------
# BARRA LATERAL (BOTÕES DE NAVEGAÇÃO E UPLOADERS SEPARADOS)
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
    st.header("📂 Carregamento de Dados")
    
    if st.session_state.pagina_ativa == 'Esporadicas':
        file_esporadica = st.file_uploader("Carregar planilha Esporádicas (Excel/CSV)", type=["xlsx", "xls", "csv"], key="up_esp")
        df = ler_planilha_inteligente(file_esporadica, tipo="esporadica")
    else:
        file_m4 = st.file_uploader("Carregar planilha Notas M4 (Excel/CSV)", type=["xlsx", "xls", "csv"], key="up_m4")
        df_m4 = ler_planilha_inteligente(file_m4, tipo="m4")

# -------------------------------------------------------------------------
# TELA 1: GESTÃO DE NOTAS ESPORÁDICAS
# -------------------------------------------------------------------------
if st.session_state.pagina_ativa == 'Esporadicas':
    # Trava de segurança caso o arquivo venha corrompido ou fora do formato
    if df is None:
        df = pd.DataFrame(columns=["NOTAS", "EQUIPAMENTO", "ÁREA", "Análise realizada?", "Mês"])

    with st.sidebar:
        if not df.empty:
            st.markdown("---")
            st.subheader("Filtros Esporádicas")
            area_opt = st.selectbox("Filtro por ÁREA:", ["Todos"] + sorted(list(df["ÁREA"].dropna().unique())))
            analise_opt = st.selectbox("Filtro por Análise realizada?:", ["Todos"] + sorted(list(df["Análise realizada?"].dropna().unique())))
            mes_opt = st.selectbox("Filtro por Mês:", ["Todos"] + sorted(list(df["Mês"].dropna().unique())))
            search_query = st.text_input("🔍 Pesquisa Geral:", "")
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

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel:</b> Esporádicas &nbsp;|&nbsp; <b>Atualizado em:</b> {now_str} &nbsp;|&nbsp; <b>Linhas filtradas:</b> {len(df_filtered):,}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📌 NOTAS")
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    total_notas = len(df_filtered)
    total_analisadas = len(df_filtered[df_filtered["Análise realizada?"].str.lower().str.contains("sim", na=False)]) if "Análise realizada?" in df_filtered.columns else 0
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
        if not df_filtered.empty and "ÁREA" in df_filtered.columns:
            area_counts = df_filtered["ÁREA"].value_counts().reset_index()
            area_counts.columns = ["Área", "Quantidade"]
            fig_donut = px.pie(area_counts, names="Área", values="Quantidade", hole=0.5, color_discrete_sequence=px.colors.qualitative.Prism)
            fig_donut.update_traces(textposition='inside', textinfo="percent+label", textfont_size=10)
            fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para o gráfico.")

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
            st.info("Nenhum dado encontrado para o gráfico.")

    st.markdown("---")
    st.subheader("📋 Tabela Detalhada - Esporádicas")
    st.dataframe(df_filtered, use_container_width=True)

# -------------------------------------------------------------------------
# TELA 2: GESTÃO DE NOTAS M4
# -------------------------------------------------------------------------
elif st.session_state.pagina_ativa == 'M4':
    # Trava de segurança para a tabela M4
    if df_m4 is None:
        df_m4 = pd.DataFrame(columns=["NOTAS", "EQUIPAMENTO", "ÁREA", "Status M4", "Mês"])

    with st.sidebar:
        if not df_m4.empty:
            st.markdown("---")
            st.subheader("Filtros M4")
            area_m4_opt = st.selectbox("Filtro por ÁREA (M4):", ["Todos"] + sorted(list(df_m4["ÁREA"].dropna().unique())))
            mes_m4_opt = st.selectbox("Filtro por Mês (M4):", ["Todos"] + sorted(list(df_m4["Mês"].dropna().unique())))
            search_m4 = st.text_input("🔍 Pesquisa M4:", "")
        else:
            area_m4_opt, mes_m4_opt, search_m4 = "Todos", "Todos", ""

    df_m4_filtered = df_m4.copy()
    
    if area_m4_opt != "Todos":
        df_m4_filtered = df_m4_filtered[df_m4_filtered["ÁREA"] == area_m4_opt]
    if mes_m4_opt != "Todos":
        df_m4_filtered = df_m4_filtered[df_m4_filtered["Mês"] == mes_m4_opt]
    if search_m4:
        mask = df_m4_filtered.astype(str).apply(lambda x: x.str.contains(search_m4, case=False)).any(axis=1)
        df_m4_filtered = df_m4_filtered[mask]

    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.markdown("## <span style='color: #0288d1;'>📌 Gestão de Notas M4 (Manutenção)</span>", unsafe_allow_html=True)
    with col_btn:
        st.button("🔗 Compartilhar")

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel:</b> Notas M4 &nbsp;|&nbsp; <b>Atualizado em:</b> {now_str} &nbsp;|&nbsp; <b>Linhas filtradas:</b> {len(df_m4_filtered):,}</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; border-left-color: #0288d1;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Total de Notas M4</p>
                <h2 style="color: #0288d1; margin: 0; font-size: 38px;">{len(df_m4_filtered)}</h2>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        pendentes = len(df_m4_filtered[df_m4_filtered["Status M4"].str.lower().str.contains("pendente", na=False)]) if "Status M4" in df_m4_filtered.columns else 0
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; border-left-color: #f57c00;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Notas Pendentes</p>
                <h2 style="color: #f57c00; margin: 0; font-size: 38px;">{pendentes}</h2>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        ativos_m4 = df_m4_filtered["EQUIPAMENTO"].nunique() if "EQUIPAMENTO" in df_m4_filtered.columns else 0
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; border-left-color: #1b5e20;">
                <p style="color: #666; font-size: 14px; margin-bottom: 5px;">Ativos M4 Únicos</p>
                <h2 style="color: #1b5e20; margin: 0; font-size: 38px;">{ativos_m4}</h2>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Registros Detalhados - Notas M4")
    st.dataframe(df_m4_filtered, use_container_width=True)
