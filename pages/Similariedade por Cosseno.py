import json
import gdown
import streamlit as st
import pandas as pd
from datetime import datetime
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords

# Função para baixar e carregar o JSON do Google Drive
@st.cache_data
def load_data_from_drive():
    # URLs dos arquivos no Google Drive
    url_applicants = "https://drive.google.com/uc?id=1CHv4tvbiLRUbqLZGGMAQdLhelUy-tQI3"
    url_vagas = "https://drive.google.com/uc?id=1b9uU-izFPVxdBePzWLbY50jq_XDwLsgl"
    url_prospects = "https://drive.google.com/uc?id=1RxZ7raYToWNPoqOlmqs7p5R_NnaMv0xB"
    
    # Caminhos locais para salvar os arquivos
    output_applicants = "applicants.json"
    output_vagas = "vagas.json"
    output_prospects = "prospects.json"
    
    # Baixar os arquivos
    gdown.download(url_applicants, output_applicants, quiet=False)
    gdown.download(url_vagas, output_vagas, quiet=False)
    gdown.download(url_prospects, output_prospects, quiet=False)
    
    # Carregar os arquivos JSON com tratamento de codificação
    try:
        with open(output_applicants, 'r', encoding='ISO-8859-1') as f:
            applicants = json.load(f)
        with open(output_vagas, 'r', encoding='ISO-8859-1') as f:
            vagas = json.load(f)
        with open(output_prospects, 'r', encoding='ISO-8859-1') as f:
            prospects = json.load(f)
    except UnicodeDecodeError as e:
        st.error(f"Erro de codificação ao carregar os dados: {e}")
        return None, None, None
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None, None, None

    return prospects, vagas, applicants

# Função para calcular a idade
def calcular_idade(data_nascimento):
    try:
        nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d')
        today = datetime.today()
        return today.year - nascimento.year - ((today.month, today.day) < (nascimento.month, nascimento.day))
    except:
        return 0

# Função para extrair frases de um CV
def extrair_frases_cv(texto):
    if not isinstance(texto, str):
        return []
    texto = texto.replace('•', '.').replace('–', '-').replace('\xad', '-')
    frases = re.split(r'\n+|\. +|\.$', texto)
    return [frase.strip() for frase in frases if frase.strip()]

# Função principal do Streamlit
def main():
    st.title("🔍 Buscador de Candidatos por Similaridade de Perfil Completo")
    
    # Carregar os dados
    prospects, vagas, applicants = load_data_from_drive()
    
    if prospects is None or vagas is None or applicants is None:
        st.stop()  # Interrompe a execução se houver erro no carregamento dos dados
    
    # Preparar os dados dos candidatos
    ap = pd.DataFrame(applicants)
    ap['nome'] = ap['informacoes_pessoais'].apply(lambda x: x.get('nome', ''))
    ap['idade'] = ap['informacoes_pessoais'].apply(lambda x: calcular_idade(x.get('data_nascimento', '0000-00-00')))
    ap['sexo'] = ap['informacoes_pessoais'].apply(lambda x: x.get('sexo', ''))
    ap['estado_civil'] = ap['informacoes_pessoais'].apply(lambda x: x.get('estado_civil', ''))
    ap['pcd'] = ap['informacoes_pessoais'].apply(lambda x: x.get('pcd', ''))
    ap.fillna("Não Informado", inplace=True)

    # Extração de frases do CV
    ap['cv_pt_lista'] = ap['cv_pt'].apply(extrair_frases_cv)

    # Extrair campos de interesse do CV
    campos_info = [
        'titulo_profissional',
        'conhecimentos_tecnicos',
        'certificacoes',
        'nivel_profissional',
        'remuneracao'
    ]
    info_extraida = ap['informacoes_profissionais'].apply(pd.Series)[campos_info]
    info_extraida1 = ap['formacao_e_idiomas'].apply(pd.Series)[['nivel_academico','nivel_ingles','nivel_espanhol','outro_idioma']]
    info_extraida2 = ap['infos_basicas'].apply(pd.Series)[['objetivo_profissional','local']]

    # Junta as novas colunas ao DataFrame
    ap = pd.concat([ap, info_extraida, info_extraida1, info_extraida2], axis=1)
    ap = ap.drop(['informacoes_pessoais','informacoes_profissionais','formacao_e_idiomas','infos_basicas'], axis=1)

    # Criar o DataFrame de candidatos
    candidatos = ap[['nome', 'idade', 'estado_civil', 'local', 'pcd', 'titulo_profissional', 'conhecimentos_tecnicos', 
                     'certificacoes', 'nivel_profissional', 'nivel_academico', 'nivel_ingles', 'nivel_espanhol', 
                     'outro_idioma', 'objetivo_profissional', 'remuneracao', 'cv_pt']].reset_index()
    candidatos.rename(columns={'index': 'id'}, inplace=True)

    # Entrada de texto para a descrição da vaga
    vaga_input = st.text_area("Descreva a vaga desejada:")

    if vaga_input:
        # Configuração para o processamento de linguagem natural
        nltk.download('stopwords')
        stopwords_pt = stopwords.words('portuguese')

        # Vetorização do texto da vaga
        vectorizer = TfidfVectorizer(stop_words=stopwords_pt)
        tfidf_matrix = vectorizer.fit_transform([vaga_input] + candidatos["cv_pt"].tolist())

        # Calcular a similaridade
        vaga_vector = tfidf_matrix[0]
        cv_vectors = tfidf_matrix[1:]
        scores = cosine_similarity(vaga_vector, cv_vectors).flatten()

        # Extrair palavras-chave relevantes para cada CV
        feature_names = vectorizer.get_feature_names_out()
        keywords_por_cv = []
        for vec in cv_vectors:
            top_indices = vec.toarray().argsort()[0][-5:][::-1]
            top_keywords = [feature_names[i] for i in top_indices if vec[0, i] > 0]
            keywords_por_cv.append(", ".join(top_keywords))

        # Criar DataFrame com resultados
        df_resultado = candidatos.copy()
        df_resultado["similaridade"] = scores
        df_resultado["palavras_chave"] = keywords_por_cv

        # Ordenar os top 10 candidatos com maior similaridade
        df_top10 = df_resultado.sort_values(by="similaridade", ascending=False).head(10)

        # Exibir os resultados
        colunas_exibir = ["id", "nome", "idade", "estado_civil", "local", "palavras_chave", "similaridade"]
        st.subheader("🧠 Top 10 Candidatos mais compatíveis:")
        st.dataframe(df_top10[colunas_exibir], use_container_width=True)

if __name__ == "__main__":
    main()
