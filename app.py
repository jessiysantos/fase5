import streamlit as st

# Configuração inicial do aplicativo
st.set_page_config(
    page_title="FIAP Data Analytics",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
st.markdown('<h2><span style="color:#542DC2;">FIAP</span> Pós Tech – Projeto Decision Match Hub</h2>', unsafe_allow_html=True)


#  Boas-vindas com parágrafos separados e respiro
st.markdown("""
<h4 style="margin-bottom: 0.5rem;">Bem-vindo(a) ao Decision Match Hub</h4>

<p style="font-size: 1.05em; line-height: 1.6; margin-bottom: 1em;">
Este projeto foi desenvolvido especialmente para o <strong>Datathon da FIAP Pós Tech – Data Analytics</strong>, com base em um desafio real da empresa <strong>Decision</strong>, referência em recrutamento e alocação de talentos.
</p>

<div style="background-color:#F4F2FF; padding: 15px 20px; border-left: 5px solid #542DC2; border-radius: 6px;">
<p style="margin: 0 0 8px 0;"><strong>✨ Destaques da nossa solução:</strong></p>
<ul style="margin: 0; padding-left: 20px; font-size: 0.98em; line-height: 1.6; color: #333;">
    <li>🔹 Interação guiada por etapas e perguntas simples.</li>
    <li>🔹 Aplicação de filtros humanizados com linguagem natural.</li>
    <li>🔹 Cálculo de <strong>similaridade com IA</strong> e <strong>score ponderado explicável</strong>.</li>
</ul>
</div>
""", unsafe_allow_html=True)
st.markdown("")
st.info("**Nosso objetivo** é aplicar inteligência artificial para transformar o processo seletivo. Tornando a triagem mais eficiente, precisa e conectada ao perfil ideal de cada vaga.")

st.divider()
st.markdown("###### Uma solução inteligente de triagem de candidatos com apoio de IA")
st.markdown("""
<div style='display: flex; align-items: center; gap: 16px; margin-top: 30px; margin-bottom: 20px;'>
    <div style='font-size: 38px;'>🤖</div>
    <div>
        <h3 style='margin: 0; padding: 0;'>Este é o <span style="color:#542DC2">Assistente Decision</span></h3>
        <p style='margin: 4px 0 0 0; font-size: 15px; color: #444;'>
            Ele foi criado para ajudar você a encontrar os candidatos mais aderentes à sua vaga,
            aplicando filtros inteligentes e explicando cada etapa do processo.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Seção "O que você encontrará"
col1, col2 = st.columns([1, 5])

with col1:
    st.image("img/Decision.png", width=100)

with col2:
    st.markdown("#### O que você encontrará neste projeto?")
st.markdown("""        
<div style="display: flex; flex-direction: column; gap: 10px;">
    <div style="background-color: #FB74AA; padding: 20px; border-radius: 10px; border-left: 8px solid #FD0260;">
        <h6 style="color:white;">🤖 IA na Triagem</h6>
        <p style="color:#4D4C4C; font-size: 16px;">A ferramenta permite aplicar filtros inteligentes e ranquear candidatos com base em similaridade textual entre perfis e descrições de vaga.</p>
    </div>
    <div style="background-color: #A28DE4; padding: 20px; border-radius: 10px; border-left: 8px solid #4E2ECF;">
        <h6 style="color:white;">📊 Score Ponderado</h6>
        <p style="color:#4D4C4C; font-size: 16px;">Os candidatos são avaliados com base em quatro critérios principais: título, área de atuação, conhecimentos técnicos e faixa salarial.</p>
    </div>
    <div style="background-color: #93D9F5; padding: 20px; border-radius: 10px; border-left: 8px solid #00B6F0;">
        <h6 style="color:white;">📂 Histórico de Participações</h6>
        <p style="color:#4D4C4C; font-size: 16px;">Veja o histórico de participação dos candidatos em vagas anteriores e o status de cada processo.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Integrantes do grupo
st.markdown("##### 💻 Integrantes do Grupo")
st.markdown("**FIAP Pós Tech – Data Analytics, 2025. Grupo 13.**")

col1, col2 = st.columns(2)
with col1:
    st.markdown("- **Anderson Cardoso Pinto de Souza - RM: 357106**")
    st.markdown("- **Fernanda Nogueira Castilho – RM: 357000**")
    st.markdown("- **Jéssica da Silva Santos - RM: 356949**")
with col2:
    st.markdown("- **Nicholas Todescan Franco de Camargo - RM: 357423**")
    st.markdown("- **Wagner Silveira Santos - RM: 357110**")

if st.button("👉 Acesse o projeto completo"):
    st.success("Use o menu lateral para navegar pelas funcionalidades.")

# Rodapé estilizado
st.markdown("""
    <div style="text-align: center; margin-top: 30px; color: #999;">
        Criado pela turma <strong>6DTAT de Data Analytics</strong>, FIAP Pós Tech.
    </div>
""", unsafe_allow_html=True)

# CSS personalizado
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #542DC2;
        color: white;
        font-weight: bold;
        padding: 10px 16px;
        border-radius: 8px;
    }
    div.stButton > button:first-child:hover {
        background-color: #3b1e96;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
        .info-box {
            background-color: #E7E5E5;
            border-left: 5px solid #582FC7;
            padding: 15px;
            border-radius: 8px;
            color: #4D4C4C;
        }
        h2, h3, h6 {
            font-family: Arial, sans-serif;
        }
        .footer {
            font-size: 14px;
            margin-top: 20px;
            color: #999;
        }
    </style>
""", unsafe_allow_html=True)
