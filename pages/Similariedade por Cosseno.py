import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import gdown

nltk.download('stopwords')
stopwords_pt = stopwords.words('portuguese')

# Carregar os dados
df_candidatos = pd.read_csv('candidatos.csv')



# Lista de colunas a serem usadas como features textuais
colunas_features = [
    "local", "pcd", "titulo_profissional",
    "conhecimentos_tecnicos", "certificacoes", "nivel_profissional",
    "nivel_academico", "nivel_ingles", "nivel_espanhol",
    "objetivo_profissional", "remuneracao", "cv_pt"
]

# Criar uma nova coluna com todas as informações combinadas como texto
df_candidatos["texto_completo"] = df_candidatos[colunas_features].astype(str).agg(" ".join, axis=1)

# =========================
# Streamlit Interface
# =========================
st.title("🔍 Buscador de Candidatos por Similaridade de Perfil Completo")

vaga_input = st.text_area("Descreva a vaga desejada:")

if vaga_input:
    # Vetorização
    vectorizer = TfidfVectorizer(stop_words=stopwords_pt)
    tfidf_matrix = vectorizer.fit_transform([vaga_input] + df_candidatos["texto_completo"].tolist())

    # Similaridade
    vaga_vector = tfidf_matrix[0]
    cv_vectors = tfidf_matrix[1:]
    scores = cosine_similarity(vaga_vector, cv_vectors).flatten()

    # Extrair palavras-chave mais relevantes do candidato
    feature_names = vectorizer.get_feature_names_out()
    keywords_por_cv = []
    for vec in cv_vectors:
        top_indices = vec.toarray().argsort()[0][-5:][::-1]
        top_keywords = [feature_names[i] for i in top_indices if vec[0, i] > 0]
        keywords_por_cv.append(", ".join(top_keywords))

    # Criar DataFrame de resultados
    df_resultado = df_candidatos.copy()
    df_resultado["similaridade"] = scores
    df_resultado["palavras_chave"] = keywords_por_cv

    # Ordenar os top 10 candidatos
    df_top10 = df_resultado.sort_values(by="similaridade", ascending=False).head(10)

    # Exibir colunas desejadas
    colunas_exibir = ["id", "nome", "idade", "estado_civil", "local", "palavras_chave", "similaridade"]
    st.subheader("🧠 Top 10 Candidatos mais compatíveis:")
    st.dataframe(df_top10[colunas_exibir], use_container_width=True)
