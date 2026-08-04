import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import unicodedata
import io

# Configuração da Página
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
        .metric-card { background-color: #ffffff; padding: 15px; border-radius: 8px; border-left: 5px solid #1b5e20; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        /* Ajuste do botão Limpar Filtros na sidebar */
        [data-testid="stSidebar"] button { margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# Função para remover acentos
def normalize_text(text):
    if not isinstance(text, str):
        text = str(text)
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).upper().strip()

# -------------------------------------------------------------------------
# ESTADOS E CONTROLE DE FILTROS (Botão Limpar e Botões Rápidos)
# -------------------------------------------------------------------------
filtros_keys = [
    'esp_situacao', 'esp_area', 'esp_status', 'esp_analise', 'esp_mes', 'esp_pesquisa', 
    'm4_situacao', 'm4_area', 'm4_status', 'm4_mes', 'm4_pesquisa'
]

# Inicializa as variáveis na memória para os filtros funcionarem
for k in filtros_keys:
    if k not in st.session_state:
        if 'pesquisa' in k:
            st.session_state[k] = ""
        elif 'situacao' in k:
            st.session_state[k] = "Todas"
        else:
            st.session_state[k] = "Todos"

def limpar_filtros():
    """Função engatilhada ao clicar no botão de limpar filtros"""
    for k in filtros_keys:
        if 'pesquisa' in k:
            st.session_state[k] = ""
        elif 'situacao' in k:
            st.session_state[k] = "Todas"
        else:
            st.session_state[k] = "Todos"

# -------------------------------------------------------------------------
# LEITOR INTELIGENTE AUTOMÁTICO (COM TRAVA DE DESDUPLICAÇÃO)
# -------------------------------------------------------------------------
@st.cache_data
def ler_planilha_inteligente(file_bytes, file_name, tipo="esporádicas"):
    if file_bytes is not None:
        try:
            is_csv = file_name.endswith('.csv')
            
            # Transforma os bytes em um "arquivo fresco" na memória
            file_io = io.BytesIO(file_bytes)
            
            # Descobre qual aba (sheet) deve ser lida de forma segura
            if not is_csv:
                xls = pd.ExcelFile(file_io)
                sheet_target = xls.sheet_names[0] if tipo == "esporádicas" else (xls.sheet_names[-1] if len(xls.sheet_names) > 1 else xls.sheet_names[0])
                
                for s in xls.sheet_names:
                    norm_s = normalize_text(s).lower()
                    if tipo == "esporádicas" and ('espor' in norm_s or 'esp' in norm_s):
                        sheet_target = s
                        break
                    elif tipo == "m4" and 'm4' in norm_s:
                        sheet_target = s
                        break
            
            file_io.seek(0)
            
            if is_csv:
                df_raw = pd.read_csv(file_io, header=None)
            else:
                df_raw = pd.read_excel(file_io, sheet_name=sheet_target, header=None)
            
            header_row = 0
            for idx, row in df_raw.head(30).iterrows():
                row_str = " ".join([normalize_text(str(val)) for val in row.values])
                if any(kw in row_str for kw in ['NOTA', 'EQUIP', 'AREA', 'M4', 'STATUS', 'SITUA', 'ORDEM', 'AVISO', 'LOCAL']):
                    header_row = idx
                    break
            
            file_io.seek(0)
            
            if is_csv:
                df = pd.read_csv(file_io, header=header_row)
            else:
                df = pd.read_excel(file_io, sheet_name=sheet_target, header=header_row)
            
            df.columns = df.columns.astype(str).str.strip()
            
            # Mapeamento com proteção contra sobreposição de nomes
            rename_dict = {}
            for col in df.columns:
                norm_col = normalize_text(col)
                if any(x in norm_col for x in ['NOTA', 'ORDEM', 'AVISO']):
                    if 'NOTAS' not in rename_dict.values(): rename_dict[col] = 'NOTAS'
                elif any(x in norm_col for x in ['EQUIP', 'DENOMINA']):
                    if 'EQUIPAMENTO' not in rename_dict.values(): rename_dict[col] = 'EQUIPAMENTO'
                elif any(x in norm_col for x in ['ARE', 'LOCAL', 'SETOR']):
                    if 'ÁREA' not in rename_dict.values(): rename_dict[col] = 'ÁREA'
                elif 'ANALIS' in norm_col:
                    if 'Análise realizada?' not in rename_dict.values(): rename_dict[col] = 'Análise realizada?'
                elif any(x in norm_col for x in ['STATUS', 'SITUA', 'ESTADO']):
                    if 'Status' not in rename_dict.values(): rename_dict[col] = 'Status'
                elif any(x in norm_col for x in ['MES', 'DATA', 'CRIACAO']):
                    if 'Mês' not in rename_dict.values(): rename_dict[col] = 'Mês'
            
            df = df.rename(columns=rename_dict)
            
            # Trava de segurança para desduplicação
            df = df.loc[:, ~df.columns.duplicated(keep='first')]
            
            if tipo == "esporádicas":
                expected_cols = ["NOTAS", "EQUIPAMENTO", "ÁREA", "Análise realizada?", "Mês", "Status"]
            else:
                expected_cols = ["NOTAS", "EQUIPAMENTO", "ÁREA", "Status", "Mês"]
                
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = "Não Classificado"
            
            if 'Mês' in df.columns:
                df['Mês'] = df['Mês'].ffill().fillna("Não Informado").astype(str).str.strip()
                
            df["ÁREA"] = df["ÁREA"].astype(str).str.strip().str.upper()
            df["Status"] = df["Status"].astype(str).str.strip().str.upper()
            
            if "Análise realizada?" in df.columns:
                df["Análise realizada?"] = df["Análise realizada?"].astype(str).str.strip().str.capitalize()

            if "NOTAS" in df.columns:
                df = df.dropna(subset=["NOTAS"])
                df = df[df["NOTAS"].astype(str).str.upper() != "NOTAS"]
                
            return df
        except Exception as e:
            st.error(f"⚠️ Erro ao processar a aba '{tipo}': {str(e)}")
            return None 
    else:
        # Dados padrão
        if tipo == "esporádicas":
            return pd.DataFrame({"NOTAS": ["26161958", "26153640", "26173261"], "EQUIPAMENTO": ["Redutor 1", "Correia C206", "Compressor"], "ÁREA": ["SINTERIZAÇÃO", "PÁTIO", "MOAGEM"], "Status": ["ABER", "ENCE", "ENCE"], "Análise realizada?": ["Sim", "Não", "Sim"], "Mês": ["Jan 2026", "Jan 2026", "Fev 2026"]})
        else:
            return pd.DataFrame({"NOTAS": ["M4-901", "M4-902", "M4-903"], "EQUIPAMENTO": ["Turbina", "Exaustor", "Forno"], "ÁREA": ["ENERGIA", "REDUÇÃO", "REDUÇÃO"], "Status": ["LIB", "ENCE", "TECO"], "Mês": ["Jan 2026", "Fev 2026", "Fev 2026"]})

# -------------------------------------------------------------------------
# CABEÇALHO PRINCIPAL E RÁDIOS DE NAVEGAÇÃO
# -------------------------------------------------------------------------
col_t1, col_t2 = st.columns([6, 1])
with col_t1:
    st.markdown("## <span style='color: #1b5e20;'>📊 Gestão de Notas e Manutenção</span>", unsafe_allow_html=True)
with col_t2:
    st.button("🔗 Compartilhar")

# Rádio de seleção
painel_selecionado = st.radio("Selecione o Painel para Visualização:", ["Esporádicas", "Notas M4"], horizontal=True)
st.markdown("---")

# -------------------------------------------------------------------------
# BARRA LATERAL (UPLOADER, FILTROS E BOTÃO LIMPAR)
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### <span style='color: #1b5e20; font-size: 26px; font-weight: bold;'>🟢 USIMINAS</span>", unsafe_allow_html=True)
    st.caption("Servidor interno / CMM")
    st.markdown("---")
    
    st.header("📂 Carregar Arquivo Único")
    uploaded_file = st.file_uploader("Planilha (Abas: Esporádicas e M4)", type=["xlsx", "xls", "csv"])
    
    if uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
    else:
        raw_bytes = None
        file_name = ""
        
    df_esporadicas = ler_planilha_inteligente(raw_bytes, file_name, tipo="esporádicas")
    df_m4 = ler_planilha_inteligente(raw_bytes, file_name, tipo="m4")

    st.markdown("---")
    st.subheader(f"Filtros - {painel_selecionado}")
    
    if painel_selecionado == "Esporádicas":
        df_ref = df_esporadicas if df_esporadicas is not None else pd.DataFrame(columns=["ÁREA", "Status", "Análise realizada?", "Mês"])
        
        # BOTÕES DE FILTRO RÁPIDO PARA SITUAÇÃO
        st.radio("Filtro Rápido (Situação):", ["Todas", "Abertas", "Encerradas"], horizontal=True, key="esp_situacao")
        
        st.selectbox("Filtro por ÁREA:", ["Todos"] + sorted(list(df_ref["ÁREA"].dropna().unique())), key="esp_area")
        st.selectbox("Filtro detalhado por Status:", ["Todos"] + sorted(list(df_ref["Status"].dropna().unique())), key="esp_status")
        st.selectbox("Filtro por Análise?:", ["Todos"] + sorted(list(df_ref["Análise realizada?"].dropna().unique())), key="esp_analise")
        st.selectbox("Filtro por Mês:", ["Todos"] + sorted(list(df_ref["Mês"].dropna().unique())), key="esp_mes")
        st.text_input("🔍 Pesquisa Geral:", key="esp_pesquisa")
    else:
        df_ref_m4 = df_m4 if df_m4 is not None else pd.DataFrame(columns=["ÁREA", "Status", "Mês"])
        
        # BOTÕES DE FILTRO RÁPIDO PARA SITUAÇÃO
        st.radio("Filtro Rápido (Situação M4):", ["Todas", "Abertas", "Encerradas"], horizontal=True, key="m4_situacao")
        
        st.selectbox("Filtro por ÁREA (M4):", ["Todos"] + sorted(list(df_ref_m4["ÁREA"].dropna().unique())), key="m4_area")
        st.selectbox("Filtro detalhado por Status (M4):", ["Todos"] + sorted(list(df_ref_m4["Status"].dropna().unique())), key="m4_status")
        st.selectbox("Filtro por Mês (M4):", ["Todos"] + sorted(list(df_ref_m4["Mês"].dropna().unique())), key="m4_mes")
        st.text_input("🔍 Pesquisa M4:", key="m4_pesquisa")
        
    st.button("🧹 Limpar Filtros", on_click=limpar_filtros, type="primary", use_container_width=True)


# -------------------------------------------------------------------------
# TELA 1: GESTÃO DE NOTAS ESPORÁDICAS
# -------------------------------------------------------------------------
if painel_selecionado == "Esporádicas":
    df = df_esporadicas if df_esporadicas is not None else pd.DataFrame(columns=["NOTAS", "EQUIPAMENTO", "ÁREA", "Status", "Análise realizada?", "Mês"])

    df_filtered = df.copy()
    
    # Filtro Rápido de Botões (Abertas / Encerradas)
    if st.session_state.esp_situacao == "Encerradas":
        df_filtered = df_filtered[df_filtered["Status"].astype(str).str.contains("ENCE|TECO|CONC", case=False, na=False)]
    elif st.session_state.esp_situacao == "Abertas":
        df_filtered = df_filtered[~df_filtered["Status"].astype(str).str.contains("ENCE|TECO|CONC", case=False, na=False)]

    # Filtros Tradicionais
    if st.session_state.esp_area != "Todos": df_filtered = df_filtered[df_filtered["ÁREA"] == st.session_state.esp_area]
    if st.session_state.esp_status != "Todos": df_filtered = df_filtered[df_filtered["Status"] == st.session_state.esp_status]
    if st.session_state.esp_analise != "Todos": df_filtered = df_filtered[df_filtered["Análise realizada?"] == st.session_state.esp_analise]
    if st.session_state.esp_mes != "Todos": df_filtered = df_filtered[df_filtered["Mês"] == st.session_state.esp_mes]
    if st.session_state.esp_pesquisa:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(st.session_state.esp_pesquisa, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel:</b> Esporádicas &nbsp;|&nbsp; <b>Atualizado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} &nbsp;|&nbsp; <b>Linhas exibidas:</b> {len(df_filtered):,}</p>", unsafe_allow_html=True)
    
    col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
    total_notas = len(df_filtered)
    encerradas = len(df_filtered[df_filtered["Status"].astype(str).str.contains("ENCE|TECO|CONC", case=False, na=False)])
    abertas = total_notas - encerradas
    total_analisadas = len(df_filtered[df_filtered["Análise realizada?"].astype(str).str.lower().str.contains("sim", na=False)]) if "Análise realizada?" in df_filtered.columns else 0
    total_equipamentos = df_filtered["EQUIPAMENTO"].nunique() if "EQUIPAMENTO" in df_filtered.columns else 0
    
    with col_k1:
        st.markdown(f"""<div class="metric-card" style="text-align: center;"><p style="color: #666; font-size: 13px; margin-bottom: 5px;">Total de Notas</p><h2 style="color: #1b5e20; margin: 0; font-size: 32px;">{total_notas}</h2></div>""", unsafe_allow_html=True)
    with col_k2:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #d32f2f;"><p style="color: #666; font-size: 13px; margin-bottom: 5px;">Notas Abertas</p><h2 style="color: #d32f2f; margin: 0; font-size: 32px;">{abertas}</h2></div>""", unsafe_allow_html=True)
    with col_k3:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #0288d1;"><p style="color: #666; font-size: 13px; margin-bottom: 5px;">Notas Encerradas</p><h2 style="color: #0288d1; margin: 0; font-size: 32px;">{encerradas}</h2></div>""", unsafe_allow_html=True)
    with col_k4:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #00796B;"><p style="color: #666; font-size: 13px; margin-bottom: 5px;">Análises Realizadas</p><h2 style="color: #00796B; margin: 0; font-size: 32px;">{total_analisadas}</h2></div>""", unsafe_allow_html=True)
    with col_k5:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #f57c00;"><p style="color: #666; font-size: 13px; margin-bottom: 5px;">Equip. Únicos</p><h2 style="color: #f57c00; margin: 0; font-size: 32px;">{total_equipamentos}</h2></div>""", unsafe_allow_html=True)
        
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

    with col_chart_right:
        st.markdown("##### 📈 Notas por Mês")
        if not df_filtered.empty and "Mês" in df_filtered.columns:
            mes_counts = df_filtered.groupby("Mês", as_index=False).size()
            mes_counts.columns = ["Mês", "Quantidade"]
            fig_bar = px.bar(mes_counts, x="Mês", y="Quantidade", text="Quantidade", color="Mês", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_bar.update_traces(textposition='auto')
            fig_bar.update_layout(showlegend=False, margin=dict(t=20, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Tabela Detalhada - Esporádicas")
    st.dataframe(df_filtered, use_container_width=True)

# -------------------------------------------------------------------------
# TELA 2: GESTÃO DE NOTAS M4
# -------------------------------------------------------------------------
else:
    df_m4_filtered = df_m4.copy() if df_m4 is not None else pd.DataFrame(columns=["NOTAS", "EQUIPAMENTO", "ÁREA", "Status", "Mês"])
    
    # Filtro Rápido de Botões (Abertas / Encerradas)
    if st.session_state.m4_situacao == "Encerradas":
        df_m4_filtered = df_m4_filtered[df_m4_filtered["Status"].astype(str).str.contains("ENCE|TECO|CONC", case=False, na=False)]
    elif st.session_state.m4_situacao == "Abertas":
        df_m4_filtered = df_m4_filtered[~df_m4_filtered["Status"].astype(str).str.contains("ENCE|TECO|CONC", case=False, na=False)]

    # Filtros Tradicionais
    if st.session_state.m4_area != "Todos": df_m4_filtered = df_m4_filtered[df_m4_filtered["ÁREA"] == st.session_state.m4_area]
    if st.session_state.m4_status != "Todos": df_m4_filtered = df_m4_filtered[df_m4_filtered["Status"] == st.session_state.m4_status]
    if st.session_state.m4_mes != "Todos": df_m4_filtered = df_m4_filtered[df_m4_filtered["Mês"] == st.session_state.m4_mes]
    if st.session_state.m4_pesquisa:
        mask = df_m4_filtered.astype(str).apply(lambda x: x.str.contains(st.session_state.m4_pesquisa, case=False)).any(axis=1)
        df_m4_filtered = df_m4_filtered[mask]

    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel:</b> Notas M4 &nbsp;|&nbsp; <b>Atualizado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} &nbsp;|&nbsp; <b>Linhas exibidas:</b> {len(df_m4_filtered):,}</p>", unsafe_allow_html=True)
    
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    total_m4 = len(df_m4_filtered)
    encerradas_m4 = len(df_m4_filtered[df_m4_filtered["Status"].astype(str).str.contains("ENCE|TECO|CONC", case=False, na=False)])
    abertas_m4 = total_m4 - encerradas_m4
    ativos_m4 = df_m4_filtered["EQUIPAMENTO"].nunique() if "EQUIPAMENTO" in df_m4_filtered.columns else 0
    
    with col_k1:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #0288d1;"><p style="color: #666; font-size: 14px; margin-bottom: 5px;">Total de Notas M4</p><h2 style="color: #0288d1; margin: 0; font-size: 36px;">{total_m4}</h2></div>""", unsafe_allow_html=True)
    with col_k2:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #d32f2f;"><p style="color: #666; font-size: 14px; margin-bottom: 5px;">Notas Abertas</p><h2 style="color: #d32f2f; margin: 0; font-size: 36px;">{abertas_m4}</h2></div>""", unsafe_allow_html=True)
    with col_k3:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #388e3c;"><p style="color: #666; font-size: 14px; margin-bottom: 5px;">Notas Encerradas</p><h2 style="color: #388e3c; margin: 0; font-size: 36px;">{encerradas_m4}</h2></div>""", unsafe_allow_html=True)
    with col_k4:
        st.markdown(f"""<div class="metric-card" style="text-align: center; border-left-color: #f57c00;"><p style="color: #666; font-size: 14px; margin-bottom: 5px;">Ativos M4 Únicos</p><h2 style="color: #f57c00; margin: 0; font-size: 36px;">{ativos_m4}</h2></div>""", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

    col_chart_m1, col_chart_m2 = st.columns(2)
    with col_chart_m1:
        st.markdown("##### 🚨 M4 - Distribuição por Área (%)")
        if not df_m4_filtered.empty and "ÁREA" in df_m4_filtered.columns:
            area_m4_counts = df_m4_filtered["ÁREA"].value_counts().reset_index()
            area_m4_counts.columns = ["Área", "Quantidade"]
            fig_donut_m4 = px.pie(area_m4_counts, names="Área", values="Quantidade", hole=0.5, color_discrete_sequence=px.colors.qualitative.Prism)
            fig_donut_m4.update_traces(textposition='inside', textinfo="percent+label", textfont_size=10)
            fig_donut_m4.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_donut_m4, use_container_width=True)

    with col_chart_m2:
        st.markdown("##### 📈 Notas M4 por Mês")
        if not df_m4_filtered.empty and "Mês" in df_m4_filtered.columns:
            mes_m4_counts = df_m4_filtered.groupby("Mês", as_index=False).size()
            mes_m4_counts.columns = ["Mês", "Quantidade"]
            fig_bar_m4 = px.bar(mes_m4_counts, x="Mês", y="Quantidade", text="Quantidade", color="Mês", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_bar_m4.update_traces(textposition='auto')
            fig_bar_m4.update_layout(showlegend=False, margin=dict(t=20, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_bar_m4, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Registros Detalhados - Notas M4")
    st.dataframe(df_m4_filtered, use_container_width=True)
