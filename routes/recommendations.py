from flask import Blueprint, render_template, request, url_for, session, redirect
from utils import get_cached_dataframe, normalize_text, save_books_to_file, load_books_from_file
import json

recommendations_bp = Blueprint('recommendations_bp', __name__)

# Carregar o DataFrame de livros
df = get_cached_dataframe()

@recommendations_bp.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    messages = session.get('messages', [])
    books_file = request.args.get('books_file', None)
    
    if books_file:
        # Carregar os livros do arquivo temporário
        top_books = load_books_from_file(books_file)
    else:
        top_books = []

    descricao = request.args.get('descricao', None)

    if not descricao:
        livro_nome = session.get('livro_nome', None)
        livro_autor = session.get('livro_autor', None)
        genero = session.get('genero', None)

        if livro_nome and livro_autor:
            matching_books = df[(df['normalized_title'] == livro_nome) & (df['autor'] == livro_autor)]
            if not matching_books.empty:
                descricao = matching_books['cleaned_description'].iloc[0]
                session['descricao_base'] = descricao
                genero = matching_books['genero'].iloc[0]
            else:
                messages.append({'sender': 'bot', 'text': "Não consegui encontrar a descrição do livro no banco de dados."})
        else:
            messages.append({'sender': 'bot', 'text': "As informações do livro não foram encontradas."})

    if request.method == "GET":
        if top_books:
            messages.append({'sender': 'bot', 'text': "<b>Aqui estão alguns livros que podem te interessar!</b>"})

            # Listar os livros recomendados
            book_list = "<br>".join([f"{i+1}. {book['titulo']} - {book['autor']}" for i, book in enumerate(top_books)])
            messages.append({'sender': 'bot', 'text': book_list})
            messages.append({'sender': 'bot', 'text': "Gostaria de ver um histograma de palavras? Se não, me diga qual dos livros acima você gostaria de saber mais sobre."})

            session['histogram_choice'] = True

    elif request.method == "POST":
        user_input = request.form.get("user_input", "")
        messages.append({'sender': 'user', 'text': user_input})

        if user_input == "sair":
            # Limpar arquivos temporários (arquivos de recomendação)
            clear_temp_files()
            # Limpar a sessão
            session.clear()
            return redirect(url_for('chat_bp.chat'))

        if user_input == "sim" and "wordcloud_choice" in session:
            chosen_book = session.get('chosen_book', None)
            return redirect(url_for('wordcloud_bp.wordcloud', book_title=chosen_book))

        if user_input == "sim" and "histogram_choice" in session:
            if descricao:
                # Pegar as descrições dos livros recomendados
                top_books_descriptions = [book['cleaned_description'] for book in top_books]
                top_books_str = json.dumps(top_books_descriptions)

                # Gerar o link do histograma e passar as descrições pela URL
                histograma_link = url_for('histograma_bp.histograma', descricao=descricao, top_books=top_books_str)
                messages.append({'sender': 'bot', 'text': f"Aqui está o seu histograma: <a href='{histograma_link}'>hist.bookworm.com</a>"})
            else:
                messages.append({'sender': 'bot', 'text': "Algo deu errado, não foi possível gerar o histograma."})
            session.pop("histogram_choice", None)

        else:
            for book in top_books:
                if normalize_text(book['titulo']) == normalize_text(user_input):
                    respective = df[(df['normalized_title'] == normalize_text(book['titulo'])) & (df['autor'] == book['autor'])]
                    if not respective.empty:
                        chosen_description = respective['descricao'].iloc[0]

                    # Detalhes do livro
                    book_details = f"<b>Título:</b> {book['titulo']}<br><b>Descrição:</b> {chosen_description}<br><b>Autor:</b> {book['autor']}"
                    messages.append({'sender': 'bot', 'text': book_details})
                    
                    # Capa provisória do livro
                    capa_provisoria = url_for('static', filename='capa_provisoria.jpg')
                    capa_message = f"<img src='{capa_provisoria}' alt='Capa do Livro' style='max-width: 200px; height: auto;'/>"
                    capa_message += "<br>Se liga na capa!"
                    messages.append({'sender': 'bot', 'text': capa_message})

                    session['chosen_book'] = normalize_text(user_input)
                    session['chosen_description'] = chosen_description
                    messages.append({'sender': 'bot', 'text': "Gostaria de ver um WordCloud do livro? Digite 'sim' para ver o WordCloud, ou 'não' para voltar ao menu anterior."})
                    session['wordcloud_choice'] = True
                    session['histogram_choice'] = False
                    break
            else:
                messages.append({'sender': 'bot', 'text': "Desculpe, não encontrei o livro que você mencionou."})

        if user_input == "não":
            session.pop("wordcloud_choice", None)
            return redirect(url_for('recommendations_bp.recommendations'))

    session['messages'] = messages
    return render_template("recommendations.html", messages=messages, show_logo=True, show_credits=True)
