import json
import streamlit as st
from sentence_transformers import SentenceTransformer, util

@st.cache_data
def load_applicants_data():
    with open("dados/applicants.json", 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_jobs_data():
    with open("dados/vagas.json", 'r', encoding='utf-8') as f:
        return json.load(f)

applicants_data = load_applicants_data()
jobs_data = load_jobs_data()
applicants_data = dict(list(applicants_data.items())[:200])

def extract_candidate_info(candidate_data):
    try:
        info = {
            'nome': candidate_data['infos_basicas'].get('nome', ''),
            'email': candidate_data['infos_basicas'].get('email', ''),
            'objetivo_profissional': candidate_data['infos_basicas'].get('objetivo_profissional', ''),
            'local': candidate_data['infos_basicas'].get('local', ''),
            'titulo_profissional': candidate_data['informacoes_profissionais'].get('titulo_profissional', ''),
            'area_atuacao': candidate_data['informacoes_profissionais'].get('area_atuacao', ''),
            'conhecimentos_tecnicos': candidate_data['informacoes_profissionais'].get('conhecimentos_tecnicos', ''),
            'nivel_profissional': candidate_data['informacoes_profissionais'].get('nivel_profissional', ''),
            'certificacoes': candidate_data['informacoes_profissionais'].get('certificacoes', ''),
            'outras_certificacoes': candidate_data['informacoes_profissionais'].get('outras_certificacoes', ''),
            'remuneracao': candidate_data['informacoes_profissionais'].get('remuneracao', ''),
            'nivel_academico': candidate_data['formacao_e_idiomas'].get('nivel_academico', ''),
            'instituicao_ensino': candidate_data['formacao_e_idiomas'].get('instituicao_ensino_superior', ''),
            'cursos': candidate_data['formacao_e_idiomas'].get('cursos', ''),
            'ano_conclusao': candidate_data['formacao_e_idiomas'].get('ano_conclusao', ''),
            'nivel_ingles': candidate_data['formacao_e_idiomas'].get('nivel_ingles', ''),
            'nivel_espanhol': candidate_data['formacao_e_idiomas'].get('nivel_espanhol', ''),
            'fonte_indicacao': candidate_data['informacoes_pessoais'].get('fonte_indicacao', ''),
            'cv': candidate_data.get('cv_pt', ''),
            'cargo_atual': candidate_data.get('cargo_atual', {})
        }
        return info
    except KeyError:
        return None

def build_candidate_description(info):
    description = f"""
    Nome: {info['nome']}
    Título Profissional: {info['titulo_profissional']}
    Objetivo Profissional: {info['objetivo_profissional']}
    Área de Atuação: {info['area_atuacao']}
    Local: {info['local']}
    Nível Profissional: {info['nivel_profissional']}
    Conhecimentos Técnicos: {info['conhecimentos_tecnicos']}
    Certificações: {info['certificacoes']}
    Outras Certificações: {info['outras_certificacoes']}
    Cursos: {info['cursos']}
    Instituição de Ensino: {info['instituicao_ensino']}
    Ano de Conclusão: {info['ano_conclusao']}
    Nível Acadêmico: {info['nivel_academico']}
    Nível de Inglês: {info['nivel_ingles']}
    Nível de Espanhol: {info['nivel_espanhol']}
    Expectativa Salarial: {info['remuneracao']}
    Fonte de Indicação: {info['fonte_indicacao']}
    """
    if info['cargo_atual']:
        description += f"\nCargo Atual: {info['cargo_atual']}"
    return description.strip()

def build_job_description(job_id, jobs_data):
    job = jobs_data.get(job_id)
    if job:
        info = job.get('informacoes_basicas', {})
        perfil = job.get('perfil_vaga', {})
        description = f"""
        Título da Vaga: {info.get('titulo_vaga', '')}
        Cliente: {info.get('cliente', '')}
        Tipo de Contratação: {info.get('tipo_contratacao', '')}
        Nível Profissional: {perfil.get('nivel profissional', '')}
        Nível Acadêmico: {perfil.get('nivel_academico', '')}
        Nível Inglês: {perfil.get('nivel_ingles', '')}
        Nível Espanhol: {perfil.get('nivel_espanhol', '')}
        Área de Atuação: {perfil.get('areas_atuacao', '')}
        Principais Atividades: {perfil.get('principais_atividades', '')}
        Competências Técnicas: {perfil.get('competencia_tecnicas_e_comportamentais', '')}
        Observações: {perfil.get('demais_observacoes', '')}
        """
        return description.strip()
    return ""

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

def find_top_10_matches(vaga_description, applicants_data):
    candidates_info = []
    descriptions = []
    for candidate_data in applicants_data.values():
        info = extract_candidate_info(candidate_data)
        if info and (info['titulo_profissional'] or info['area_atuacao'] or info['conhecimentos_tecnicos']):
            descriptions.append(build_candidate_description(info))
            candidates_info.append(info)
    if not candidates_info:
        return []
    with st.spinner("Processando candidatos..."):
        candidate_embeddings = model.encode(descriptions, batch_size=8, convert_to_tensor=True)
    vaga_embedding = model.encode(vaga_description, convert_to_tensor=True)
    cosine_sim = util.pytorch_cos_sim(vaga_embedding, candidate_embeddings)[0]
    scored_candidates = sorted(zip(cosine_sim, candidates_info), reverse=True, key=lambda x: x[0].item())
    return [dict(candidate, similaridade=f"{similarity.item():.2f}") for similarity, candidate in scored_candidates if similarity.item() > 0.70][:10]

# ========================
# Streamlit App
# ========================
st.title("Sistema de Sugestão de Candidatos")

def reset_results():
    st.session_state.top_matches = None

job_options = [(key, job['informacoes_basicas'].get('titulo_vaga', '')) for key, job in jobs_data.items()]
job_choices = ["(Não selecionar vaga)"] + [f"{job_id} - {title}" for job_id, title in job_options]
selected_job = st.selectbox("Selecione uma vaga do jobs.json:", job_choices, key="job_select", on_change=reset_results)

if selected_job != "(Não selecionar vaga)":
    job_id = selected_job.split(" - ")[0]
    vaga_description = build_job_description(job_id, jobs_data)
    st.markdown("**Descrição da vaga selecionada:**")
    st.info(vaga_description)
else:
    vaga_description = st.text_area("Ou digite manualmente a descrição da vaga:", key="vaga_text", on_change=reset_results)

if "top_matches" not in st.session_state:
    st.session_state.top_matches = None

if st.button("Encontrar Candidatos"):
    st.session_state.top_matches = find_top_10_matches(vaga_description, applicants_data)

top_matches = st.session_state.top_matches

if st.session_state.top_matches is None:
    st.info("Clique em 'Encontrar Candidatos' para iniciar a busca.")
elif not st.session_state.top_matches:
    st.warning("Nenhum candidato com similaridade maior que 0.70 encontrado.")
else:
    salarios = []
    locais = set()

    for c in st.session_state.top_matches:
        try:
            salario = float(str(c['remuneracao']).replace("R$", "").replace(".", "").replace(",", ".").strip())
        except:
            salario = 0
        loc = c['local'].strip() if c['local'] else "(Local não informado)"
        locais.add(loc)
        if salario > 0:
            salarios.append(salario)

    st.subheader("📊 Visão Geral dos Candidatos Encontrados")
    locais_encontrados = sorted(list(locais))
    filtro_locais = st.multiselect("Filtrar candidatos por local:", locais_encontrados, default=locais_encontrados)

    if salarios:
        salario_min, salario_max = int(min(salarios)), int(max(salarios))
        faixa = (salario_min, salario_max) if salario_min == salario_max else st.slider(
            "Filtrar candidatos por faixa salarial (R$):",
            salario_min, salario_max,
            (salario_min, salario_max)
        )
    else:
        faixa = (0, float('inf'))
        st.write("Faixa Salarial: Não informada")

    for i, match in enumerate(st.session_state.top_matches, 1):
        try:
            salario_candidato = float(str(match['remuneracao']).replace("R$", "").replace(".", "").replace(",", ".").strip())
        except:
            salario_candidato = 0
        loc_candidato = match['local'].strip() if match['local'] else "(Local não informado)"
        if (not filtro_locais or loc_candidato in filtro_locais) and faixa[0] <= salario_candidato <= faixa[1]:
            st.markdown(f"## {i}. {match['nome']}")
            st.write(f"📧 **Email:** {match['email']}")
            st.write(f"🎯 **Objetivo:** {match['objetivo_profissional']}")
            st.write(f"💼 **Título Profissional:** {match['titulo_profissional']}")
            if match['cargo_atual']:
                st.write(f"📝 **Cargo Atual:** {match['cargo_atual']}")
            st.write(f"🏙️ **Local:** {match['local'] if match['local'] else 'Local não informado'}")
            st.write(f"📚 **Área de Atuação:** {match['area_atuacao']}")
            st.write(f"🎓 **Formação:** {match['nivel_academico']} - {match['cursos']} ({match['instituicao_ensino']})")
            st.write(f"📜 **Certificações:** {match['certificacoes']} | {match['outras_certificacoes']}")
            st.write(f"🛠️ **Conhecimentos Técnicos:** {match['conhecimentos_tecnicos']}")
            st.write(f"💰 **Expectativa Salarial:** {match['remuneracao']}")
            st.write(f"🌐 **Idiomas:** Inglês: {match['nivel_ingles']} | Espanhol: {match['nivel_espanhol']}")
            st.write(f"🔗 **Fonte de Indicação:** {match['fonte_indicacao']}")
            st.write(f"⭐ **Similaridade:** {match['similaridade']}")
            st.markdown("---")
