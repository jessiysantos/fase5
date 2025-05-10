import requests
import pandas as pd
import io
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def carregar_dados_drive(url, file_type='json'):
    try:
        # Realizar o download do arquivo
        response = requests.get(url)
        
        # Verificar se o download foi bem-sucedido
        if response.status_code == 200:
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

# Carregar os dados
dados_vagas = carregar_dados_drive(url_vagas, file_type='json')
dados_prospects = carregar_dados_drive(url_prospects, file_type='json')

# Se os dados forem carregados corretamente
if dados_vagas is not None and dados_prospects is not None:
    # Análise das vagas por estado
    estados_vagas = []
    for vaga in dados_vagas.values():
        estado = vaga["perfil_vaga"].get("estado", "")
        if estado:
            estados_vagas.append(estado)
    
    # Criar gráfico de distribuição das vagas por estado
    estado_df = pd.DataFrame(estados_vagas, columns=['Estado'])
    estado_count = estado_df['Estado'].value_counts()
    
    # Gráfico - Distribuição das vagas por estado
    plt.figure(figsize=(10, 6))
    sns.countplot(data=estado_df, x='Estado', order=estado_count.index)
    plt.title('Distribuição das Vagas por Estado')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(plt)

    # Análise de candidatos por situação de candidatura
    prospects_data = []
    for vaga_id, vaga_info in dados_prospects.items():
        for prospect in vaga_info['prospects']:
            prospects_data.append({
                'Nome': prospect['nome'],
                'Situacao': prospect['situacao_candidado'],
                'Data Candidatura': prospect['data_candidatura']
            })
    
    prospects_df = pd.DataFrame(prospects_data)
    
    # Gráfico - Quantidade de prospects por situação de candidatura
    plt.figure(figsize=(10, 6))
    sns.countplot(data=prospects_df, x='Situacao', order=prospects_df['Situacao'].value_counts().index)
    plt.title('Quantidade de Prospects por Situação de Candidatura')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(plt)

    # Análise do tipo de contratação das vagas
    tipos_contratacao = []
    for vaga in dados_vagas.values():
        tipo_contratacao = vaga["informacoes_basicas"].get("tipo_contratacao", "")
        if tipo_contratacao:
            tipos_contratacao.append(tipo_contratacao)
    
    # Criar gráfico de distribuição dos tipos de contratação
    tipo_df = pd.DataFrame(tipos_contratacao, columns=['Tipo Contratação'])
    tipo_count = tipo_df['Tipo Contratação'].value_counts()
    
    # Gráfico - Distribuição dos tipos de contratação das vagas
    plt.figure(figsize=(10, 6))
    sns.countplot(data=tipo_df, x='Tipo Contratação', order=tipo_count.index)
    plt.title('Distribuição dos Tipos de Contratação das Vagas')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(plt)

else:
    st.error("Não foi possível carregar os dados.")
