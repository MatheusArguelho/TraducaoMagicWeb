import pandas as pd
from deep_translator import GoogleTranslator
import requests
import csv
from tqdm import tqdm
import webbrowser
import os
import json

CACHE_FILE = "translation_cache.json"

# Função para carregar o cache do arquivo JSON
def load_translation_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    return {}

# Função para salvar o cache no arquivo JSON sem sobrescrever
def save_translation_cache(new_cache_entry):
    # Carrega o cache existente (se houver)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            json_cache = json.load(file)
    else:
        json_cache = {}

    # Atualiza o cache com a nova entrada
    json_cache.update(new_cache_entry)

    # Salva o cache atualizado
    with open(CACHE_FILE, 'w') as file:
        json.dump(json_cache, file)


# Inicializar o cache de traduções
translation_cache = {}  # Cache em memória
json_cache = load_translation_cache()  # Cache em JSON

def download_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise Exception("Set não encontrado, Erro 404")
    else:
        raise Exception(f"Falha, codigo: {response.status_code}")

def process_card_data(card):
    try:
        oracle_texto = card["oracle_text"]
    except KeyError:
        try:
            oracle_texto = card['card_faces'][0]['oracle_text'] + '\n' + '----' + '\n' + card['card_faces'][1]['oracle_text']
        except KeyError:
            oracle_texto = ''
    return {
        "num": card.get("collector_number", ""),
        "name": card["name"],
        "oracle_text": oracle_texto
    }

def filter_card_data(df):
    df = df[~df['num'].str.contains('z')]
    names_to_drop = ['Plains', 'Swamp', 'Island', 'Mountain', 'Forest']
    return df[~df['name'].isin(names_to_drop)]

# Função para verificar e traduzir textos de cartas com cache
def translate_and_format_text(card_name, text):
    cache_key = f"{card_name}_oracle"

    # Verifica se a tradução está no cache em memória
    if cache_key in translation_cache:
        return translation_cache[cache_key]['translated_text']

    # Verifica o cache no arquivo JSON
    if cache_key in json_cache:
        return json_cache[cache_key]['translated_text']

    # Se não estiver no cache, faz a tradução
    translated = GoogleTranslator(source='auto', target='pt').translate(text=text)
    formatted_text = translated.replace('\n', '<br>')

    # Armazena no cache em memória e JSON
    translation_cache[cache_key] = {
        'original_text': text,
        'translated_text': formatted_text
    }
    json_cache[cache_key] = {
        'original_text': text,
        'translated_text': formatted_text
    }

    # Salva o cache atualizado
    save_translation_cache(json_cache)

    return formatted_text

def translate_card_texts(df):
    translated_texts = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Translating cards"):
        card_name = row['name']
        oracle_text = row['oracle_text']
        translated_text = translate_and_format_text(card_name, oracle_text)
        translated_texts.append(translated_text)
    return translated_texts

def save_csv_file(df, file_path):
    df.to_csv(file_path, index=False, encoding='utf-8')

def create_html_table(rows):
    html_table = '<table class="styled-table">\n'
    for row in rows:
        html_table += '  <tr>\n'
        for cell in row:
            # Replace '\n' with '<br>' in cell content
            cell_content = cell.replace('\n', '<br>')
            html_table += f'    <td>{cell_content}</td>\n'
        html_table += '  </tr>\n'
    html_table += '</table>'
    return html_table

def read_html_template(template_path):
    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()

def fill_html_template(template_content, set_code, html_table):
    return template_content.format(set_code=set_code, html_table=html_table)

def save_html_file(html_content, file_path):
    with open(file_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

def open_html_file(html_file_path):
    webbrowser.open(html_file_path)

def func_traducao(set_code):
    try:
        set_url = f"https://api.scryfall.com/sets/{set_code}"
        set_json = download_json(set_url)
        if set_json and 'search_uri' in set_json:
            url = set_json['search_uri']
        else:
            raise Exception("Falha ao obter o URL de pesquisa do conjunto JSON")

        all_card_data = []
        while url:
            json_data = download_json(url)
            all_card_data.extend([process_card_data(card) for card in json_data["data"]])
            url = json_data.get("next_page")

        df = pd.DataFrame(all_card_data)

        if not df.empty:
            df.index += 1
            df['oracle_text'] = df['oracle_text'].fillna(value='DEBUG', inplace=False)

        df = filter_card_data(df)

        translated_texts = translate_card_texts(df)
        df['traduzido'] = translated_texts

        df = df.rename(columns={'num': 'numero', 'name': 'nome', 'oracle_text': 'texto_ingles'})

        save_csv_file(df, 'traducao.csv')

        with open('traducao.csv', 'r', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile)
            rows = list(csvreader)

        html_table = create_html_table(rows)

        # Retorna o HTML diretamente aqui
        return html_table

    except Exception as e:
        print(e)
        return f"Erro: {e}"


if __name__ == "__main__":
    func_traducao()
