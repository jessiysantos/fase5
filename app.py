import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Candidatos", layout="wide")

# Carregar dados do GitHub
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/jessiysantos/fase5/main/candidatos.csv"
    df = pd.read_csv(url)

    # Limpeza da coluna 'remuneracao'
    if "remuneracao" in df.columns:
        df["remuneracao"] = (
            df["remuneracao"]
            .astype(str)
            .str.replace("R\$", "", regex=True)
            .str.replace(",", ".", regex=False)
            .str.extract(r"(\d+\.?\d*)")[0]
            .astype(float)
        )

    return df

df = carregar_dados()

# Título e boas-vindas
st.title("Dashboard de Análise de Candidatos")
st.markdown("""
### 👋 Seja bem-vindo!
Este painel permite explorar os dados dos candidatos por meio de gráficos interativos.

← Utilize as **abas laterais** para acessar outras funcionalidades, como a **pesquisa por similaridade** entre perfis e vagas.
""")

# Campo para seleção de atributo
st.subheader("Distribuição por Campo Selecionado")
opcao = st.selectbox("Escolha o campo para visualizar:", [
    "local", "pcd", "titulo_profissional", "conhecimentos_tecnicos",
    "certificacoes", "nivel_profissional", "nivel_academico",
    "nivel_ingles", "nivel_espanhol", "objetivo_profissional"
])

# Gerar gráfico de distribuição
if df[opcao].nunique() < 20:
    fig = px.histogram(df, x=opcao, color=opcao, title=f"Distribuição de {opcao}")
else:
    top_categorias = df[opcao].value_counts().nlargest(20)
    fig = px.bar(
        x=top_categorias.index,
        y=top_categorias.values,
        labels={"x": opcao, "y": "Frequência"},
        title=f"Top 20 valores mais frequentes de {opcao}"
    )

st.plotly_chart(fig, use_container_width=True)

# Gráfico de Remuneração por Nível Profissional
st.subheader("Remuneração por Nível Profissional")

if "remuneracao" in df.columns and "nivel_profissional" in df.columns:
    media_salarial = df.groupby("nivel_profissional")["remuneracao"].mean().reset_index()

    fig2 = px.box(df, x="nivel_profissional", y="remuneracao", title="Remuneração por Nível Profissional")

    fig2.add_trace(
        go.Scatter(
            x=media_salarial["nivel_profissional"],
            y=media_salarial["remuneracao"],
            mode="lines+markers",
            name="Média Salarial",
            line=dict(color="red", dash="dash")
        )
    )

    fig2.update_layout(
        yaxis=dict(
            range=[0, 10000],
            tick0=0,
            dtick=1000,
            title="Remuneração"
        )
    )

    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Colunas 'remuneracao' ou 'nivel_profissional' não estão disponíveis.")

# Visualização de currículo
st.subheader("Visualizar Currículo (cv_pt)")
if "nome" in df.columns and "cv_pt" in df.columns:
    nome_selecionado = st.selectbox("Selecione um candidato", df["nome"].dropna().unique())
    cv = df[df["nome"] == nome_selecionado]["cv_pt"].values[0]
    st.text_area("Currículo (PT)", value=cv, height=300)
else:
    st.warning("Colunas 'nome' ou 'cv_pt' não estão disponíveis.")
