import streamlit as st
import pandas as pd
import plotly.express as px
 
# Configuração da página
st.set_page_config(page_title="Logistics AI Dashboard", layout="wide")
 
# 1. Leitura de Dados
@st.cache_data
def carregar_dados():
    # Substitua pelo caminho do seu arquivo anexado
    df = pd.read_excel("Base_Logistica.xlsx")
    
    # Tratamento de Datas (ajuste os nomes das colunas conforme seu Excel)
    df["Data Pedido"] = pd.to_datetime(df["Data Pedido"])
    df["Data Entrega"] = pd.to_datetime(df["Data Entrega"])
    
    # Diferencial: Criação de colunas de cálculo logístico
    df["Tempo_Entrega"] = (df["Data Entrega"] - df["Data Pedido"]).dt.days
    
    # Exemplo de lógica de atraso (considerando meta de 5 dias)
    df["Status_Prazo"] = df["Tempo_Entrega"].apply(lambda x: "Atrasado" if x > 5 else "No Prazo")
    
    return df
 
try:
    df = carregar_dados()
 
    st.title("🚚 Dashboard Inteligente de Logística")
    st.markdown("---")
 
    # --- PARTE 3: FILTROS ---
    st.sidebar.header("Filtros")
    regiao = st.sidebar.multiselect("Selecione a Região", options=df["Região"].unique(), default=df["Região"].unique())
    status = st.sidebar.multiselect("Status da Entrega", options=df["Status_Prazo"].unique(), default=df["Status_Prazo"].unique())
 
    df_filtrado = df[(df["Região"].isin(regiao)) & (df["Status_Prazo"].isin(status))]
 
    # --- PARTE 1: KPIs ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Pedidos", len(df_filtrado))
    with col2:
        # KPI que impressiona
        st.metric("Tempo Médio de Entrega", f"{round(df_filtrado['Tempo_Entrega'].mean(), 2)} dias")
    with col3:
        atrasos = len(df_filtrado[df_filtrado["Status_Prazo"] == "Atrasado"])
        st.metric("Total de Atrasos", atrasos, delta_color="inverse")
 
    st.markdown("---")
 
    # --- GRÁFICOS DINÂMICOS ---
    st.subheader("Análise Gráfica")
    col_chart1, col_chart2 = st.columns(2)
 
    with col_chart1:
        eixo_x = st.selectbox("Selecione o Eixo X", ["Região", "Transportadora", "Status_Prazo"])
        fig = px.histogram(df_filtrado, x=eixo_x, title=f"Entregas por {eixo_x}", color=eixo_x)
        st.plotly_chart(fig, use_container_width=True)
 
    with col_chart2:
        fig_tempo = px.box(df_filtrado, x="Região", y="Tempo_Entrega", title="Distribuição de Tempo por Região")
        st.plotly_chart(fig_tempo, use_container_width=True)
 
    # --- TABELA DE DADOS ---
    st.subheader("📋 Base de Dados")
    st.dataframe(df_filtrado, use_container_width=True)
 
    # --- PARTE 2: IA (Interpretador) ---
    st.markdown("---")
    st.subheader("Consultoria de IA Logística")
    pergunta = st.text_input("Pergunte algo sobre seus dados (ex: Quais são os principais problemas?)")
 
    if pergunta:
        # Aqui simulamos a lógica da IA baseada nos dados reais do DF
        total_atrasos = len(df[df["Status_Prazo"] == "Atrasado"])
        pior_regiao = df[df["Status_Prazo"] == "Atrasado"]["Região"].mode()[0]
        
        resposta_ia = f"""
        **Análise da IA:** Identifiquei que temos {total_atrasos} pedidos com atraso.
        O principal gargalo está na região **{pior_regiao}**.
        Recomendo revisar os contratos das transportadoras que atendem essa área e verificar o tempo de processamento interno.
        """
        st.info(resposta_ia)
 
except Exception as e:
    st.error(f"Aguardando base de dados: {e}")
    st.info("Certifique-se de que o arquivo 'Base_Logistica.xlsx' está na mesma pasta do código.")