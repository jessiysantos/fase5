import streamlit as st
import sys
import os

# Adicionando o diretório 'pages' ao caminho de busca de módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'pages'))

# Configuração da página
st.set_page_config(page_title="Página inicial", page_icon=":guardsman:", layout="wide")

# Título
st.title("🎯 Sistema de Recomendação de Candidatos")
st.markdown("Selecione uma aba no menu lateral para começar.")
