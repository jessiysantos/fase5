import streamlit as st
import pandas as pd
import plotly.express as px

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

# Mensagem de boas-vindas
st.title("Dashboard de Análise de Candidatos")
st.markdown("""
### 👋 Seja bem-vindo!
Este painel permite explorar os dados dos candidatos por meio de gráficos interativos.

→ Utilize as **abas laterais** para acessar outras funcionalidades, como a **pesquisa por similaridade** entre perfis e vagas.
""")

# Campo selecionável para visualização
st.subheader("Distribuição por Campo Selecionado")
campo = st.selectbox("Escolha o campo para visualizar:", [
    "local", "pcd", "titulo_profissional",
    "nivel_profissional", "nivel_academico",
    "nivel_ingles", "nivel_espanhol", "objetivo_profissional"
])

# Gráfico do campo selecionado
if df[campo].nunique() < 20:
    fig = px.histogram(df, x=campo, color=campo, title=f"Distribuição de {campo}")
else:
    top_valores = df[campo].value_counts().nlargest(20)
    fig = px.bar(
        x=top_valores.index,
        y=top_valores.values,
        labels={"x": campo, "y": "Frequência"},
        title=f"Top 20 valores mais frequentes de {campo}"
    )

st.plotly_chart(fig, use_container_width=True)

# Gráfico de média salarial por nível profissional
st.subheader("Média Salarial por Nível Profissional")

if "remuneracao" in df.columns and "nivel_profissional" in df.columns:
    df_filtrado = df.dropna(subset=["remuneracao", "nivel_profissional"])
    media = df_filtrado.groupby("nivel_profissional")["remuneracao"].median().reset_index()

    fig2 = px.bar(
        media,
        x="nivel_profissional",
        y="remuneracao",
        color="nivel_profissional",
        text=media["remuneracao"].round(2),
        title="Média Salarial por Nível Profissional"
    )

    fig2.update_layout(
        yaxis=dict(
            range=[0, 10000],
            tick0=0,
            dtick=1000,
            title="Remuneração (R$)"
        ),
        xaxis_title="Nível Profissional",
        showlegend=False
    )

    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Colunas 'remuneracao' ou 'nivel_profissional' não estão disponíveis.")

# Exibição do CV
st.subheader("Visualizar Currículo (cv_pt)")
if "nome" in df.columns and "cv_pt" in df.columns:
    nome = st.selectbox("Selecione um candidato", df["nome"].dropna().unique())
    cv = df[df["nome"] == nome]["cv_pt"].values[0]
    st.text_area("Currículo em Português", value=cv, height=300)
else:
    st.warning("Colunas 'nome' ou 'cv_pt' não estão disponíveis.")
