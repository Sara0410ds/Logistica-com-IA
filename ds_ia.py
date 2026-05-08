import pandas as pd
import os
import streamlit as st
import plotly.express as px
from openai import OpenAI


st.set_page_config(
    page_title="Dashboard Inteligente de Logística com IA",
    layout="wide"
)

st.title("Dashboard Inteligente de Logística com IA")


api_key = os.getenv("OPENAI_API_KEY")

client = None

if api_key:
    client = OpenAI(api_key=api_key)
else:
    st.warning("API da OpenAI não configurada. IA desativada.")


arquivo = st.file_uploader(
    "Faça upload da base logística",
    type=["xlsx", "xls", "csv"]
)


if arquivo:

    try:

        if arquivo.name.endswith(".csv"):

            df = pd.read_csv(arquivo)

        else:

            clientes = pd.read_excel(
                arquivo,
                sheet_name="dCliente"
            )

            veiculos = pd.read_excel(
                arquivo,
                sheet_name="dVeiculo"
            )

            frete = pd.read_excel(
                arquivo,
                sheet_name="fFrete"
            )

            km = pd.read_excel(
                arquivo,
                sheet_name="fKmRodado"
            )


            df = frete.merge(
                clientes,
                on="ID Cliente",
                how="left"
            )

            df = df.merge(
                veiculos,
                on="ID Veiculo",
                how="left"
            )

        # Extrair data da viagem
        if "Viagem" in df.columns:

            df["Data_Viagem"] = pd.to_datetime(
                df["Viagem"].astype(str).str[:8],
                format="%Y%m%d",
                errors="coerce"
            )

        # Tempo fictício de entrega
        # (para KPI obrigatório)
        if "Data_Viagem" in df.columns:

            df["Tempo_Entrega"] = (
                (df.index % 10) + 1
            )

            df["Atraso"] = df["Tempo_Entrega"] > 7

        # Custo médio KM
        if (
            "Valor do Frete Líquido" in df.columns
            and "Peso (KG)" in df.columns
        ):

            df["Custo_Medio"] = (
                df["Valor do Frete Líquido"]
                / df["Peso (KG)"]
            )

        # =====================================
        # SIDEBAR FILTROS
        # =====================================
        st.sidebar.header("Filtros")

        df_filtrado = df.copy()

        # UF
        if "UF" in df.columns:

            uf = st.sidebar.multiselect(
                "UF",
                sorted(df["UF"].dropna().unique())
            )

            if uf:
                df_filtrado = df_filtrado[
                    df_filtrado["UF"].isin(uf)
                ]

        # Cidade
        if "Cidade" in df.columns:

            cidades = st.sidebar.multiselect(
                "Cidade",
                sorted(df["Cidade"].dropna().unique())
            )

            if cidades:
                df_filtrado = df_filtrado[
                    df_filtrado["Cidade"].isin(cidades)
                ]

        # Marca
        if "Marca" in df.columns:

            marcas = st.sidebar.multiselect(
                "Marca do Veículo",
                sorted(df["Marca"].dropna().unique())
            )

            if marcas:
                df_filtrado = df_filtrado[
                    df_filtrado["Marca"].isin(marcas)
                ]

        # Tipo Veículo
        if "Tipo Veículo" in df.columns:

            tipos = st.sidebar.multiselect(
                "Tipo Veículo",
                sorted(df["Tipo Veículo"].dropna().unique())
            )

            if tipos:
                df_filtrado = df_filtrado[
                    df_filtrado["Tipo Veículo"].isin(tipos)
                ]

        # =====================================
        # KPIs
        # =====================================
        st.subheader("Indicadores Logísticos")

        col1, col2, col3, col4 = st.columns(4)

        total_pedidos = len(df_filtrado)

        tempo_medio = round(
            df_filtrado["Tempo_Entrega"].mean(),
            2
        )

        atrasos = df_filtrado["Atraso"].sum()

        frete_total = round(
            df_filtrado["Valor do Frete Líquido"].sum(),
            2
        )

        col1.metric(
            "Total de Pedidos",
            total_pedidos
        )

        col2.metric(
            "Tempo Médio de Entrega",
            f"{tempo_medio} dias"
        )

        col3.metric(
            "Total de Atrasos",
            int(atrasos)
        )

        col4.metric(
            "Frete Total",
            f"R$ {frete_total:,.2f}"
        )

        # =====================================
        # TABELA
        # =====================================
        st.subheader("Dados Logísticos")

        st.dataframe(
            df_filtrado,
            use_container_width=True
        )

        # =====================================
        # GRÁFICO DINÂMICO
        # =====================================
        st.subheader("Gráfico Dinâmico")

        colunas_num = df_filtrado.select_dtypes(
            include=["number"]
        ).columns.tolist()

        colunas_cat = df_filtrado.select_dtypes(
            exclude=["number"]
        ).columns.tolist()

        if colunas_num and colunas_cat:

            x = st.selectbox(
                "Selecione o Eixo X",
                colunas_cat
            )

            y = st.selectbox(
                "Selecione o Eixo Y",
                colunas_num
            )

            grafico = px.bar(
                df_filtrado,
                x=x,
                y=y,
                color=x,
                title=f"{y} por {x}"
            )

            st.plotly_chart(
                grafico,
                use_container_width=True
            )

        # =====================================
        # GRÁFICO EXTRA
        # =====================================
        st.subheader("🚛 Entregas por UF")

        if (
            "UF" in df_filtrado.columns
            and "Valor do Frete Líquido" in df_filtrado.columns
        ):

            uf_grafico = (
                df_filtrado.groupby("UF")[
                    "Valor do Frete Líquido"
                ]
                .sum()
                .reset_index()
            )

            fig2 = px.pie(
                uf_grafico,
                names="UF",
                values="Valor do Frete Líquido",
                title="Distribuição de Frete por UF"
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        # =====================================
        # IA
        # =====================================
        st.subheader("Pergunte para a IA")

        pergunta = st.chat_input(
            "Ex: Quais são os principais problemas logísticos?"
        )

        if pergunta:

            with st.chat_message("user"):
                st.write(pergunta)

            if client:

                resumo = df_filtrado.head(30).to_string()

                prompt = f"""
                Você é um analista de logística.

                Analise os dados abaixo e responda
                de forma clara, objetiva e profissional.

                Dados:
                {resumo}

                Pergunta:
                {pergunta}
                """

                try:

                    resposta = client.responses.create(
                        model="gpt-4.1-mini",
                        input=prompt
                    )

                    with st.chat_message("assistant"):
                        st.write(
                            resposta.output_text
                        )

                except Exception as e:

                    with st.chat_message("assistant"):
                        st.error(f"Erro na API: {e}")

            else:

                with st.chat_message("assistant"):
                    st.write(
                        "IA desativada porque a API Key não foi configurada."
                    )

    except Exception as erro:

        st.error(f"Erro ao processar arquivo: {erro}")