from flask import Flask, render_template, request, redirect, url_for
import os
from traducao_individual import process_card
from traducao_set import func_traducao

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_text = request.form['card_name']
        result = process_card(original_text)
        if result:
            return render_template('carta_individual.html', **result)
        else:
            return "Erro ao processar a carta."
    return render_template('index.html')

@app.route('/traducao_set', methods=['GET', 'POST'])
def traducao_set():
    if request.method == 'POST':
        set_code = request.form['set_code']
        html_content = func_traducao(set_code)
        return render_template('resultado_set.html', html_content=html_content)
    return render_template('index_set.html')

@app.route('/resultado_set/<set_code>')
def resultado_set(set_code):
    return redirect(url_for('traducao_set'))

if __name__ == '__main__':
    app.run(debug=True)
