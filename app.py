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
        titulo_profissional = candidate_data['informacoes_profissionais']['titulo_profissional']
        area_atuacao = candidate_data['informacoes_profissionais']['area_atuacao']
        conhecimentos_tecnicos = candidate_data['informacoes_profissionais']['conhecimentos_tecnicos']
        nome = candidate_data['infos_basicas']['nome']
        email = candidate_data['infos_basicas']['email']
        return {
            'nome': nome,
            'email': email,
            'titulo_profissional': titulo_profissional,
            'area_atuacao': area_atuacao,
            'conhecimentos_tecnicos': conhecimentos_tecnicos
        }
    except KeyError:
        return None

# Função para encontrar os candidatos com maior similaridade
def find_best_matches(vaga_description, data):
    candidates_info = []
    descriptions = []
    
    # Extraímos os dados dos candidatos
    for key, candidate_data in data.items():
        candidate_info = extract_candidate_info(candidate_data)
        if candidate_info:
            # Concatenamos os dados relevantes para formar uma descrição
            description = f"{candidate_info['titulo_profissional']} {candidate_info['area_atuacao']} {candidate_info['conhecimentos_tecnicos']}"
            candidates_info.append(candidate_info)
            descriptions.append(description)
    
    # Adiciona a descrição da vaga à lista de descrições
    descriptions.append(vaga_description)
    
    # Aplica o TF-IDF para transformar as descrições em vetores numéricos
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(descriptions)
    
    # Calcula a similaridade de cosseno entre a descrição da vaga e as descrições dos candidatos
    cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    
    # Classifica os candidatos com base na similaridade
    similar_candidates = sorted(zip(cosine_similarities[0], candidates_info), reverse=True, key=lambda x: x[0])
    
    # Retorna os melhores matches com similaridade maior que 70%
    matches = []
    for similarity, candidate in similar_candidates:
        if similarity > 0.50:  # Similaridade maior que 50%
            matches.append({
                'nome': candidate['nome'],
                'email': candidate['email'],
                'titulo_profissional': candidate['titulo_profissional'],
                'area_atuacao': candidate['area_atuacao'],
                'conhecimentos_tecnicos': candidate['conhecimentos_tecnicos'],
                'similaridade': f"{similarity:.2f}"
            })
    
    return matches

# Interface Streamlit
st.title("Sistema de Sugestão de Candidatos")

# Campo de entrada para a descrição da vaga
vaga_description = st.text_area("Digite a descrição da vaga", "Implantação e manutenção de software")

# Botão para encontrar os melhores matches
if st.button('Encontrar Candidatos'):
    matches = find_best_matches(vaga_description, data)
    
    if matches:
        for match in matches:
            st.subheader(f"Nome: {match['nome']}")
            st.write(f"Email: {match['email']}")
            st.write(f"Título Profissional: {match['titulo_profissional']}")
            st.write(f"Área de Atuação: {match['area_atuacao']}")
            st.write(f"Conhecimentos Técnicos: {match['conhecimentos_tecnicos']}")
            st.write(f"Similaridade: {match['similaridade']}")
            st.write("---")
    else:
        st.write("Nenhum candidato com similaridade maior que 50% encontrado.")
