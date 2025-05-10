import streamlit as st
import sys
import os

# Adicionando o diretório 'pages' ao caminho de busca de módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))

# Configuração da página
st.set_page_config(page_title="Página inicial", page_icon=":guardsman:", layout="wide")

# Título
st.title("🎯 Sistema de Recomendação de Candidatos")
st.markdown("Selecione uma aba no menu lateral para começar.")

# Adicionando as abas na lateral (usando radio buttons)
aba = st.sidebar.radio("Escolha o módulo:", ['Similaridade por Cosseno', 'Similaridade por NPL'])

# Exibindo o conteúdo baseado na aba selecionada
if aba == 'Similaridade por Cosseno':
    st.subheader('Módulo: Similaridade por Cosseno')
    st.write("Aqui vai o conteúdo do módulo de similaridade cosseno.")
    # Você pode importar e chamar funções ou rodar o script relacionado aqui.
    import por_similaridade_cosseno
    por_similaridade_cosseno.run()
elif aba == 'Similaridade por NPL':
    st.subheader('Módulo: Similaridade por NPL')
    st.write("Aqui vai o conteúdo do módulo de similaridade por NPL.")
    # Importando o módulo 'streamlit_app' da pasta 'pages'
    exec(open("pages/streamlit_app.py").read())
