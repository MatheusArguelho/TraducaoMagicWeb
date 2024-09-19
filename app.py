from flask import Flask, render_template, request
from traducao_individual import process_card

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


if __name__ == '__main__':
    app.run(debug=True)
