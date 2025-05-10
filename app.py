import json
import streamlit as st
import gdown
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Função para baixar e carregar o JSON do Google Drive
@st.cache_data
def load_data_from_drive():
    url = "https://drive.google.com/uc?id=1CHv4tvbiLRUbqLZGGMAQdLhelUy-tQI3"
    output = "applicants.json"
    gdown.download(url, output, quiet=False)
    with open(output, 'r', encoding='utf-8') as f:
        return json.load(f)

data = load_data_from_drive()

# Função para extrair os dados relevantes de cada candidato
def extract_candidate_info(candidate_data):
    try:
        return {
            'nome': candidate_data['infos_basicas']['nome'],
            'email': candidate_data['infos_basicas']['email'],
            'titulo_profissional': candidate_data['informacoes_profissionais']['titulo_profissional'],
            'area_atuacao': candidate_data['informacoes_profissionais']['area_atuacao'],
            'conhecimentos_tecnicos': candidate_data['informacoes_profissionais']['conhecimentos_tecnicos']
        }
    except KeyError:
        return None

# Função para encontrar os 10 candidatos mais similares
def find_top_10_matches(vaga_description, data):
    candidates_info = []
    descriptions = []

    # Extrai e monta as descrições dos candidatos
    for candidate_data in data.values():
        info = extract_candidate_info(candidate_data)
        if info:
            description = f"{info['titulo_profissional']} {info['area_atuacao']} {info['conhecimentos_tecnicos']}"
            descriptions.append(description)
            candidates_info.append(info)

    # Adiciona a descrição da vaga
    descriptions.append(vaga_description)

    # Vetorização com TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    # Calcula similaridade
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]

    # Combina com os dados dos candidatos
    scored_candidates = sorted(zip(cosine_sim, candidates_info), reverse=True, key=lambda x: x[0])

    # Retorna os top 10
    top_matches = []
    for similarity, candidate in scored_candidates[:10]:
        top_matches.append({
            'nome': candidate['nome'],
            'email': candidate['email'],
            'titulo_profissional': candidate['titulo_profissional'],
            'area_atuacao': candidate['area_atuacao'],
            'conhecimentos_tecnicos': candidate['conhecimentos_tecnicos'],
            'similaridade': f"{similarity:.2f}"
        })

    return top_matches

# Interface Streamlit
st.title("Sistema de Sugestão de Candidatos")

vaga_description = st.text_area("Digite a descrição da vaga:", "Implantação e manutenção de software")

if st.button("Encontrar Candidatos"):
    top_matches = find_top_10_matches(vaga_description, data)

    if top_matches:
        st.subheader("Top 10 Candidatos Mais Compatíveis:")
        for i, match in enumerate(top_matches, 1):
            st.markdown(f"### {i}. {match['nome']}")
            st.write(f"**Email:** {match['email']}")
            st.write(f"**Título Profissional:** {match['titulo_profissional']}")
            st.write(f"**Área de Atuação:** {match['area_atuacao']}")
            st.write(f"**Conhecimentos Técnicos:** {match['conhecimentos_tecnicos']}")
            st.write(f"**Similaridade:** {match['similaridade']}")
            st.markdown("---")
    else:
        st.write("Nenhum candidato encontrado.")
