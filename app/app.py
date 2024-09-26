import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components
import requests
import openai
from PIL import Image
import base64
from io import BytesIO
# Configurar a chave da API da OpenAI
st.set_page_config(page_title="Análise de Imagens", layout='wide')

# CSS da página
st.markdown(
    f"""
        <style>

        </style>
        """,
    unsafe_allow_html=True,
)

# coloque a chave aqui


# Função para converter imagem em base64
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # Você pode ajustar o formato conforme a imagem
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_base64

def openai_image_read(images_data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Prepara o payload com todas as imagens
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Você recebeu um conjunto de imagens extraidas do Instagram. Com base nas imagens fornecidas e na descrição de cada uma, você deve analisar as postagens e responder as seguintes perguntas:
                             1 - Quais as caracteristicas das postagens com mais likes;
                             2 - Quais as caracteristicas das imagens com mais comentarios;
                             3 - Analisando todas as postagens, quais as Potenciais Oportunidades que podem ser exploradas pela marca;
                             4 - Por fim, Baseado nas imagens e nas descrições, gere uma ideia de postagem relacionada.
                             """
                }
            ]
        }
    ]
    
    # Adiciona as imagens e informações ao payload
    for img_data in images_data:
        messages[0]['content'].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_data['base64']}"
            }
        })
        messages[0]['content'].append({
            "type": "text",
            "text": f"Likes: {img_data['like_count']}, Comentários: {img_data['comment_count']}, Descrição: {img_data['description']}"
        })

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "max_tokens": 3000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    json_response = response.json()
    analysis_result = json_response['choices'][0]['message']['content']
    formatted_text = analysis_result.encode('utf-16', 'surrogatepass').decode('utf-16', 'ignore')
    
    return formatted_text



def generate_image_from_description(analise, hashtag):
    dalle_headers = {
        "Authorization": f"Bearer {api_key}"
    }
    # prompt = f"Gere uma imagem para postar nas redes sociais com base nessa análise: {analise}, e na hashtag: {hashtag}"
    prompt = """
        Ideia de Postagem: Visuais: Uma imagem divertida de um grupo de amigos reunidos em um churrasco, com canecos de cerveja gigantes e um ambiente descontraído.

        Texto: "Quem disse que a única decisão difícil é escolher a cerveja? 🍻 Entre amigos, cada riso é uma rodada a mais! 😂 Qual a sua melhor memória com a galera? Compartilhe e vamos relembrar as melhores histórias! #BebendoComResponsabilidade #ZéDelivery #Amigos"

        Esta ideia utiliza humor, interatividade e um convite à reminiscência que deve ressoar positivamente com o público, aumentando o engajamento.
    """
    if len(prompt) > 1000:
        prompt = prompt[:997] + "..."  # Limita o prompt a 1000 caracteres

    dalle_payload = {
        "prompt": prompt,
        "size": "512x512"
    }
    
    try:
        # Faz a requisição para a API DALL-E
        dalle_response = requests.post("https://api.openai.com/v1/images/generations", headers=dalle_headers, json=dalle_payload)
        dalle_json = dalle_response.json()
        
        # Verifica se a chave 'data' está presente
        if 'data' in dalle_json and dalle_json['data']:
            image_url = dalle_json['data'][0]['url']
            return image_url
        else:
            # Exibe o erro e a resposta para depuração
            st.error("Erro ao gerar imagem: Resposta inesperada da API.")
            st.write(dalle_json)
            return None
    except Exception as e:
        # Captura e exibe qualquer exceção ocorrida durante a requisição
        st.error(f"Erro ao se comunicar com a API DALL-E: {e}")
        return None

# DataFrame para armazenar os dados
df = {
    'index': [],
    'url': [],
    'comment_count': [],
    'like_count': [],
    'username': [],
    'description': []
}

# Lista para armazenar as URLs das imagens
urls = []

# Sidebar com o título e a caixa de texto para a hashtag
with st.sidebar:
    st.header('Análise de imagem')
    
    st.write('Buscar por hashtag:')
    prompt = st.chat_input(placeholder='Inserir a hashtag', max_chars=250, key='input')
   


images_descriptions = ''

messages_list = []


if prompt:
    st.header('Galeria de imagens')
    
    if prompt == 'Ambev':
        with open('ambev_top.json', 'r') as arquivo:
            data = json.load(arquivo)
    elif prompt == 'Budweiser':
        with open('budweiser.json', 'r') as arquivo:
            data = json.load(arquivo)

    # Loop para percorrer os posts
    try:
        for media in data["data"]["medias"]:
            # Verifica se 'video_duration' não está presente ou é None
            if media.get("video_duration") is None:
                url = media.get("image_versions2", {}).get(
                    "candidates", [{}])[0].get("url")
                comment_count = media.get("comment_count")
                like_count = media.get("like_count")
                username = media.get("user", {}).get("username")
                description = media.get("caption", {}).get("text")

                # Adiciona a URL à lista
                if url:
                    urls.append(url)

                # Adiciona os dados ao DataFrame
                df['index'].append(len(df['index'])+1)
                df['url'].append(url)
                df['comment_count'].append(comment_count)
                df['like_count'].append(like_count)
                df['username'].append(username)
                df['description'].append(description)
    except:
        st.error("Erro ao salvar os dados")

    # st.dataframe(df)

    images_data_list = []

    df = pd.DataFrame(df)  # Certifique-se de que 'df' seja um dicionário válido
    
    num_columns = 3
    columns = st.columns(num_columns)
    for index, row in df.iterrows():
        url = row['url']
        like_count = row['like_count']
        comment_count = row['comment_count']
        description = row['description']
        username = row['username']
        
        # Fazer o download da imagem
        try:
            image = Image.open(requests.get(url, stream=True).raw)

            images_data_list.append({
                'base64': image_to_base64(image),  # Converte a imagem para base64
                'like_count': like_count,
                'comment_count': comment_count,
                'description': description or "Sem descrição"  # Adiciona uma descrição padrão se estiver vazia
            })

            # Definir qual coluna usar
            col = columns[index % num_columns]
            
            # Exibir a imagem na coluna correspondente
            with col:
                st.image(image, use_column_width=True)
                st.html(f"<p style='text-align:center'>@{username} <br>Likes: {like_count} | Comentários: {comment_count}</p>")
                # st.markdown(f"**@{username}**<br>Likes: {like_count} | Comentários: {comment_count}", unsafe_allow_html=True)

            
        except Exception as e:
            st.write(f"Erro ao carregar a imagem: {e}")
    
    st.header("Resultado da análise")

    # Envia todas as imagens com seus contextos para a função de leitura
    if images_data_list:
       
        analise = openai_image_read(images_data_list)
        st.markdown(analise)

        # generated_image_url = generate_image_from_description(analise, prompt)
        # if generated_image_url:
            # st.image(generated_image_url, caption="Imagem gerada com base na análise", use_column_width=True)