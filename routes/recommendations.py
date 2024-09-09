from flask import Blueprint, session, render_template, request, redirect, url_for
from utils import generate_wordcloud
import nltk
from nltk.corpus import stopwords as nltk_stopwords
import os

recommendations_bp = Blueprint('recommendations_bp', __name__)

@recommendations_bp.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    messages = session.get('messages', [])

    if request.method == "GET":
        book_details = "<b>Título:</b> {}<br><b>Descrição:</b> {}<br><b>Autor:</b> {}".format(
            session.get('recommended_title'),
            session.get('recommended_description'),
            session.get('recommended_author')
        )
        messages.append({'sender': 'bot', 'text': book_details})
        capa_provisoria = url_for('static', filename='capa_provisoria.jpg')
        capa_message = f"<img src='{capa_provisoria}' alt='Capa do Livro' style='max-width: 200px; height: auto;'/>"
        capa_message += "<br>Se liga na capa!"
        messages.append({'sender': 'bot', 'text': capa_message})
        messages.append({'sender': 'bot', 'text': "Quer ver um WordCloud? Responda com 'sim' ou 'não'."})

    elif request.method == "POST":
        user_input = request.form.get("user_input", "").strip().lower()
        messages.append({'sender': 'user', 'text': user_input})

        if user_input == "sim":
            # Gerar o WordCloud
            nltk.download('punkt')
            stop_words_portuguese = nltk_stopwords.words('portuguese')
            font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            wordcloud_path = "/home/jufln/Projeto-IALC/static/wordcloud.png"

            generate_wordcloud(session['recommended_description'], font_path, stop_words_portuguese, wordcloud_path)

            messages.append({'sender': 'bot', 'text': f'Aqui está o seu WordCloud: <a href="{url_for("wordcloud_bp.wordcloud")}">www.wordcloud.com/bwbot</a>'})
        elif user_input == "não":
            messages.append({'sender': 'bot', 'text': 'Então tchau, até a próxima!'})
            session['messages'] = messages
            return render_template("recommendations.html", messages=messages, redirect_delay=True)
        else:
            messages.append({'sender': 'bot', 'text': "Desculpe, não entendi. Responda com 'sim' ou 'não'."})

    session['messages'] = messages
    return render_template("recommendations.html", messages=messages)

