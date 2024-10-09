import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components
import requests
import openai
from PIL import Image
import base64
from io import BytesIO
import io

# Configurar a chave da API da OpenAI
st.set_page_config(page_title="Análise de Imagens", layout='wide')

# coloque a chave aqui
# openai.api_key = ''
# api_key = ''

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

def openai_translate(text):
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
                    "text": """Você recebeu relatórios de análise de imagens extraídas do Instagram. Com base nas análises fornecidas, 
                               você deve traduzir o texto para o inglês."""
                }
            ]
        }
    ]
    
    # Adiciona as imagens e informações ao payload
    messages[0]['content'].append({
        "type": "text",
        "text": text
    })

    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 3000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    # Obtendo o texto da resposta diretamente
    if response.status_code == 200:
        json_response = response.json()
        analysis_result = json_response['choices'][0]['message']['content']
        return analysis_result  # Retorna o texto traduzido diretamente
    else:
        return f"Erro na tradução: {response.status_code} - {response.text}"
    


def generate_image_from_description(analise, hashtag):
    dalle_headers = {
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"Crie uma imagem relacionada à hashtag {hashtag} com base na análise das postagens do Instagram. {analise}"

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


def chamada_api(palavra, select):
    url = "https://instagram-scraper-api3.p.rapidapi.com/hashtag_media"

    querystring = {"hashtag":palavra,"feed_type":select}

    headers = {
	    "x-rapidapi-key": "feeda19c62msha9a23d340f8e0a5p17d4a4jsn27b26cb032be",
        "x-rapidapi-host": "instagram-scraper-api3.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data=response.json()
    return data


# DataFrame para armazenar os dados
df = {
    # 'index': [],
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
    prompt = st.chat_input(placeholder='Inserir a palavra', max_chars=250, key='input')
    st.info("Utilize a palavra sem a #")

    select = st.selectbox('Tipo de busca', ['Relevância', 'Recentes'], key='select', index=0)

# Iniciando a estrutura do HTML para o carrossel
carousel_html = '''
    <div id="content">
        <div id="carrossel">
            <ul>
'''

images_descriptions = ''

messages_list = []

if prompt:   
    if select == 'Relevância':
        select = 'top'
    else:
        select  = 'recent'

    data = chamada_api(prompt, select) 
    # if prompt == 'Corona':
    #     with open('app/ambev_top.json', 'r') as arquivo:
    #         data = json.load(arquivo)
    
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
                # df['index'].append(len(df['index'])+1)
                df['url'].append(url)
                df['comment_count'].append(comment_count)
                df['like_count'].append(like_count)
                df['username'].append(username)
                df['description'].append(description)
    except:
        st.error("Erro ao salvar os dados")

    images_data_list = []

    df = pd.DataFrame(df)  # Certifique-se de que 'df' seja um dicionário válido
    
    st.header('Análises Rápidas')

    html_code = f"""
    <head>
    <link href="https://fonts.googleapis.com/css?family=Open+Sans:300i,400" rel="stylesheet">
    <style>
        body {{
        background-color: #100e17;
        font-family: 'Open Sans', sans-serif;
        }}

        .container {{
        margin: 0 auto;
        height: 350px;
        max-width: 1300px;
        top: 50px;
        left: calc(50% - 400px);
        display: flex;
        }}

        .card {{
        display: flex;
        height: 250px;
        width: 570px;
        background-color: #0A3D62;
        border-radius: 10px;
        box-shadow: -1rem 0 3rem #000;
        transition: 0.4s ease-out;
        position: relative;
        left: 0px;
        top:12%;
        }}

        .card:not(:first-child) {{
            margin-left: -50px;
        }}

        .card:hover {{
        transform: translateY(-20px);
        transition: 0.4s ease-out;
        }}

        .card:hover ~ .card {{
        position: relative;
        left: 50px;
        transition: 0.4s ease-out;
        }}

        .title {{
        color: white;
        font-weight: 300;
        position: absolute;
        left: 20px;
        top: 15px;
        }}

        .bar {{
        position: absolute;
        top: 90px;
        left: 17%;
        height: 5px;
        width: 290px;
        }}

        .emptybar {{
        background-color: #2e3033;
        width: 100%;
        height: 100%;
        }}

        .filledbar_quantidade_posts, .filledbar_media_likes, .filledbar_media_comments {{
        position: absolute;
        top: 0px;
        z-index: 3;
        width: 0px;
        height: 100%;
        background: rgb(0,154,217);
        background: linear-gradient(90deg, rgba(0,154,217,1) 0%, rgba(217,147,0,1) 65%, rgba(255,186,0,1) 100%);
        transition: 0.6s ease-out;
        }}

        .card:hover .filledbar_quantidade_posts {{
        width: 100%;
        transition: 0.4s ease-out;
        }}

        .card:hover .filledbar_media_likes {{
        width: { (df['like_count'].mean() / df['like_count'].max()) * 100}%;
        transition: 0.4s ease-out;
        }}

        .card:hover .filledbar_media_comments {{
        width: {(df['comment_count'].mean() / df['comment_count'].max()) * 100}%;
        transition: 0.4s ease-out;
        }}

        .circle_saude {{
        position: absolute;
        top: 115px;
        left: 44%;
        }}

        .circle {{
        position: absolute;
        top: 115px;
        left: 40%;
        }}

        .circle2 {{
        position: absolute;
        top: 115px;
        width: 150px;
        left: 32%;
        text-align: center;
        }}

        .stroke {{
        stroke: white;
        stroke-dasharray: 360;
        stroke-dashoffset: 360;
        transition: 0.6s ease-out;
        }}

        svg {{
        fill: #17141d;
        stroke-width: 2px;
        }}

        .card:hover .stroke {{
        stroke-dashoffset: 100;
        transition: 0.6s ease-out;
        }}

        /* Centraliza o texto dentro do círculo */
        .circle text, .circle2 text, .circle_saude text {{
        fill: white;
        font-size: 29px;
        text-anchor: middle;
        font-weight:Bold;
        dominant-baseline: central;
        }}

        .descript{{
        text-align: center;
        position: absolute;
        top: 170px;
        width:300px;
        left: 16%;
        color: white;
        }}

        .descript_rever{{
        text-align: center;
        position: absolute;
        top: 165px;
        width:210px;
        left: 27%;
        color: white;
        }}

    </style>
    </head>
    <body class="body">
    <div class="container">
    <div class="card">
        <h3 class="title">Quantidade de posts</h3>
        <div class="bar">
        <div class="emptybar"></div>
        <div class="filledbar_quantidade_posts"></div>
        </div>
        <div class="circle_saude">
        <text x="60" y="60" style="color:white;">{len(df.index)}</text>
        </div>
        <text class="descript">Posts encontrados</text>
    </div>
    <div class="card">
        <h3 class="title">Média de likes</h3>
        <div class="bar">
        <div class="emptybar"></div>
        <div class="filledbar_media_likes"></div>
        </div>
        <div class="circle">
            <text x="60" y="60" style="color:white;">{round(df['like_count'].mean(), 2)}</text>
        </div>
        <text class="descript_rever">Média de likes</text>
    </div>
    <div class="card">
        <h3 class="title">Média de comentários</h3>
        <div class="bar">
        <div class="emptybar"></div>
        <div class="filledbar_media_comments"></div>
        </div>
        <div class="circle2">
        <text x="60" y="60" style="color:white;">{round(df['comment_count'].mean(), 2)}</text>
        </div>
        <text class="descript">Média de comentários</text>
    </div>
    </div>
    </body>
    """

    st.markdown(html_code, unsafe_allow_html=True)

    st.header('Galeria de imagens')

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
                'description': description or "Sem descrição",  # Adiciona uma descrição padrão se estiver vazia
                'username': username,
                # 'index': index
            })
           
        except Exception as e:
            st.write(f"Erro ao carregar a imagem: {e}")

    carousel_html += '''
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
    '''
    for img_data in images_data_list:
        carousel_html += f'''
            <li>
                <img src="data:image/jpeg;base64,{img_data['base64']}" alt="Imagem" style="width: 300px; height: 300px;border-radius: 10px 10px 0px 0px; object-fit: cover;">
                <p style="font-family:'Open Sans', sans-serif;color:white;text-align:center;line-height:25px;">@{img_data['username']} <br>Likes: {img_data['like_count']} | Comentários: {img_data['comment_count']}</p>
            </li>
        '''

    carousel_html += '''
                </ul>
                    </div>
                    <nav id="menu-carrossel">
                        <a href="#" class="prev" title="Anterior">◀️</a>
                        <a href="#" class="next" title="Próximo">▶️</a>
                    </nav>
                    </div>

                <style>
                #carrossel {
                    width: 100%;
                    overflow: hidden;
                    position: relative;
                }
                #carrossel ul {
                    display: flex;
                    transition: transform 0.5s ease;
                    padding: 0;
                    list-style: none;
                }
                #carrossel li {
                    background-color: black;
                    border: 1px solid white;
                    border-radius: 10px;
                    min-width: 300px;
                    margin-right: 10px;
                }
                #menu-carrossel {
                    display: flex;
                    justify-content: space-between;
                    width: 7%;
                    margin: 0 auto;
                    pointer-events: none;
                }
                #menu-carrossel a {
                    text-decoration: none;
                    padding: 5px 10px;
                    background-color: rgba(0, 0, 0, 0.5);
                    color: white;
                    border-radius: 5px;
                    pointer-events: all;
                    z-index: 10;
                }
                </style>

                <script>
                document.addEventListener('DOMContentLoaded', function () {
                    const prev = document.querySelector('.prev');
                    const next = document.querySelector('.next');
                    const carrossel = document.querySelector('#carrossel ul');
                    const maxScroll = carrossel.scrollWidth - carrossel.clientWidth; // Tamanho máximo de rolagem
                    let scrollAmount = 0;

                    next.addEventListener('click', function (e) {
                        e.preventDefault();
                        if (scrollAmount < maxScroll) {
                            scrollAmount += 200;
                            carrossel.style.transform = `translateX(-${scrollAmount}px)`;
                        }
                    });

                    prev.addEventListener('click', function (e) {
                        e.preventDefault();
                        if (scrollAmount > 0) {
                            scrollAmount -= 200;
                            carrossel.style.transform = `translateX(-${scrollAmount}px)`;
                        }
                    });
                });
                </script>
                '''

                # Renderizando o carrossel no Streamlit
    st.components.v1.html(carousel_html, height=500)

    st.header("Análise Completa")
    
   
    # Envia todas as imagens com seus contextos para a função de leitura
    if images_data_list:
        analise = openai_image_read(images_data_list)
        st.markdown(analise)

    st.header("Geração de Imagem")

    if analise:
        analise_ingles = openai_translate(analise)

        #     # Defina sua chave de API aqui
        api_key_stability = "sk-t3bEh0oXOY0xMRNcl3fCJkiEPJaHcZ88psSP03CJtXCwwWs7"

            # Defina o prompt para a geração da imagem
        prompt = f"Based on the analysis of the Instagram posts, generate an image related to the word '{prompt}' and {analise_ingles}"

            # Faça a solicitação para a API
        response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/ultra",  # URL da API
                headers={
                    "Authorization": f"Bearer {api_key_stability}",
                    "Accept": "image/*"  # Formato da imagem
                },
                 files={
                    "none": '',  # Campo de arquivos vazio, pois não estamos enviando um arquivo
                },
                data={
                    "prompt": prompt,  # Texto que descreve a imagem
                    "width": 512,  # Largura da imagem gerada
                    "height": 512,  # Altura da imagem gerada
                    "num_inference_steps": 50,  # Passos de inferência para a geração da imagem
                    "guidance_scale": 7.0,  # Parâmetro de "guidance" (quanto a IA segue o prompt)
                    "output_format": "png"  # Formato da imagem gerada
                }
            )

            # Verifique o status da resposta
        if response.status_code == 200:
                image = BytesIO(response.content)
                st.image(image, caption="Imagem gerada com Stable Diffusion", use_column_width=True)
        else:
                st.error(f"Erro ao gerar a imagem: {response.status_code} - {response.text}")


        
