import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Carregar dados diretamente do GitHub
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/jessiysantos/fase5/main/candidatos.csv"
    return pd.read_csv(url)

df = carregar_dados()

# Mensagem de boas-vindas
st.title("Dashboard de Análise de Candidatos")

st.markdown("""
### 👋 Seja bem-vindo!
Este painel permite explorar os dados dos candidatos por meio de gráficos interativos.

← Utilize as **abas laterais** para acessar outras funcionalidades, como a **pesquisa por similaridade** entre perfis e vagas.
""")

# Seletor de campo para gráfico de distribuição
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
    fig = px.bar(top_categorias, x=top_categorias.index, y=top_categorias.values,
                 labels={"x": opcao, "y": "Frequência"},
                 title=f"Top 20 valores mais frequentes de {opcao}")

st.plotly_chart(fig, use_container_width=True)

# Gráfico de remuneração com média e eixo ajustado
if "remuneracao" in df.columns and "nivel_profissional" in df.columns:
    # Calcular média salarial por nível profissional
    media_salarial = df.groupby("nivel_profissional")["remuneracao"].mean().reset_index()

    # Gráfico de boxplot
    fig2 = px.box(df, x="nivel_profissional", y="remuneracao", title="Remuneração por Nível Profissional")

    # Adicionar linha de média
    fig2.add_trace(
        go.Scatter(
            x=media_salarial["nivel_profissional"],
            y=media_salarial["remuneracao"],
            mode="lines+markers",
            name="Média Salarial",
            line=dict(color="red", dash="dash")
        )
    )

    # Ajustar eixo Y
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

# Visualização do currículo
st.subheader("Visualizar Currículo (cv_pt)")
nome_selecionado = st.selectbox("Selecione um candidato", df["nome"].unique())

cv = df[df["nome"] == nome_selecionado]["cv_pt"].values[0]
st.text_area("Currículo (PT)", value=cv, height=300)
