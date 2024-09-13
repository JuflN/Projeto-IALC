from flask import Blueprint, render_template, url_for, session
from utils import generate_wordcloud, stop_words_portuguese
import os

wordcloud_bp = Blueprint('wordcloud_bp', __name__)

@wordcloud_bp.route("/wordcloud")
def wordcloud():
    # Obtendo a descrição do livro via URL
    cleaned_description = session.get('chosen_description', None)

    if cleaned_description:
        # Definir caminho para salvar o arquivo da WordCloud
        #wordcloud_path = os.path.join('static', 'wordcloud.png')

        # Gerar o WordCloud
        generate_wordcloud(cleaned_description=cleaned_description, stop_words=stop_words_portuguese)

        # Retornar o template com o WordCloud gerado
        wordcloud_link = url_for('static', filename='wordcloud.png')
        return render_template("wordcloud.html", show_logo=True, show_credits=True, wordcloud_link=wordcloud_link)

    else:
        return render_template("wordcloud.html", show_logo=True, show_credits=True, error="Descrição do livro não fornecida.")
