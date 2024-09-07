from flask import Blueprint, render_template, request, session, redirect, url_for
from utils import normalize_text, find_similar_books, process_dataframe
import aiml

chat_bp = Blueprint('chat_bp', __name__)

# Carregando o kernel AIML
kernel = aiml.Kernel()
kernel.learn("/home/jufln/Projeto-IALC/book_bot.aiml")

# Carregar o DataFrame
df = process_dataframe()

@chat_bp.route("/", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        session.clear()

    if 'messages' not in session:
        session['messages'] = []

    if request.method == "GET" and not session['messages']:
        bot_response = "Olá! Eu sou o seu assistente de recomendações de livros. Gostaria de receber uma indicação com base em um livro que você goste?"
        session['messages'].append({'sender': 'bot', 'text': bot_response})

    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        normalized_input = normalize_text(user_input)
        session['messages'].append({'sender': 'user', 'text': user_input})
        response = kernel.respond(normalized_input)

        if "Estou procurando o livro" in response:
            livro_nome = kernel.getPredicate("livro").lower()
            if livro_nome in df['normalized_title'].values:
                livro_descricao = df[df['normalized_title'] == livro_nome]['descricao'].iloc[0]
                similar_books = find_similar_books(livro_descricao)
                similar_books = similar_books[similar_books['normalized_title'] != livro_nome]

                if not similar_books.empty:
                    recommended_book = similar_books.iloc[0]
                    session['recommended_title'] = recommended_book['titulo']
                    session['recommended_description'] = recommended_book['descricao']
                    session['recommended_author'] = recommended_book['autor']
                    return redirect(url_for('recommendations_bp.recommendations'))
                else:
                    session['messages'].append({'sender': 'bot', 'text': f"Não encontrei um livro para recomendar com base em '{livro_nome}'."})
            else:
                session['messages'].append({'sender': 'bot', 'text': f"Não encontrei o livro '{livro_nome}' no meu banco de dados. Você pode descrever o livro para que eu tente recomendar algo similar?"})
                session['esperando_descricao'] = True

        elif session.get('esperando_descricao'):
            descricao_usuario = normalized_input
            if descricao_usuario.strip() != "":
                similar_books = find_similar_books(descricao_usuario)
                if not similar_books.empty:
                    recommended_book = similar_books.iloc[0]
                    session['recommended_title'] = recommended_book['titulo']
                    session['recommended_description'] = recommended_book['descricao']
                    session['recommended_author'] = recommended_book['autor']
                    session.pop('esperando_descricao', None)
                    return redirect(url_for('recommendations_bp.recommendations'))
                else:
                    session['messages'].append({'sender': 'bot', 'text': "Não encontrei livros semelhantes com base na descrição fornecida."})
            else:
                session['messages'].append({'sender': 'bot', 'text': "Por favor, descreva o livro para que eu possa buscar algo similar."})
        else:
            session['messages'].append({'sender': 'bot', 'text': response})

    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
