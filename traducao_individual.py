import requests
from deep_translator import GoogleTranslator
#from dicionario import translation_dict

def download_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        error_data = response.json()
        error_t = error_data["details"]
        error_t = GoogleTranslator(source='auto', target='pt').translate(text=error_t)
        return {"error": error_t}
    else:
        return {"error": f"Erro ao baixar o JSON. Status code: {response.status_code}"}

def descapitalize_and_replace(text):
    return text.lower().replace(" ", "+").replace("'", "")

def translate_text(text):
    return GoogleTranslator(source='auto', target='pt').translate(text=text)

def replace_newline_with_br(text):
    return text.replace("\n", "<br>")

def fetch_card_data(nome):
    url = f"https://api.scryfall.com/cards/named?fuzzy={nome}"
    return download_json(url)

def extract_image_urls(data):
    try:
        normal_image_url = data["image_uris"]["normal"]
        return normal_image_url, None
    except KeyError:
        try:
            normal_image_url = data['card_faces'][0]['image_uris']['normal']
            normal_image_url2 = data['card_faces'][1]['image_uris']['normal']
            return normal_image_url, normal_image_url2
        except KeyError:
            return None, None

def extract_oracle_text(data):
    try:
        oracle_texto = data["oracle_text"]
    except KeyError:
        try:
            oracle_texto = data['card_faces'][0]['oracle_text']
            oracle_texto = oracle_texto + '\n' + '----' + '\n' + data['card_faces'][1]['oracle_text']
        except KeyError:
            oracle_texto = ''
    return oracle_texto

def extract_flavor_text(data):
    try:
        flavor_original = data["flavor_text"]
    except KeyError:
        try:
            flavor_original = ''
            if 'card_faces' in data:
                card_faces = data['card_faces']
                if isinstance(card_faces, list) and len(card_faces) > 0:
                    if 'flavor_text' in card_faces[0]:
                        flavor_original = card_faces[0]['flavor_text']
                    if len(card_faces) > 1 and 'flavor_text' in card_faces[1]:
                        flavor_original2 = card_faces[1]['flavor_text']
                        flavor_original += '\n' + '-' + '\n' + flavor_original2
        except KeyError:
            flavor_original = ''
    return flavor_original

def translate_and_format_text(text):
    #for term, translation in translation_dict.items():
    #    text = text.replace(term, translation)
    text = translate_text(text)
    return replace_newline_with_br(text)

def process_card(original_text):
    nome = descapitalize_and_replace(original_text)
    data = fetch_card_data(nome)

    if data is None:
        return None

    normal_image_url, normal_image_url2 = extract_image_urls(data)
    oracle_texto = extract_oracle_text(data)
    flavor_original = extract_flavor_text(data)

    translated_oracle = translate_and_format_text(oracle_texto)
    translated_flavor = translate_and_format_text(flavor_original)

    return {
        'original_text': original_text,
        'normal_image_url': normal_image_url,
        'normal_image_url2': normal_image_url2,
        'oracle_texto': oracle_texto,
        'flavor_original': flavor_original,
        'translated': translated_oracle,
        'flavor_translated': translated_flavor
    }

