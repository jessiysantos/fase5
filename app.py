import streamlit as st

# Configuração da página
st.set_page_config(page_title="Página inicial", page_icon=":guardsman:", layout="wide")

# Título
st.title("🎯 Sistema de Recomendação de Candidatos")
st.markdown("Selecione uma aba no menu lateral para começar.")

# Adicionando as abas (usando selectbox ou radio)
aba = st.selectbox('Escolha o módulo:', ['Por Similaridade Coseno', 'Por NPL'])

# Exibindo o conteúdo baseado na aba selecionada
if aba == 'Por Similaridade Coseno':
    st.subheader('Módulo: Similaridade Coseno')
    st.write("Aqui vai o conteúdo do módulo de similaridade cosseno.")
    # Você pode importar e chamar funções ou rodar o script relacionado aqui.
    # Por exemplo:
    import por_similaridade_cosseno
    por_similaridade_cosseno.run()
elif aba == 'Por NPL':
    st.subheader('Módulo: NPL')
    st.write("Aqui vai o conteúdo do aplicativo Streamlit.")
    # Da mesma forma, importe e execute o script desejado:
    import streamlit_app
    streamlit_app.run()
