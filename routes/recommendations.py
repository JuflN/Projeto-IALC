from flask import Blueprint, session, render_template, redirect, url_for, request
from utils import process_dataframe, find_similar_books, calcular_similaridade, gerar_histograma, normalize_text
import os
import numpy as np

recommendations_bp = Blueprint('recommendations_bp', __name__)

df = process_dataframe()

@recommendations_bp.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    messages = session.get('messages', [])
    top_books = session.get('top_books', [])

    if request.method == "GET":
        if 'Oi! Eu sou o bot BookWorm.' in messages[0]['text']:
            messages.pop(0)

        if not top_books:
            messages.append({'sender': 'bot', 'text': "<b>Aqui estão alguns livros que podem te interessar!</b>"})
            top_books = df.sample(5).to_dict('records')

        book_list = "<br>".join([f"{i+1}. {book['titulo']} - {book['autor']}" for i, book in enumerate(top_books)])
        messages.append({'sender': 'bot', 'text': book_list})
        messages.append({'sender': 'bot', 'text': "Gostaria de ver um histograma de similaridade? Se não, me diga qual dos livros acima você gostaria de saber mais sobre."})

    elif request.method == "POST":
        user_input = request.form.get("user_input", "").strip().lower()
        messages.append({'sender': 'user', 'text': user_input})

        if user_input == "sair":
            session.clear()
            return redirect(url_for('chat_bp.chat'))

        # Verifica se o usuário escolheu um livro da lista
        for book in top_books:
            if normalize_text(book['titulo']) == user_input:
                book_details = f"<b>Título:</b> {book['titulo']}<br><b>Descrição:</b> {book['descricao']}<br><b>Autor:</b> {book['autor']}"
                messages.append({'sender': 'bot', 'text': book_details})
                capa_provisoria = url_for('static', filename='capa_provisoria.jpg')
                capa_message = f"<img src='{capa_provisoria}' alt='Capa do Livro' style='max-width: 200px; height: auto;'/>"
                capa_message += "<br>Se liga na capa!"
                messages.append({'sender': 'bot', 'text': capa_message})
                messages.append({'sender': 'bot', 'text': "Quer ver um WordCloud? Responda com 'sim' ou 'não'."})
                session['chosen_book'] = book['titulo']
                break
        else:
            messages.append({'sender': 'bot', 'text': "Desculpe, não encontrei o livro que você mencionou."})

        # Geração do histograma
        if user_input == "sim":
            livro_base = session.get('livro', None)
            livro_base_autor = session.get('author', None)
            preferencia_autor = session.get('same_author', 0) == 1

            if livro_base and livro_base in df['normalized_title'].values:
                livro_base_descricao = df.loc[df['normalized_title'] == livro_base, 'cleaned_description'].values[0]
                livro_base_autor = df.loc[df['normalized_title'] == livro_base, 'autor'].values[0]
            else:
                livro_base_descricao = session.get('descricao', None)
                if not livro_base_descricao:
                    messages.append({'sender': 'bot', 'text': "Não foi possível determinar as informações do livro base."})
                    return render_template("recommendations.html", messages=messages)

            similaridade = calcular_similaridade(
                livro_base_descricao,
                preferencia_autor=preferencia_autor,
                livro_base_autor=livro_base_autor
            )

            top_indices = np.argsort(similaridade)[::-1][:10]
            top_books_to_plot = df.iloc[top_indices]

            hist_path = gerar_histograma(top_books_to_plot, livro_base)

            hist_link = "<a href='/histograma'>histograma.bookworm</a>"
            messages.append({'sender': 'bot', 'text': f"Aqui está seu link para acessar o histograma: {hist_link}"})

        if user_input == "voltar":
            return redirect(url_for('recommendations_bp.recommendations'))

    session['messages'] = messages
    return render_template("recommendations.html", messages=messages)
