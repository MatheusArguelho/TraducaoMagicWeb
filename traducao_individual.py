import requests
from deep_translator import GoogleTranslator
import json
import os

# Nome do arquivo de cache para traduções
CACHE_FILE = "translation_cache.json"

# Função para carregar o cache de traduções a partir de um arquivo JSON
def load_translation_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)  # Retorna o conteúdo do arquivo como um dicionário
    return {}  # Retorna um dicionário vazio se o arquivo não existir

# Função para salvar o cache no arquivo JSON
def save_translation_cache(new_cache_entry):
    # Verificar se o arquivo JSON já existe
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            json_cache = json.load(file)  # Carregar o cache existente
    else:
        json_cache = {}

    # Atualizar o cache com a nova entrada
    json_cache.update(new_cache_entry)

    # Salvar o cache atualizado de volta ao arquivo
    with open(CACHE_FILE, 'w') as file:
        json.dump(json_cache, file)

# Inicializar o cache de traduções ao iniciar a aplicação Flask
translation_cache = {}  # Cache em memória para traduções
json_cache = load_translation_cache()  # Cache carregado do arquivo JSON

# Função para baixar JSON de uma URL
def download_json(url):
    response = requests.get(url)  # Realiza a requisição HTTP GET
    if response.status_code == 200:
        return response.json()  # Retorna o JSON se a requisição for bem-sucedida
    elif response.status_code == 404:  # Se recurso não for encontrado
        try:
            error_data = response.json()  # Tenta obter detalhes do erro
            error_t = error_data.get("details", "Detalhes não fornecidos")
            error_t = GoogleTranslator(source='auto', target='pt').translate(text=error_t)  # Traduza o texto do erro
            return {"error": error_t}  # Retorna mensagem de erro traduzida
        except ValueError:
            return {"error": "Erro 404: Recurso não encontrado e detalhes não estão disponíveis."}
    else:
        return {"error": f"Erro ao baixar o JSON. Status code: {response.status_code}"}  # Retorna mensagem de erro genérica

# Função para descapitalizar e substituir caracteres em uma string
def descapitalize_and_replace(text):
    return text.lower().replace(" ", "+").replace("'", "")  # Retorna texto em letras minúsculas e com espaços substituídos por '+'

# Função para traduzir texto usando o Google Translator
def translate_text(card_name, text, text_type):
    cache_key = f"{card_name}_{text_type}"  # Cria chave única para o cache

    # Verifica primeiro o cache em memória
    if cache_key in translation_cache:
        print("carta encontrada no cache")
        return translation_cache[cache_key]['translated_text']

    # Em seguida, verifica o cache em JSON
    if cache_key in json_cache:
        print("carta encontrada no JSON")
        return json_cache[cache_key]['translated_text']

    # Se não encontrado, traduz do zero
    print("carta não encontrada")
    translated = GoogleTranslator(source='auto', target='pt').translate(text=text)

    # Armazena a tradução no cache em memória
    translation_cache[cache_key] = {
        'original_text': text,
        'translated_text': translated
    }

    # Atualizar o cache JSON com a nova tradução e salvar
    save_translation_cache({cache_key: {
        'original_text': text,
        'translated_text': translated
    }})

    return translated

# Função para formatar texto para exibição em HTML
def format_text_for_html(text):
    return text.replace("\n", "<br>")  # Substitui novas linhas por quebras de linha em HTML

# Função para traduzir e formatar texto para HTML
def translate_and_format_text(card_name, text, text_type):
    translated_text = translate_text(card_name, text, text_type)  # Traduz o texto
    return format_text_for_html(translated_text)  # Retorna texto formatado para HTML

# Função para buscar dados de uma carta a partir da API Scryfall
def fetch_card_data(nome):
    url = f"https://api.scryfall.com/cards/named?fuzzy={nome}"  # URL da API com o nome da carta
    return download_json(url)  # Chama a função para baixar o JSON

# Função para extrair URLs das imagens da carta
def extract_image_urls(data):
    try:
        normal_image_url = data["image_uris"]["normal"]  # Tenta obter URL da imagem normal
        return normal_image_url, None  # Retorna a URL da imagem normal
    except KeyError:
        try:
            # Tenta obter URLs de cartas que têm faces diferentes
            normal_image_url = data['card_faces'][0]['image_uris']['normal']
            normal_image_url2 = data['card_faces'][1]['image_uris']['normal']
            return normal_image_url, normal_image_url2  # Retorna as URLs das duas faces
        except KeyError:
            return None, None  # Retorna None se não encontrar imagens

# Função para extrair o texto Oracle da carta
def extract_oracle_text(data):
    try:
        oracle_texto = data["oracle_text"]  # Tenta obter o texto Oracle
    except KeyError:
        try:
            # Tenta obter o texto Oracle das faces da carta
            oracle_texto = data['card_faces'][0]['oracle_text']
            oracle_texto += '\n' + '----' + '\n' + data['card_faces'][1]['oracle_text']
        except KeyError:
            oracle_texto = ''  # Retorna vazio se não encontrar texto
    return oracle_texto  # Retorna o texto Oracle

# Função para extrair o texto de sabor da carta
def extract_flavor_text(data):
    try:
        flavor_original = data["flavor_text"]  # Tenta obter o texto de sabor
    except KeyError:
        try:
            flavor_original = ''  # Inicializa como vazio
            if 'card_faces' in data:
                card_faces = data['card_faces']
                if isinstance(card_faces, list) and len(card_faces) > 0:
                    # Obtém texto de sabor das faces da carta
                    if 'flavor_text' in card_faces[0]:
                        flavor_original = card_faces[0]['flavor_text']
                    if len(card_faces) > 1 and 'flavor_text' in card_faces[1]:
                        flavor_original2 = card_faces[1]['flavor_text']
                        flavor_original += '\n' + '-' + '\n' + flavor_original2
        except KeyError:
            flavor_original = ''  # Retorna vazio se não encontrar texto de sabor
    return flavor_original  # Retorna o texto de sabor

# Função principal para processar dados de uma carta
def process_card(original_text):
    nome = descapitalize_and_replace(original_text)  # Formata o nome da carta
    data = fetch_card_data(nome)  # Busca dados da carta

    if data is None:
        return None  # Retorna None se não encontrar dados da carta

    # Extrai informações da carta
    normal_image_url, normal_image_url2 = extract_image_urls(data)
    oracle_texto = extract_oracle_text(data)
    flavor_original = extract_flavor_text(data)

    # Passa o nome da carta ao traduzir
    translated_oracle = translate_and_format_text(original_text, oracle_texto, 'oracle')
    translated_flavor = translate_and_format_text(original_text, flavor_original, 'flavor')

    return {
        'original_text': original_text,
        'normal_image_url': normal_image_url,
        'normal_image_url2': normal_image_url2,
        'oracle_texto': oracle_texto,
        'flavor_original': flavor_original,
        'translated': translated_oracle,
        'flavor_translated': translated_flavor
    }
