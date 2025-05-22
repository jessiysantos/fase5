import streamlit as st
import gdown
import json
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator
from sentence_transformers import util
import unicodedata
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Decision Match Hub", layout="wide")
st.image("img/Decision.png", width=100)


# ------------------- FUNÇÕES AUXILIARES ------------------- #

# Função auxiliar para formatar valores como percentual
def format_percent(value):
    return f"{round(value * 100)}%"

def normalize_text(text):
    import unicodedata
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower().strip()

def traduzir_para_portugues(texto):
    return GoogleTranslator(source='auto', target='pt').translate(texto)

def calcular_idade(data):
    if pd.isna(data):
        return None
    if isinstance(data, pd.Timestamp):
        nascimento = data
    else:
        try:
            nascimento = pd.to_datetime(data, errors="coerce")
            if pd.isna(nascimento):
                return None
        except:
            return None

    hoje = datetime.today()
    idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    return idade if 15 <= idade <= 90 else None

def avancar(pergunta, resposta, proxima_etapa):
    if resposta:
        st.session_state.mensagens.append({"usuario": "user", "texto": resposta})
    if pergunta:
        st.session_state.mensagens.append({"usuario": "assistant", "texto": pergunta})
    st.session_state.etapa = proxima_etapa
    st.rerun()


#---MOSTRAR RESULTADO---#

def mostrar_resultado():
    @st.cache_resource
    def load_model():
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")

    model = load_model()
    
    df_filtro = st.session_state.df_filtro

    if df_filtro.empty:
        st.warning("⚠️ Nenhum candidato encontrado com os filtros aplicados.")
        st.stop()

    # ① RESUMO + OPÇÃO DE RANQUEAMENTO
    #st.markdown("### 🎯 Agora você pode ranquear os candidatos com base na vaga desejada.")

    with st.expander("🤝 Ranquear candidatos com base na vaga ideal (opcional)", expanded=False):
        
        job_options = [(k, v["informacoes_basicas"]["titulo_vaga"]) for k, v in jobs_data.items()]
        job_choices = ["(Não selecionar vaga)"] + [f"{jid} - {titulo}" for jid, titulo in job_options]
        selected_job = st.selectbox("📄 Selecione uma vaga da base:", job_choices)

        if selected_job != "(Não selecionar vaga)":
            job_id = selected_job.split(" - ")[0]
            vaga_data = jobs_data.get(job_id, {})
            descricao_vaga = vaga_data.get("perfil_vaga", {}).get("principais_atividades", "")
            descricao_vaga = traduzir_para_portugues(descricao_vaga)
            
            st.markdown("**📄 Descrição da vaga selecionada:**")
            st.markdown(descricao_vaga if descricao_vaga else "_Sem descrição disponível._")

        else:
            descricao_vaga = st.text_area("📝 Ou cole a descrição da vaga manualmente:", height=180)
    
        salario_alvo = st.number_input(
            "💰 Informe a faixa salarial ideal para a vaga (opcional):",
            min_value=0,
            step=500,
            format="%d"
        )
        if salario_alvo > 0:
            st.session_state["salario_alvo"] = salario_alvo
        
        if st.button("🔎 Ranquear por similaridade com IA"):
            if not descricao_vaga.strip():
                st.warning("⚠️ Descrição da vaga está vazia.")
                st.stop()
            else:

                descricoes_candidatos = df_filtro.apply(lambda row: f"""
                    Título Profissional: {row['titulo_profissional']}
                    Área de Atuação: {row['area_atuacao']}
                    Conhecimentos Técnicos: {row['conhecimentos_tecnicos']}
                    Faixa Salarial: {row['remuneracao']}
                """, axis=1)

                vaga_emb = model.encode(normalize_text(descricao_vaga), convert_to_tensor=True)
                candidatos_emb = model.encode([normalize_text(d) for d in descricoes_candidatos], convert_to_tensor=True)
                similaridades = util.pytorch_cos_sim(vaga_emb, candidatos_emb)[0].cpu().numpy()

                df_filtro["score_similaridade"] = similaridades
                df_filtro = df_filtro.sort_values("score_similaridade", ascending=False).reset_index(drop=True)

                st.session_state.df_filtro = df_filtro
                st.session_state["card_index"] = 0
                st.session_state["vaga_emb"] = vaga_emb
                st.success("✅ Candidatos ranqueados com sucesso! Veja os 10 mais aderentes abaixo.")             
                #st.rerun()
    if "vaga_emb" not in st.session_state:
        st.info("ℹ️ Para visualizar o ranking, primeiro ranqueie os candidatos com base na vaga.")
        return
    vaga_emb = st.session_state["vaga_emb"]

    WEIGHTS = {
        "Título Profissional": 0.4,
        "Área de Atuação": 0.25,
        "Conhecimentos Técnicos": 0.25,
        "Faixa Salarial": 0.10
    }

                    
    def gerar_justificativa(scores):
        destaques = []
        alertas = []
        for fator, valor in scores.items():
            if valor >= 0.65:
                destaques.append(f"{fator} ({format_percent(valor)})")
            elif valor <= 0.30:
                alertas.append(f"{fator} ({format_percent(valor)})")

        justificativa = ""
        if destaques:
            justificativa += "✅ Destaques: " + ", ".join(destaques) + ". "
        if alertas:
            justificativa += "⚠️ Pontos de atenção: " + ", ".join(alertas) + "."

        return justificativa if justificativa else "—"

    top_10_exp = []

    for i, row in df_filtro.head(10).iterrows():
        fatores = {
            "Título Profissional": row["titulo_profissional"],
            "Área de Atuação": row["area_atuacao"],
            "Conhecimentos Técnicos": row["conhecimentos_tecnicos"],
            "Faixa Salarial": row["remuneracao"]
        }

        scores = {}
        total_score = 0

        for chave, texto in fatores.items():
            if chave == "Faixa Salarial":
                try:
                    salario = float(str(texto).replace("R$", "").replace(".", "").replace(",", "."))
                    alvo = st.session_state.get("salario_alvo", None)
                    if alvo:
                        score = max(0, 1 - abs(salario - alvo) / alvo)
                    else:
                        score = 0
                except:
                    score = 0
            else:
                texto = texto or ""
                score = float(util.pytorch_cos_sim(vaga_emb, model.encode(normalize_text(texto), convert_to_tensor=True))[0])
            scores[chave] = score
            total_score += score * WEIGHTS[chave]

        top_10_exp.append({
            "🏅 Posição": i + 1,
            "👤 Candidato": row["nome"],
            "⭐ Similaridade com a vaga (IA)": format_percent(row["score_similaridade"]),
            "🎓 Título (40%)": format_percent(scores["Título Profissional"]),
            "🧭 Área (25%)": format_percent(scores["Área de Atuação"]),
            "💻 Técnicos (25%)": format_percent(scores["Conhecimentos Técnicos"]),
            "💰 Faixa Salarial (10%)": format_percent(scores["Faixa Salarial"]),
            "📊 Score ponderado": format_percent(total_score),
            "📘 Justificativa": gerar_justificativa(scores)
        })

    st.markdown("## 📋 Top 10 candidatos mais aderentes à vaga")

    st.markdown("""
<details>
<summary style='font-size: 16px; '>🤖 <b>Assistente Decision:</b> Quer saber como o ranqueamento foi calculado?</summary>
<div style='margin-top: 10px; font-size: 15px;'>

Após aplicar os filtros, eu analisei os candidatos comparando quatro fatores principais com a descrição da vaga: 

- 🎓 <b>Título Profissional</b>: 40%
- 🧭 <b>Área de Atuação</b>: 25%
- 💻 <b>Conhecimentos Técnicos</b>: 25%
- 💰 <b>Faixa Salarial</b>: 10%

Esses pesos me ajudam a destacar os candidatos mais aderentes à vaga no topo da lista.

Você pode usar isso para entender, de forma transparente, por que cada candidato apareceu no ranking.             
</div>
</details>
""", unsafe_allow_html=True)
    
    st.markdown("""
<details>
<summary style='font-size: 16px;'>O que significa <b>similaridade com a vaga</b>?</summary>
<div style='margin-top: 10px; font-size: 15px;'>

Esse valor é gerado com base em <b>inteligência artificial</b>, considerando o <b>texto completo</b> do perfil do candidato.  
A IA compara esse conteúdo com a descrição da vaga e calcula uma similaridade entre <b>0% e 100%</b>.

✅ <b>Importante:</b>  
- Esse valor <u>não</u> é uma média dos fatores individuais.  
- Ele representa uma <b>medida geral da aderência textual</b> do candidato à vaga ideal.  
- É ele quem define a <b>ordem do ranking</b> exibido abaixo.

</div>
</details>
""", unsafe_allow_html=True)
    
    st.markdown(f"<div style='font-size: 12px; color: #888;'>ℹ️ <b>Nota:</b> Se algum fator aparece com 0%, isso indica que o candidato não informou esse dado ou que o conteúdo está distante do perfil da vaga e teve baixa similaridade.</div></b><br></div>", unsafe_allow_html=True)

    #Visualizar Top 10 Dataframe
    df_resultado = pd.DataFrame(top_10_exp)
    st.dataframe(df_resultado, use_container_width=True)
    
    st.markdown("#### Resumo Inteligente")
    st.info(f"""
    - 🔟 Exibindo os 10 mais aderentes entre {len(st.session_state.df_filtro)} candidatos filtrados.
    - 🎓 Média de similaridade (IA): **{round(st.session_state.df_filtro['score_similaridade'].mean()*100)}%**
    - 💰 Faixa salarial mais comum: **{st.session_state.df_filtro['remuneracao'].mode()[0]}**
    - 📍 Região predominante: **{st.session_state.df_filtro['estado'].mode()[0]}**
    """)

    # Base para o gráfico: top 10 ranqueados
    df_plot = st.session_state.df_filtro.head(10).copy()
    df_plot["similaridade"] = df_plot["score_similaridade"] * 100
    df_plot["candidato"] = df_plot["nome"]

    fig_scatter = px.scatter(
        df_plot,
        x="similaridade",
        y="candidato",
        size="similaridade",
        color="nivel_profissional",
        labels={
            "similaridade": "Similaridade com a Vaga (%)",
            "nivel_profissional": "Nível Profissional",
            "candidato": "Candidato"
        },
        hover_data=["cidade", "estado", "remuneracao"]
    )

    fig_scatter.update_layout(yaxis=dict(autorange="reversed"),showlegend=False)  # para ordenar do mais aderente no topo
    with st.expander("🎯 Top 10 Candidatos x Similaridade com a Vaga", expanded=False):
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    fig_bar = px.bar(
        df_resultado,
        x="📊 Score ponderado",
        y="👤 Candidato",
        orientation="h",
        color="📊 Score ponderado",
        color_continuous_scale="YlGnBu",
        labels={"📊 Score ponderado": "Score %"}
    )
    fig_bar.update_layout(yaxis=dict(autorange="reversed"))  # Candidato 1 no topo
    with st.expander("📈 Comparativo de Score Ponderado - Top 10", expanded=False):
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()    
    
    # Filtro por nome com controle de loop
    st.markdown("### 🔎 Procurar candidato pelo nome")
    
    nomes_disponiveis = st.session_state.df_filtro["nome"].dropna().unique().tolist()
    nome_selecionado = st.selectbox(
        "Selecione o nome do candidato:",
        ["(Selecionar)"] + nomes_disponiveis,
        index=0,
        key="filtro_nome"
    )
    
    # Controla para não entrar em loop
    if nome_selecionado != "(Selecionar)" and st.session_state.get("nome_filtrado") != nome_selecionado:
        indices = st.session_state.df_filtro.index[st.session_state.df_filtro["nome"] == nome_selecionado].tolist()
        if indices:
            st.session_state["card_index"] = indices[0]
            st.session_state["nome_filtrado"] = nome_selecionado
            st.rerun()         

    # EXIBIÇÃO DO CANDIDATO
    if "card_index" not in st.session_state:
        st.session_state["card_index"] = 0

    total = len(df_filtro)
    atual = st.session_state["card_index"] % total
    candidato = df_filtro.iloc[atual]

    fatores = {
        "Título Profissional": candidato["titulo_profissional"],
        "Área de Atuação": candidato["area_atuacao"],
        "Conhecimentos Técnicos": candidato["conhecimentos_tecnicos"],
        "Faixa Salarial": candidato["remuneracao"]
    }
    
    scores = {}
    for chave, texto in fatores.items():
        if chave == "Faixa Salarial":
            try:
                salario = float(str(texto).replace("R$", "").replace(".", "").replace(",", "."))
                alvo = st.session_state.get("salario_alvo", None)
                if alvo:
                    score = max(0, 1 - abs(salario - alvo) / alvo)
                else:
                    score = 0
            except:
                score = 0
        else:
            texto = texto or ""
            score = float(util.pytorch_cos_sim(st.session_state["vaga_emb"], model.encode(normalize_text(texto), convert_to_tensor=True))[0])
        scores[chave] = score

    st.markdown("---")
    st.markdown(f"##### Candidato {atual+1} de {total}")
    st.markdown(f"### 👤 {candidato['nome']}")
    # Layout lateral
    col_esq, col_dir = st.columns([3, 2])  # Coluna esquerda maior para as infos

    with col_esq:
        if "score_similaridade" in candidato:
            st.markdown(f"**⭐ Similaridade com a vaga:** `{candidato['score_similaridade']:.2f}`")
        st.write(f"📧 Email: {candidato['email']}")
        st.write(f"🎯 Objetivo: {candidato['objetivo_profissional']}")
        st.write(f"🎓 Formação: {candidato['nivel_academico']}")
        st.write(f"💬 Inglês: {candidato['nivel_ingles']} | Espanhol: {candidato['nivel_espanhol']}")
        st.write(f"💼 Título: {candidato['titulo_profissional']}")
        st.write(f"📈 Nível: {candidato['nivel_profissional']}")
        st.write(f"📍 Local: {candidato['cidade']}, {candidato['estado']}")

    with col_dir:
        #st.markdown("<div style='text-align:center; font-weight:600'>📊 Aderência por Fator</div>", unsafe_allow_html=True)
        st.markdown("📊 **Aderência por Fator**")
        # Radar Chart com legenda visível e menor tamanho
        fatores_radar = ["🎓 Título", "🧭 Área", "💻 Técnicos", "💰 Faixa Salarial"]
        valores_candidato = [
            scores["Título Profissional"],
            scores["Área de Atuação"],
            scores["Conhecimentos Técnicos"],
            scores["Faixa Salarial"]
        ]
        valores_ideais = [1.0] * len(fatores_radar)

        fig_radar = go.Figure()

        fig_radar.add_trace(go.Scatterpolar(
            r=valores_candidato,
            theta=fatores_radar,
            fill='toself',
            name="Candidato",
            line=dict(color="#4626C0")
        ))

        fig_radar.add_trace(go.Scatterpolar(
            r=valores_ideais,
            theta=fatores_radar,
            fill='toself',
            name="Perfil Ideal",
            line=dict(color="#00AEEF", dash="dash")
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    tickvals=[0.25, 0.5, 0.75, 1],
                    ticktext=["25%", "50%", "75%", "100%"]
                )
            ),
            width=350,
            height=320,
            showlegend=True,
            margin=dict(t=30, l=40, r=40, b=40),  # ⬅️ margens mais generosas para evitar cortes
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
                font=dict(size=11)
            
            )
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    
    
  #  if "score_similaridade" in candidato:
  #      st.markdown(f"**⭐ Similaridade com a vaga:** `{candidato['score_similaridade']:.2f}`")

  #  col_a, col_b = st.columns(2)
  #  with col_a:
  #      st.write(f"📧 Email: {candidato['email']}")
  #      st.write(f"🎯 Objetivo: {candidato['objetivo_profissional']}")
  #      st.write(f"🎓 Formação: {candidato['nivel_academico']}")
  #   st.write(f"💬 Inglês: {candidato['nivel_ingles']} | Espanhol: {candidato['nivel_espanhol']}")
  #  with col_b:
  #      st.write(f"💼 Título: {candidato['titulo_profissional']}")
  #      st.write(f"📈 Nível: {candidato['nivel_profissional']}")
  #      st.write(f"📍 Local: {candidato['cidade']}, {candidato['estado']}")

  #  st.text_area("📄 Currículo (preview)", value=candidato["cv_pt"][:1500], height=200, disabled=True)

    # ③ HISTÓRICO DE VAGAS
    st.markdown("### 📂 Histórico de Participação em Vagas")
    st.markdown("""<div style='margin-bottom:10px'>
    🟢 <span style='background-color:#d4edda; padding:3px 8px; border-radius:5px'>Contratado</span> &nbsp;
    🔵 <span style='background-color:#d1ecf1; padding:3px 8px; border-radius:5px'>Encaminhado</span> &nbsp;
    🔴 <span style='background-color:#f8d7da; padding:3px 8px; border-radius:5px'>Reprovado</span> &nbsp;
    🟠 <span style='background-color:#ffeeba; padding:3px 8px; border-radius:5px'>Desistente</span> &nbsp;
    ⚪️ <span style='background-color:#f0f0f0; padding:3px 8px; border-radius:5px'>Sem histórico</span>
    </div>""", unsafe_allow_html=True)

    achou = False
    for vaga_id, vaga_data in prospects.items():
        for p in vaga_data.get("prospects", []):
            if p["nome"].strip().lower() == candidato["nome"].strip().lower():
                achou = True
                status = p["situacao_candidado"]
                status_texto = status.lower()
                if any(kw in status_texto for kw in ["contratado", "admitido"]):
                    emoji, cor = "🟢", "#d4edda"
                elif any(kw in status_texto for kw in ["encaminhado", "enviado", "submetido", "prospect", "inscrito"]):
                    emoji, cor = "🔵", "#d1ecf1"
                elif any(kw in status_texto for kw in ["reprovado", "não aprovado", "nao aprovado", "rejeitado"]):
                    emoji, cor = "🔴", "#f8d7da"
                elif any(kw in status_texto for kw in ["desistente", "desistiu", "desistência", "sem interesse"]):
                    emoji, cor = "🟠", "#ffeeba"
                else:
                    emoji, cor = "⚪️", "#f0f0f0"
                st.markdown(f"""<div style='background-color:{cor}; padding:10px; border-radius:5px; margin-bottom:10px'>
<b>{emoji} Vaga:</b> {vaga_data['titulo']}<br>
<b>📆 Data:</b> {p['data_candidatura']}<br>
<b>📌 Situação:</b> {p['situacao_candidado']}<br>
<b>💬 Comentário:</b> {p['comentario'] or '—'}<br>
<b>👤 Recrutador:</b> {p['recrutador']}
</div>""", unsafe_allow_html=True)

    if not achou:
        st.markdown("<div style='background-color:#f0f0f0; padding:10px; border-radius:5px'>⚪️ Nenhum histórico encontrado para esse candidato.</div>", unsafe_allow_html=True)

    # ④ NAVEGAÇÃO ENTRE CANDIDATOS
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⬅️ Anterior", key="botao_anterior"):
            st.session_state["card_index"] = max(0, st.session_state["card_index"] - 1)
            st.rerun()

    with col_nav2:
        if st.button("Próximo ➡️", key="botao_proximo"):
            st.session_state["card_index"] = min(total - 1, st.session_state["card_index"] + 1)
            st.rerun()

# ------------------- CARREGAMENTO DE DADOS ------------------- #

@st.cache_data
def carregar_prospects():
    url = "https://drive.google.com/uc?id=1I7PN2XeaETuBjcED8BDbC8mYKtEFsRHM"
    output = "prospects.json"
    gdown.download(url, output, quiet=False)
    
    with open(output, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data
def load_jobs_data():
    url = "https://drive.google.com/uc?id=1teqXm-T5shxF5_fjxaTCJIKnOp8LPmMR"
    output = "vagas.json"
    gdown.download(url, output, quiet=False)

    with open(output, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def carregar_dados_parquet():
    df = pd.read_parquet("applicants_part3.parquet")

    # Converte e calcula idade
    df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce")
    df["idade"] = df["data_nascimento"].apply(calcular_idade)

    # Se a coluna existir, trata os valores; se não existir, cria com 0
    if "pcd" in df.columns:
        def eh_pcd(valor):
            if pd.isna(valor):
                return 0
            valor_str = str(valor).strip().lower()
            return int(valor_str in ["sim", "s", "pcd", "1", "sim.", "deficiente", "pessoa com deficiência"])
        df["pcd"] = df["pcd"].apply(eh_pcd)
    else:
        df["pcd"] = 0

    # Preenche apenas os campos ausentes com "Nenhum"
    campos_esperados = [
        "nome", "email", "cidade", "estado", "objetivo_profissional",
        "titulo_profissional", "area_atuacao", "conhecimentos_tecnicos",
        "nivel_profissional", "remuneracao", "nivel_academico", "nivel_ingles",
        "nivel_espanhol", "cv_pt"
    ]
    for campo in campos_esperados:
        if campo not in df.columns:
            df[campo] = "Nenhum"

    return df

# ------------------- INICIALIZAÇÃO DE SESSÃO ------------------- #
# Carregamento efetivo dos dados
# Lê os 3 arquivos separadamente
#part1 = pd.read_parquet("applicants_part1.parquet")
#part2 = pd.read_parquet("applicants_part2.parquet")
#part3 = pd.read_parquet("applicants_part3.parquet")

# Junta tudo em um único DataFrame
#df = pd.concat([part1, part2, part3], ignore_index=True)
#df = part1
df = carregar_dados_parquet()
prospects = carregar_prospects()
jobs_data = load_jobs_data()

total_sem_idade = df["idade"].isna().sum()

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []
if "etapa" not in st.session_state:
    st.session_state.etapa = 0
if "df_filtro" not in st.session_state:
    st.session_state.df_filtro = df.copy()
if "resumo" not in st.session_state:
    st.session_state.resumo = []
if "idioma_escolhido" not in st.session_state:
    st.session_state.idioma_escolhido = None

#st.title("Triagem Inteligente de Candidatos")
st.markdown("""
<div style='background-color:#542DC2; padding:20px; border-radius:8px; box-shadow: 0px 4px 12px rgba(0,0,0,0.1);'>
    <h2 style='color:white; text-align:center; font-size:28px; margin:0;'>Decision Match Hub</h2>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #00AEEF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
}
div.stButton > button:first-child:hover {
    background-color: #028bb8;
}
</style>
""", unsafe_allow_html=True)

etapa = st.session_state.etapa
df_filtro = st.session_state.df_filtro.copy()

#st.markdown("#### 🤖 Assistente de Triagem")
#st.markdown(
#    """
#    <div style='color: #666; font-size: 0.9rem; margin-bottom: 1rem'>
#    Estou aqui para te ajudar a encontrar os melhores candidatos. <br>
#    Responda abaixo e siga a conversa 👇
#    </div>
#    """,
#    unsafe_allow_html=True,
#)

# ------------------- MENSAGENS ------------------- #
with st.expander("🗣️ Ver histórico da conversa com a IA", expanded=True):  
    chat_css = """
    <style>
    .chat-container {
        width: 100%;
        display: flex;
        flex-direction: column;
    }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 15px;
        margin: 8px 0;
        max-width: 70%;
        clear: both;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    .user {
        background-color: #4626C0;
        color: white;
        float: right;
        text-align: right;
        border-bottom-right-radius: 0;
    }
    .assistant {
        background-color: #E6E4F7;
        color: #222;
        align-self: flex-start;
        text-align: left;
        border-bottom-left-radius: 0;
    }
    .label {
        font-size: 0.75rem;
        font-weight: bold;
        margin-bottom: 2px;
        color: #888;
    }
    </style>
    """
    st.markdown(chat_css, unsafe_allow_html=True)
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    for m in st.session_state.mensagens:
        usuario = m.get("usuario", "assistant")
        texto = m.get("texto", "")

        if usuario == "user":
            nome = "Você"
            alinhamento = "flex-end"
            classe = "chat-bubble user"
        else:
            nome = "🤖 Assistente Decision"
            alinhamento = "flex-start"
            classe = "chat-bubble assistant"

        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; align-items: {alinhamento};">
                <div class='label'>{nome}</div>
                <div class='{classe}'>{texto}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)  # fecha chat container

# ------------------- ETAPA 21: SLIDER DE IDADE ------------------- #
    if st.session_state.etapa == 21:
        if "faixa_etaria_mensagem_enviada" not in st.session_state:
            st.session_state.mensagens.append({
                "usuario": "assistant",
                "texto": "Agora me diga, qual faixa etária você gostaria de considerar?"
            })
            st.session_state.faixa_etaria_mensagem_enviada = True
            st.rerun()
    
        idade_validas = pd.to_numeric(st.session_state.df_filtro["idade"], errors="coerce").dropna()

        if not idade_validas.empty:
            idade_min, idade_max = int(idade_validas.min()), int(idade_validas.max())
            idade_range = st.slider(
                "Selecione a faixa de idade dos candidatos que deseja considerar:",
                min_value=idade_min,
                max_value=idade_max,
                value=(idade_min, idade_max),
                key="faixa_idade"
            )
            if st.button("Aplicar faixa etária"):
                df_filtro = st.session_state.df_filtro
                df_filtro = df_filtro[df_filtro["idade"].between(*idade_range)]
                st.session_state.df_filtro = df_filtro
                st.session_state.resumo.append(f"🔹 Idade entre {idade_range[0]} e {idade_range[1]} anos")
                avancar("Quer focar em alguma região específica do Brasil?", f"{idade_range[0]}-{idade_range[1]}", 3)


# ------------------- ETAPA 31: CAMPOS DE ESTADO E CIDADE ------------------- #
    elif etapa == 31:
        if "mensagem_regiao_enviada" not in st.session_state:
            st.session_state.mensagens.append({
                "usuario": "assistant",
                "texto": "🌎 Selecione o estado e as cidades que deseja considerar:"
            })
            st.session_state.mensagem_regiao_enviada = True
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            estado = st.selectbox(
                "Estado",
                ["Todos"] + sorted(df_filtro["estado"].dropna().unique()),
                key="estado_etapa3"
            )
        with col2:
            if estado == "Todos":
                cidades_sel = []
                st.selectbox("Cidade", ["Escolha um estado primeiro"], disabled=True, key="cidade_bloqueado")
            else:
                cidades = sorted(df_filtro[df_filtro["estado"] == estado]["cidade"].dropna().unique())
                cidades_sel = st.multiselect("Cidade", cidades, key="cidade_ativa")

        if st.button("Aplicar filtro de localização"):
            if estado == "Todos":
                texto_usuario = "Quero considerar candidatos de todas as regiões do Brasil."
            else:
                if cidades_sel:
                    if len(cidades_sel) == 1:
                        texto_usuario = f"Quero focar em {estado}, na cidade de {cidades_sel[0]}."
                    elif len(cidades_sel) == 2:
                        texto_usuario = f"Quero focar em {estado}, nas cidades de {cidades_sel[0]} e {cidades_sel[1]}."
                    else:
                        texto_usuario = f"Vou considerar o estado de {estado} e as seguintes cidades: {', '.join(cidades_sel[:-1])} e {cidades_sel[-1]}."
                else:
                    texto_usuario = f"Quero considerar apenas o estado de {estado}."

            st.session_state.mensagens.append({"usuario": "user", "texto": texto_usuario})

            if estado != "Todos":
                df_filtro = df_filtro[df_filtro["estado"] == estado]
                st.session_state.resumo.append(f"🔹 Estado: {estado}")
                if cidades_sel:
                    df_filtro = df_filtro[df_filtro["cidade"].isin(cidades_sel)]
                    st.session_state.resumo.append(f"🔹 Cidades: {', '.join(cidades_sel)}")
            else:
                st.session_state.resumo.append("🔹 Sem filtro de localização")

            st.session_state.df_filtro = df_filtro
            st.session_state.pop("mensagem_regiao_enviada", None)
            avancar("Qual o nível de experiência desejado para a vaga?", "", 4)

# ------------------- ETAPA 4: NÍVEL PROFISSIONAL ------------------- #
    elif  st.session_state.etapa == 4:
        niveis = sorted([
            n for n in st.session_state.df_filtro["nivel_profissional"].dropna().unique()
            if n.strip() != "Nenhum"
        ])

        nivel_sel = st.selectbox(
            "👤 Selecione o nível profissional desejado:",
            ["Todos"] + niveis,
            key="nivel_profissional"
        )

        if st.button("Aplicar nível profissional"):
            if nivel_sel != "Todos":
                df_filtro = st.session_state.df_filtro[
                    st.session_state.df_filtro["nivel_profissional"] == nivel_sel
                ]
                st.session_state.resumo.append(f"🔹 Nível profissional: {nivel_sel}")
                texto_usuario = f"Quero candidatos com perfil de nível {nivel_sel.lower()}."
            else:
                st.session_state.resumo.append("🔹 Nível profissional: Todos")
                texto_usuario = "Quero considerar todos os níveis de cargo disponíveis."

            st.session_state.mensagens.append({"usuario": "user", "texto": texto_usuario})
            st.session_state.df_filtro = df_filtro
            avancar("Você quer considerar o conhecimento em idiomas para essa vaga?", "", 5)

# ------------------- ETAPA 51: ESCOLHA DE IDIOMA ------------------- #
    elif etapa == 51:
        col1, col2 = st.columns(2)

        with col1:
            idioma_sel = st.selectbox(
                "Idioma",
                ["Inglês", "Espanhol"],
                index =0
            )

        with col2:
            if idioma_sel == "Todos":
                niveis_sel = []
                st.multiselect("Nível", ["Selecione um idioma primeiro"], disabled=True, key="nivel_bloqueado")
            else:
                col_idioma = "nivel_ingles" if idioma_sel == "Inglês" else "nivel_espanhol"
                niveis_disponiveis = sorted([
                    n for n in st.session_state.df_filtro[col_idioma].dropna().unique() if n.strip() != "Nenhum"
                ])
                niveis_sel = st.multiselect(
                    "Nível",
                    options=niveis_disponiveis,
                    default=niveis_disponiveis,
                    key="niveis_idioma"
                )

        if st.button("Aplicar idioma"):
            if idioma_sel == "Todos" or not niveis_sel:
                st.session_state.resumo.append("🔹 Nenhum idioma filtrado")
                resposta = "Não vamos considerar o conhecimento em idiomas como critério para essa vaga."
                st.session_state.mensagens.append({"usuario": "user", "texto": resposta})
                avancar("", "", 99)
            else:
                col_idioma = "nivel_ingles" if idioma_sel == "Inglês" else "nivel_espanhol"

                # Gera frase humanizada conforme quantidade de níveis
                if len(niveis_sel) == len(niveis_disponiveis):
                    frase = f"Quero considerar o idioma {idioma_sel.lower()} sem restrição de nível."
                elif len(niveis_sel) == 1:
                    frase = f"Gostaria de candidatos com nível {niveis_sel[0].lower()} em {idioma_sel.lower()}."
                elif len(niveis_sel) == 2:
                    frase = f"Quero considerar {idioma_sel.lower()} com os níveis {niveis_sel[0].lower()} e {niveis_sel[1].lower()}."
                else:
                    lista_formatada = ", ".join(n.lower() for n in niveis_sel[:-1]) + f" e {niveis_sel[-1].lower()}"
                    frase = f"Vamos considerar o idioma {idioma_sel.lower()} com os níveis {lista_formatada}."

                st.session_state.mensagens.append({"usuario": "user", "texto": frase})
                st.session_state.resumo.append(f"🔹 {idioma_sel}: {', '.join(niveis_sel)}")

                df_filtro = st.session_state.df_filtro[st.session_state.df_filtro[col_idioma].isin(niveis_sel)]
                st.session_state.df_filtro = df_filtro
                avancar("", "", 99)

# ------------------- Entrada DO USUÁRIO ------------------- #
# Etapa 0: mensagem de boas-vindas + botão iniciar
if etapa == 0:
    if not st.session_state.mensagens:
        st.session_state.mensagens.append({
            "usuario": "assistant",
            "texto": (
                "Olá! Eu sou o assistente de triagem de vagas da Decision. "
                "Estou aqui para te ajudar a encontrar os candidatos mais alinhados com a sua vaga.\n\n"
                "👉 É só responder **Sim** ou **Não** para cada uma, combinado?"
            )
        })
        st.rerun()  # <- força o Streamlit a redesenhar a interface

    if st.button("Ok, podemos começar!"):
        st.session_state.df_filtro = df.copy()
        avancar(
            "Para começarmos a filtrar os melhores perfis, você gostaria de considerar apenas candidatos com deficiência (PCD)?",
            resposta="Ok, podemos começar!",
            proxima_etapa=1
        )

# ------------------- ETAPA 1: PCD ------------------- #
if etapa >= 1:
    mensagem_usuario = st.chat_input("Digite sua resposta") 
    if mensagem_usuario:
        resposta = mensagem_usuario.strip()

        if etapa == 1:
            if resposta.lower() not in ["sim", "não", "nao"]:
                st.session_state.mensagens.append({"usuario": "user", "texto": resposta})
                st.session_state.mensagens.append({
                    "usuario": "assistant",
                    "texto": "Ops! Não entendi sua resposta. Me diga apenas Sim ou Não, combinado? Assim consigo aplicar o filtro direitinho."
                })  
                st.session_state.mensagens.append({
                    "usuario": "assistant",
                    "texto": "Você quer considerar apenas candidatos com deficiência (PCD)?"
                })
            
            elif resposta.lower() in ["sim"]:
                base = df.copy()  # <- base original, não filtrada
                base = base[base["pcd"] == 1]
                st.session_state.df_filtro = base
                st.session_state.resumo.append("🔹 Apenas PCD")
                avancar("Deseja aplicar uma faixa etária?", resposta, 2)
            else:
                st.session_state.resumo.append("🔹 Todos os candidatos")
                st.session_state.df_filtro = df_filtro
                avancar("Deseja aplicar uma faixa etária?", resposta, 2)

# ------------------- ETAPA 2: FAIXA ETÁRIA ------------------- #
        elif etapa == 2:
            if resposta.lower() not in ["sim", "não", "nao"]:
                st.session_state.mensagens.append({"usuario": "user", "texto": resposta})
                st.session_state.mensagens.append({
                    "usuario": "assistant",
                    "texto": "Ops! Não entendi sua resposta. Me diga apenas Sim ou Não, combinado? Assim consigo aplicar o filtro direitinho."
                })  
                st.session_state.mensagens.append({
                    "usuario": "assistant",
                    "texto": "Deseja aplicar uma faixa etária?"
                })
                st.rerun()

            elif resposta.lower() in ["sim"]:
                st.session_state.mensagens.append({"usuario": "user", "texto": resposta})
                st.session_state.mensagens.append({
                    "usuario": "assistant",
                    "texto": f"⚠️ Atenção: {total_sem_idade} candidato(s) da base não informaram a data de nascimento. Por isso, ao aplicar o filtro por faixa etária, esses perfis não poderão ser considerados."
                })
                st.session_state.etapa = 21   
                st.rerun()         
            
            else:
                st.session_state.resumo.append("🔹 Não aplicou faixa etária")
                avancar("Quer focar em alguma região específica do Brasil?", resposta, 3)



# ------------------- ETAPA 3: PERGUNTA DE REGIÃO ------------------- #
        elif etapa == 3:
            if resposta.lower() not in ["sim", "não", "nao"]:
                st.session_state.mensagens.append({
                    "usuario": "assistant",
                    "texto": "Ops! Não entendi sua resposta. Me diga apenas Sim ou Não, combinado? Assim consigo aplicar o filtro direitinho."
                })
                st.session_state.mensagens.append({
                    "usuario": "assistant",
                    "texto": "Quer focar em alguma região específica do Brasil?"
                })
                st.rerun()

            elif resposta.lower() in ["sim"]:
                st.session_state.mensagens.append({"usuario": "user", "texto": resposta})    
                st.session_state.etapa = 31
                st.rerun()

            else: 
                st.session_state.resumo.append("🔹 Sem filtro de localização")
                resposta = "Quero considerar candidatos de todas as regiões do Brasil."
                avancar("Qual o nível de experiência desejado para a vaga?", resposta, 4)

# ------------------- ETAPA 5: IDIOMA ------------------- #
        elif etapa == 5:
            if resposta.lower() not in ["sim", "não", "nao"]:
                st.session_state.mensagens.append({"usuario": "assistant", "texto": "Ops! Não entendi sua resposta. Me diga apenas Sim ou Não, combinado? Assim consigo aplicar o filtro direitinho."})
                st.session_state.mensagens.append({"usuario": "assistant", "texto": "Você quer considerar o conhecimento em idiomas para essa vaga?"})
                st.rerun()
            
            elif resposta.lower() == "sim":
                st.session_state.mensagens.append({"usuario": "user", "texto": resposta})
                avancar("🌐 Qual idioma deseja considerar?", "", 51)
            
            else:
                
                st.session_state.resumo.append("🔹 Nenhum idioma filtrado")
                resposta = "Prefiro não considerar o domínio de idiomas como critério para essa vaga."
                st.session_state.mensagens.append({"usuario": "user", "texto": resposta})
                avancar("", "", 99)


# ------------------- ETAPA 6: NÍVEL DO IDIOMA ------------------- #
elif etapa == 6:
    idioma = st.session_state.idioma_escolhido
    coluna = "nivel_ingles" if idioma == "Inglês" else "nivel_espanhol"
    niveis = sorted([n for n in df_filtro[coluna].dropna().unique() if n.strip() != ""])
    nivel_idioma = st.selectbox(f"📘 Qual o nível de {idioma.lower()} desejado:", ["Todos"] + niveis)
    if st.button("Aplicar nível de idioma"):
        if nivel_idioma != "Todos":
            df_filtro = df_filtro[df_filtro[coluna] == nivel_idioma]
            st.session_state.resumo.append(f"🔹 {idioma}: {nivel_idioma}")
        st.session_state.df_filtro = df_filtro
        avancar("", nivel_idioma, 99)


# ------------------- RESULTADO FINAL ------------------- #
if st.session_state.etapa == 99:
    total_base = len(df)  # df original, não filtrado
    total = len(st.session_state.df_filtro)
    if total_base > total:
        st.markdown(f"<div style='font-size: 12px; color: #888;'>De <b>{total_base}</b> candidatos na base, restaram <b>{total}</b> após os filtros.</div></b><br></div>", unsafe_allow_html=True)

    st.markdown("""
<details>
<summary style='font-size: 16px; '>🤖 <b>Assistente Decision:</b> Agora que aplicamos os filtros, posso te ajudar a <b>ranquear</b> os <b>candidatos</b> com base na <b>vaga</b> desejada.</summary>
<div style='margin-top: 10px; font-size: 15px;'>

Para isso, me diga qual é a vaga que você quer usar como referência. Você pode:

- Selecionar uma vaga da base da <b>Decision</b>, ou
- Colar manualmente a descrição da vaga.

Assim consigo comparar os perfis e destacar os mais aderentes no topo da lista.            
</div>
</details>
""", unsafe_allow_html=True)        
    st.markdown(" ")
    mostrar_resultado()

# ------------------- SIDEBAR: PERFIL E TOTAL ------------------- #
with st.sidebar:
    st.markdown("### 📋 Perfil buscado")

    if st.session_state.resumo:
        for r in st.session_state.resumo:
            st.markdown(f"- {r}")
    else:
        st.markdown("_Nenhum filtro aplicado ainda_")

    st.markdown("---")
    total = len(st.session_state.df_filtro)
    st.markdown(f"<div style='font-size: 18px;'>👥 <b>Total de candidatos:</b> <span style='color:#00AEEF; font-size: 20px'>{total}</span></div>", unsafe_allow_html=True)

st.markdown("""
<hr style='margin-top:40px'>
<div style='text-align:center; font-size:14px; color:#666'>
    <b>Decision</b> • Soluções em RPO e Hunting com mais de 20 anos de experiência. <br>
    Recrutamento completo, estratégico e com foco em performance desde o primeiro dia.
</div>
""", unsafe_allow_html=True)
