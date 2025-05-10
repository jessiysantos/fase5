import streamlit as st
import sys
import os
import pandas as pd
import json
import requests
import io

# Adicionando o diretório 'pages' ao caminho de busca de módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'pages'))

# Configuração da página
st.set_page_config(page_title="Página inicial", page_icon=":guardsman:", layout="wide")

# Título
st.title("🎯 Sistema de Recomendação de Candidatos")
st.markdown("Selecione uma aba no menu lateral para começar.")

# Função para carregar arquivos do Google Drive
def carregar_dados_drive(url):
    # Realizar o download do arquivo do Google Drive
    file_id = url.split('id=')[-1]
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    response = requests.get(download_url)
    
    if response.status_code == 200:
        try:
            # Tenta carregar como JSON e normalizar
            return pd.read_json(io.StringIO(response.text))
        except ValueError as e:
            st.error(f"Erro ao processar o arquivo JSON: {str(e)}")
            return None
    else:
        st.error("Erro ao carregar o arquivo.")
        return None

# URLs dos arquivos no Google Drive
url_applicants = "https://drive.google.com/uc?id=1CHv4tvbiLRUbqLZGGMAQdLhelUy-tQI3"
url_vagas = "https://drive.google.com/uc?id=1b9uU-izFPVxdBePzWLbY50jq_XDwLsgl"
url_prospects = "https://drive.google.com/uc?id=1RxZ7raYToWNPoqOlmqs7p5R_NnaMv0xB"

# Função para carregar as bases de dados com cache
@st.cache_data
def carregar_dados():
    applicants = carregar_dados_drive(url_applicants)
    vagas = carregar_dados_drive(url_vagas)
    prospects = carregar_dados_drive(url_prospects)
    
    # Verificação para garantir que as bases foram carregadas corretamente
    if applicants is None or vagas is None or prospects is None:
        st.error("Houve um erro ao carregar as bases de dados.")
    return prospects, vagas, applicants

# Carregar as bases de dados
prospects, vagas, applicants = carregar_dados()

# Verificação de carregamento
if applicants is not None and vagas is not None and prospects is not None:
    st.success("Bases de dados carregadas com sucesso!")
else:
    st.error("Houve um erro ao carregar as bases de dados.")

