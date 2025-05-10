import requests
import pandas as pd
import io
import streamlit as st

def carregar_dados_drive(url, file_type='json'):
    try:
        # Realizar o download do arquivo
        response = requests.get(url)
        
        # Verificar se o download foi bem-sucedido
        if response.status_code == 200:
            # Depuração: Exibir o conteúdo da resposta para verificar o que está sendo retornado
            st.write("Conteúdo do arquivo completo (primeiros 1000 caracteres):")
            st.write(response.text[:1000])  # Exibe até 1000 caracteres para depuração

            # Verificar se o conteúdo retornado é uma página HTML de aviso de verificação de vírus
            if "Virus scan warning" in response.text:
                st.error("O arquivo contém um aviso de verificação de vírus. Tente baixar manualmente.")
                return None
            
            # Se for um arquivo JSON
            if file_type == 'json':
                try:
                    # Tenta processar o JSON
                    return pd.read_json(io.StringIO(response.text))
                except ValueError as e:
                    st.error(f"Erro ao processar o arquivo JSON: {str(e)}")
                    return None
            else:
                st.error(f"Formato de arquivo não suportado: {file_type}")
                return None
        else:
            st.error(f"Erro ao carregar o arquivo. Status: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")
        return None

# URLs fornecidas
url_vagas = "https://drive.google.com/uc?export=download&id=1U_H3lw1PUwitQxPhL_3HaOqll9KNabG9"
url_prospects = "https://drive.google.com/uc?export=download&id=1PV1VfdOUEUITazlZMfvZkvbzO6NS63xD"
url_applicants = "https://drive.google.com/uc?export=download&id=1CHv4tvbiLRUbqLZGGMAQdLhelUy-tQI3"

# Carregar os dados
dados_vagas = carregar_dados_drive(url_vagas, file_type='json')
dados_prospects = carregar_dados_drive(url_prospects, file_type='json')
dados_applicants = carregar_dados_drive(url_applicants, file_type='json')

# Se os dados forem carregados corretamente, você pode processá-los
if dados_vagas is not None:
    st.write("Dados das vagas carregados com sucesso!")
    st.write(dados_vagas)
else:
    st.error("Não foi possível carregar os dados das vagas.")

if dados_prospects is not None:
    st.write("Dados dos prospects carregados com sucesso!")
    st.write(dados_prospects)
else:
    st.error("Não foi possível carregar os dados dos prospects.")

if dados_applicants is not None:
    st.write("Dados dos applicants carregados com sucesso!")
    st.write(dados_applicants)
else:
    st.error("Não foi possível carregar os dados dos applicants.")
