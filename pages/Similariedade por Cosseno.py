import json
import streamlit as st
import gdown
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords

# 🌐 Título da Aplicação
st.set_page_config(page_title="Sugestão de Candidatos", layout="wide")
st.title("🔍 Sistema Inteligente de Sugestão de Candidatos")

# 📦 Downloads necessários
nltk.download('stopwords')
stopwords_pt = stopwords.words('portuguese')

# 📥 Carregamento dos Dados
@st.cache_data
def load_data_from_drive():
    url = "https://drive.google.com/uc?id=1CHv4tvbiLRUbqLZGGMAQdLhelUy-tQI3"
    output = "applicants.json"
    gdown.download(url, output, quiet=False)
    with open(output, 'r', encoding='utf-8') as f:
        return json.load(f)

data = load_data_from_drive()

# 🔑 Extração de palavras-chave do campo cv_pt
def extract_keywords(text, top_n=10):
    if not text or not isinstance(text, str):
        return ""

    # Limpeza simples
    text = text.lower().replace('\n', ' ')
    words = [w for w in text.split() if w not in stopwords_pt and len(w) > 2]

    if not words:
        return ""

    vectorizer = TfidfVectorizer(stop_words=stopwords_pt)
    try:
        tfidf_matrix = vectorizer.fit_transform([" ".join(words)])
    except ValueError:
        return ""

    tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
    sorted_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

    return " ".join([kw for kw, _ in sorted_keywords[:top_n]])


# 📄 Extração de Informações
def extract_candidate_info(candidate_data):
    try:
        cv_text = candidate_data['informacoes_profissionais'].get('cv_pt', '')
        keywords_cv = extract_keywords(cv_text)
        return {
            'nome': candidate_data['infos_basicas']['nome'],
            'email': candidate_data['infos_basicas']['email'],
            'titulo_profissional': candidate_data['informacoes_profissionais']['titulo_profissional'],
            'area_atuacao': candidate_data['informacoes_profissionais']['area_atuacao'],
            'conhecimentos_tecnicos': candidate_data['informacoes_profissionais']['conhecimentos_tecnicos'],
            'keywords_cv': keywords_cv  # <- Adiciona aqui
        }
    except KeyError:
        return None


# 🔎 Função de Similaridade
def find_top_10_matches(vaga_description, data):
    candidates_info = []
    descriptions = []

    for candidate_data in data.values():
        info = extract_candidate_info(candidate_data)
        if info:
            description = f"{info['titulo_profissional']} {info['area_atuacao']} {info['conhecimentos_tecnicos']} {info['keywords_cv']}"
            descriptions.append(description)
            candidates_info.append(info)

    descriptions.append(vaga_description)

    vectorizer = TfidfVectorizer(stop_words=stopwords_pt)
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]

    scored_candidates = sorted(zip(cosine_sim, candidates_info), reverse=True, key=lambda x: x[0])

    top_matches = []
    for similarity, candidate in scored_candidates:
        if similarity > 0.50:
            top_matches.append({
                'nome': candidate['nome'],
                'email': candidate['email'],
                'titulo_profissional': candidate['titulo_profissional'],
                'area_atuacao': candidate['area_atuacao'],
                'conhecimentos_tecnicos': candidate['conhecimentos_tecnicos'],
                'similaridade': f"{similarity:.2f}"
            })
        if len(top_matches) == 10:
            break

    return top_matches

# 📋 Formulário de Entrada
st.markdown("<h3 style='color:#4CAF50;'>✍️ Descreva a vaga</h3>", unsafe_allow_html=True)
vaga_description = st.text_area("Digite a descrição da vaga", "Implantação e manutenção de Software")

# 🔘 Botão de ação
if st.button("🔍 Encontrar Candidatos"):
    top_matches = find_top_10_matches(vaga_description, data)

    if top_matches:
        st.markdown("<h3 style='color:#4CAF50;'>👥 Candidatos Recomendados</h3>", unsafe_allow_html=True)
        for i, match in enumerate(top_matches, 1):
            with st.container():
                st.markdown(f"<h4 style='color:#4CAF50;'> {i}. {match['nome']} </h4>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📧 **Email:** {match['email']}")
                    st.markdown(f"💼 **Título Profissional:** {match['titulo_profissional']}")
                    st.markdown(f"📍 **Área de Atuação:** {match['area_atuacao']}")
                with col2:
                    st.markdown(f"🧠 **Conhecimentos Técnicos:** {match['conhecimentos_tecnicos']}")
                    st.markdown(f"✅ **Similaridade:** `{match['similaridade']}`")
                    st.markdown(f"🔑 **Palavras-chave do CV:** `{match['keywords_cv']}`")
                st.markdown("---")
    else:
        st.warning("⚠️ Nenhum candidato com similaridade maior que 0.50 foi encontrado.")
