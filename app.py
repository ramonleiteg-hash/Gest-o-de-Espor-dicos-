import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# ESTADOS E CONTROLE DE FILTROS
# -------------------------------------------------------------------------
filtros_keys = [
    'esp_area', 'esp_status', 'esp_pesquisa', 
    'm4_area', 'm4_status', 'm4_pesquisa'
]

for k in filtros_keys:
    if k not in st.session_state:
        if 'pesquisa' in k:
            st.session_state[k] = ""
        else:
            st.session_state[k] = "Todos"

def limpar_filtros():
    for k in filtros_keys:
        if 'pesquisa' in k:
            st.session_state[k] = ""
        else:
            st.session_state[k] = "Todos"

# -------------------------------------------------------------------------
# LEITOR INTELIGENTE AUTOMÁTICO (COM REMOÇÃO DE LINHAS DE TOTAL)
# -------------------------------------------------------------------------
@st.cache_data
def ler_planilha_inteligente(file_bytes, file_name, tipo="esporádicas"):
    if file_bytes is not None:
        try:
            is_csv = file_name.endswith('.csv')
            file_io = io.BytesIO(file_bytes)
            
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
                if any(kw in row_str for kw in ['NOTA', 'EQUIP', 'AREA', 'M4', 'STATUS', 'SITUA', 'ORDEM', 'AVISO', 'INSTALA', 'LOC', 'GERENCIA', 'SETOR']):
                    header_row = idx
                    break
            
            file_io.seek(0)
            
            if is_csv:
                df = pd.read_csv(file_io, header=header_row)
            else:
                df = pd.read_excel(file_io, sheet_name=sheet_target, header=header_row)
            
            df.columns = df.columns.astype(str).str.strip()
            
            def find_col(df_cols, keywords):
                for kw in keywords:
                    for c in df_cols:
                        if kw in normalize_text(c):
                            return c
                return None
            
            rename_dict = {}
            col_notas = find_col(df.columns, ['NOTA', 'ORDEM', 'AVISO'])
            if col_notas: rename_dict[col_notas] = 'NOTAS'
            
            col_equip = find_col(df.columns, ['EQUIP', 'DENOMINA', 'TAG'])
            if col_equip: rename_dict[col_equip] = 'EQUIPAMENTO'
            
            col_area = find_col(df.columns, ['INSTALA', 'LOC', 'ARE', 'GERENCIA', 'SETOR', 'OFICINA', 'PLANTA', 'UNIDADE', 'CENTRO', 'DIVISAO'])
            if col_area: rename_dict[col_area] = 'ÁREA'
            
            col_status = find_col(df.columns, ['STATUS SISTEMA', 'STATUS DO SISTEMA', 'STATUS', 'SITUA', 'ESTADO'])
            if col_status: rename_dict[col_status] = 'Status'
            
            col_mes = find_col(df.columns, ['MES', 'DATA NO', 'DATA', 'CRIACAO'])
            if col_mes: rename_dict[col_mes] = 'Mês'
            
            col_analise = find_col(df.columns, ['ANALIS'])
            if col_analise: rename_dict[col_analise] = 'Análise realizada?'
            
            df = df.rename(columns=rename_dict)
            df = df.loc[:, ~df.columns.duplicated(keep='first')]
            
            # --- TRADUTOR DE STATUS SAP ---
            if "Status" in df.columns:
                df["Status SAP"] = df["Status"].astype(str).str.strip().str.upper()
                def classificar_status(val):
                    val_str = str(val).upper()
                    if any(x in val_str for x in ['MSEN', 'MREL', 'ENCE', 'TECO', 'CONC']):
                        return "Encerrada"
                    return "Aberta"
                df["Status"] = df["Status SAP"].apply(classificar_status)
            else:
                df["Status"] = "Encerrada"
                df["Status SAP"] = "N/A"
            # -----------------------------

            if tipo == "esporádicas":
                expected_cols = ["NOTAS", "EQUIPAMENTO", "ÁREA", "Análise realizada?", "Mês", "Status", "Status SAP"]
            else:
                expected_cols = ["NOTAS", "EQUIPAMENTO", "ÁREA", "Status", "Mês", "Status SAP"]
                
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = "Não Classificado"
            
            if 'Mês' in df.columns:
                df['Mês'] = df['Mês'].ffill().fillna("Não Informado").astype(str).str.strip()
                
            df["ÁREA"] = df["ÁREA"].astype(str).str.strip().str.upper()
            df["Status"] = df["Status"].astype(str).str.strip().str.capitalize()
            
            if "Análise realizada?" in df.columns:
                df["Análise realizada?"] = df["Análise realizada?"].astype(str).str.strip().str.capitalize()

            if "NOTAS" in df.columns:
                df = df.dropna(subset=["NOTAS"])
                # Remove linhas indesejadas de cabeçalho repetido ou linhas de Total do SAP
                df = df[~df["NOTAS"].astype(str).str.upper().str.contains("TOTAL|SOMA|MEDIA|NOTAS", na=False)]
                
            return df
        except Exception as e:
            st.error(f"⚠️ Erro ao processar a aba '{tipo}': {str(e)}")
            return None 
    else:
        if tipo == "esporádicas":
            return pd.DataFrame({"NOTAS": ["26161958", "26153640", "26173261"], "EQUIPAMENTO": ["Redutor 1", "Correia C206", "Compressor"], "ÁREA": ["US01-RD-SINT3", "US01-RD-SINT2", "US01-RD-AF002"], "Status": ["Encerrada", "Encerrada", "Encerrada"], "Status SAP": ["N/A", "N/A", "N/A"], "Análise realizada?": ["Sim", "Não", "Sim"], "Mês": ["2026-01-01", "2026-01-15", "2026-02-10"]})
        else:
            return pd.DataFrame({"NOTAS": ["M4-901", "M4-902", "M4-903"], "EQUIPAMENTO": ["Turbina", "Exaustor", "Forno"], "ÁREA": ["US01-RD-SINT3", "US01-RD-SINT2", "US01-RD-AF002"], "Status": ["Encerrada", "Encerrada", "Aberta"], "Status SAP": ["MSEN", "MBAR MREL MSEN", "MSPN"], "Mês": ["2026-01-01", "2026-02-15", "2026-02-20"]})

# -------------------------------------------------------------------------
# CABEÇALHO PRINCIPAL E NAVEGAÇÃO
# -------------------------------------------------------------------------
col_t1, col_t2 = st.columns([6, 1])
with col_t1:
    st.markdown("## <span style='color: #1b5e20;'>📊 Gestão de Notas de Manutenção</span>", unsafe_allow_html=True)
with col_t2:
    st.button("🔗 Compartilhar")

painel_selecionado = st.radio("Selecione o Painel para Visualização:", ["Esporádicas", "Notas M4"], horizontal=True)
st.markdown("---")

# -------------------------------------------------------------------------
# BARRA LATERAL (UPLOADER E FILTROS)
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
        df_ref = df_esporadicas if df_esporadicas is not None else pd.DataFrame(columns=["ÁREA", "Status"])
        st.selectbox("Filtro por ÁREA:", ["Todos"] + sorted(list(df_ref["ÁREA"].dropna().unique())), key="esp_area")
        st.text_input("🔍 Pesquisa Geral:", key="esp_pesquisa")
    else:
        df_ref_m4 = df_m4 if df_m4 is not None else pd.DataFrame(columns=["ÁREA", "Status"])
        st.selectbox("Filtro por ÁREA (M4):", ["Todos"] + sorted(list(df_ref_m4["ÁREA"].dropna().unique())), key="m4_area")
        st.selectbox("Filtro por Status (M4):", ["Todos", "Aberta", "Encerrada"], key="m4_status")
        st.text_input("🔍 Pesquisa M4:", key="m4_pesquisa")
        
    st.button("🧹 Limpar Filtros", on_click=limpar_filtros, type="primary", use_container_width=True)

# -------------------------------------------------------------------------
# TELA 1: GESTÃO DE NOTAS ESPORÁDICAS
# -------------------------------------------------------------------------
if painel_selecionado == "Esporádicas":
    df = df_esporadicas if df_esporadicas is not None else pd.DataFrame(columns=["NOTAS", "EQUIPAMENTO", "ÁREA", "Status", "Status SAP", "Mês"])

    df_filtered = df.copy()

    if st.session_state.esp_area != "Todos": df_filtered = df_filtered[df_filtered["ÁREA"] == st.session_state.esp_area]
    if st.session_state.esp_pesquisa:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(st.session_state.esp_pesquisa, case=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel:</b> Esporádicas &nbsp;|&nbsp; <b>Atualizado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} &nbsp;|&nbsp; <b>Linhas exibidas:</b> {len(df_filtered):,}</p>", unsafe_allow_html=True)
    
    col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
    total_notas = len(df_filtered)
    encerradas = total_notas
    abertas = 0
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
            fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_donut, use_container_width=True)

    with col_chart_right:
        st.markdown("##### 🌡️ Termômetro de Conclusão")
        taxa_conclusao = 100.0 if total_notas > 0 else 0
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = taxa_conclusao,
            number = {'suffix': "%", 'font': {'size': 40, 'color': '#1b5e20'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#1b5e20"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#ffebee'},
                    {'range': [50, 80], 'color': '#fff9c4'},
                    {'range': [80, 100], 'color': '#c8e6c9'}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}
            }
        ))
        fig_gauge.update_layout(margin=dict(t=30, b=10, l=20, r=20), height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("##### 📊 Evolução Histórica (Gráfico de Colunas)")
    if not df_filtered.empty and "Mês" in df_filtered.columns:
        df_chart = df_filtered.copy()
        df_chart["Mês_Formatado"] = pd.to_datetime(df_chart["Mês"], errors='coerce').dt.strftime('%Y-%m')
        df_chart["Mês_Formatado"] = df_chart["Mês_Formatado"].fillna(df_chart["Mês"])
        
        grouped = df_chart.groupby("Mês_Formatado").size().reset_index(name='Total')
        grouped = grouped.sort_values("Mês_Formatado")
        
        fig_evo = go.Figure()
        fig_evo.add_trace(go.Bar(
            x=grouped['Mês_Formatado'], y=grouped['Total'], name='Total de Notas', 
            marker_color='#2e7d32', text=grouped['Total'], textposition='outside', textfont=dict(weight='bold')
        ))
        
        fig_evo.update_layout(
            barmode='group', margin=dict(t=20, b=10, l=10, r=10), height=350, 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
            xaxis_title="", yaxis_title="Quantidade"
        )
        fig_evo.update_yaxes(range=[0, grouped['Total'].max() * 1.15])
        st.plotly_chart(fig_evo, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Tabela Detalhada - Esporádicas")
    st.dataframe(df_filtered, use_container_width=True)

# -------------------------------------------------------------------------
# TELA 2: GESTÃO DE NOTAS M4
# -------------------------------------------------------------------------
else:
    df_m4_filtered = df_m4.copy() if df_m4 is not None else pd.DataFrame(columns=["NOTAS", "EQUIPAMENTO", "ÁREA", "Status", "Status SAP", "Mês"])
    
    if st.session_state.m4_area != "Todos": df_m4_filtered = df_m4_filtered[df_m4_filtered["ÁREA"] == st.session_state.m4_area]
    if st.session_state.m4_status != "Todos": df_m4_filtered = df_m4_filtered[df_m4_filtered["Status"] == st.session_state.m4_status]
    if st.session_state.m4_pesquisa:
        mask = df_m4_filtered.astype(str).apply(lambda x: x.str.contains(st.session_state.m4_pesquisa, case=False)).any(axis=1)
        df_m4_filtered = df_m4_filtered[mask]

    st.markdown(f"<p style='font-size: 13px; color: #555;'><b>Painel:</b> Notas M4 &nbsp;|&nbsp; <b>Atualizado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} &nbsp;|&nbsp; <b>Linhas exibidas:</b> {len(df_m4_filtered):,}</p>", unsafe_allow_html=True)
    
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    total_m4 = len(df_m4_filtered)
    encerradas_m4 = len(df_m4_filtered[df_m4_filtered["Status"] == "Encerrada"])
    abertas_m4 = len(df_m4_filtered[df_m4_filtered["Status"] == "Aberta"])
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
            fig_donut_m4.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_donut_m4, use_container_width=True)

    with col_chart_m2:
        st.markdown("##### 🌡️ Termômetro de Conclusão M4")
        taxa_conclusao_m4 = (encerradas_m4 / total_m4 * 100) if total_m4 > 0 else 0
        fig_gauge_m4 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = taxa_conclusao_m4,
            number = {'suffix': "%", 'font': {'size': 40, 'color': '#0288d1'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#0288d1"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#ffebee'},
                    {'range': [50, 80], 'color': '#fff9c4'},
                    {'range': [80, 100], 'color': '#c8e6c9'}],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}
            }
        ))
        fig_gauge_m4.update_layout(margin=dict(t=30, b=10, l=20, r=20), height=300)
        st.plotly_chart(fig_gauge_m4, use_container_width=True)

    st.markdown("##### 📊 Evolução Histórica M4 (Gráfico de Colunas)")
    if not df_m4_filtered.empty and "Mês" in df_m4_filtered.columns:
        df_chart_m4 = df_m4_filtered.copy()
        df_chart_m4["Mês_Formatado"] = pd.to_datetime(df_chart_m4["Mês"], errors='coerce').dt.strftime('%Y-%m')
        df_chart_m4["Mês_Formatado"] = df_chart_m4["Mês_Formatado"].fillna(df_chart_m4["Mês"])
        
        grouped_m4 = df_chart_m4.groupby(["Mês_Formatado", "Status"]).size().unstack(fill_value=0).reset_index()
        if 'Encerrada' not in grouped_m4.columns: grouped_m4['Encerrada'] = 0
        if 'Aberta' not in grouped_m4.columns: grouped_m4['Aberta'] = 0
        
        grouped_m4['Total'] = grouped_m4['Aberta'] + grouped_m4['Encerrada']
        grouped_m4 = grouped_m4.sort_values("Mês_Formatado")
        
        fig_evo_m4 = go.Figure()
        fig_evo_m4.add_trace(go.Bar(
            x=grouped_m4['Mês_Formatado'], y=grouped_m4['Total'], name='Total de Notas', 
            marker_color='#8bc34a', text=grouped_m4['Total'], textposition='outside', textfont=dict(weight='bold')
        ))
        fig_evo_m4.add_trace(go.Bar(
            x=grouped_m4['Mês_Formatado'], y=grouped_m4['Encerrada'], name='Encerradas', 
            marker_color='#0288d1', text=grouped_m4['Encerrada'], textposition='outside', textfont=dict(weight='bold')
        ))
        
        fig_evo_m4.update_layout(
            barmode='group', margin=dict(t=20, b=10, l=10, r=10), height=350, 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
            xaxis_title="", yaxis_title="Quantidade"
        )
        fig_evo_m4.update_yaxes(range=[0, grouped_m4['Total'].max() * 1.15])
        st.plotly_chart(fig_evo_m4, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Registros Detalhados - Notas M4")
    cols_order_m4 = [c for c in df_m4_filtered.columns if c not in ["Status", "Status SAP"]] + ["Status", "Status SAP"]
    st.dataframe(df_m4_filtered[cols_order_m4], use_container_width=True)
