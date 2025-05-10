import pandas as pd
import re
from datetime import datetime

# Carregar os dados
@st.cache_data
def load_data_from_drive():
    url = "https://drive.google.com/uc?id=1CHv4tvbiLRUbqLZGGMAQdLhelUy-tQI3"
    output = "applicants.json"
    gdown.download(url, output, quiet=False)
    with open(output, 'r', encoding='utf-8') as f:
        return json.load(f)

data = load_data_from_drive()
# Extraindo as informações para novas colunas
ap = applicants.T
ap['nome'] = ap['informacoes_pessoais'].apply(lambda x: x.get('nome', ''))
ap['idade'] = ap['informacoes_pessoais'].apply(lambda x: calcular_idade(x.get('data_nascimento', '0000-00-00')))
ap['sexo'] = ap['informacoes_pessoais'].apply(lambda x: x.get('sexo', ''))
ap['estado_civil'] = ap['informacoes_pessoais'].apply(lambda x: x.get('estado_civil', ''))
ap['pcd'] = ap['informacoes_pessoais'].apply(lambda x: x.get('pcd', ''))
ap.fillna("Não Informado")
# Função para extrair frases de um texto de CV
def extrair_frases_cv(texto):
    if not isinstance(texto, str):
        return []
    # Substitui marcadores e quebras em pontuação simples
    texto = texto.replace('•', '.').replace('–', '-').replace('\xad', '-')
    # Quebra por novas linhas ou por ponto final seguido de espaço
    frases = re.split(r'\n+|\. +|\.$', texto)
    # Remove espaços extras e frases vazias
    return [frase.strip() for frase in frases if frase.strip()]
# Aplica a função ao DataFrame 'ap' na coluna 'cv_pt'
ap['cv_pt_lista'] = ap['cv_pt'].apply(extrair_frases_cv)
# Lista dos campos que você quer extrair
campos_info = [
    'titulo_profissional',
    'conhecimentos_tecnicos',
    'certificacoes',
    'nivel_profissional',
    'remuneracao'
]
# Extrai os campos como colunas novas
info_extraida = ap['informacoes_profissionais'].apply(pd.Series)[campos_info]
info_extraida1 = ap['formacao_e_idiomas'].apply(pd.Series)[['nivel_academico','nivel_ingles','nivel_espanhol','outro_idioma']]
info_extraida2 = ap['infos_basicas'].apply(pd.Series)[['objetivo_profissional','local']]

# Junta ao DataFrame original
ap = pd.concat([ap, info_extraida,info_extraida1,info_extraida2], axis=1)
ap = ap.drop(['informacoes_pessoais','informacoes_profissionais','formacao_e_idiomas','infos_basicas'],axis=1)
candidatos = ap[['nome','idade','estado_civil','local','pcd','titulo_profissional','conhecimentos_tecnicos','certificacoes','nivel_profissional','nivel_academico','nivel_ingles','nivel_espanhol','outro_idioma','objetivo_profissional','remuneracao','cv_pt']].reset_index()
candidatos = pd.DataFrame(candidatos)
candidatos.rename(columns={'index':'id'},inplace=True)

###################### STREAMLIT ############################

import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
stopwords_pt = stopwords.words('portuguese')

df_candidatos = candidatos

# Lista de colunas a serem usadas como features textuais
colunas_features = [
    "idade", "estado_civil", "local", "pcd", "titulo_profissional",
    "conhecimentos_tecnicos", "certificacoes", "nivel_profissional",
    "nivel_academico", "nivel_ingles", "nivel_espanhol", "outro_idioma",
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
