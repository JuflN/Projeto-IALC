from data_processing import find_similar_books
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
        
        # Verifica se o livro existe e se há mais de um autor para o mesmo título
        matching_books = df[df['normalized_title'] == livro_nome]
        if not matching_books.empty:
            if matching_books['autor'].nunique() > 1:
                # Se houver mais de um autor, pergunte ao usuário qual autor ele prefere
                autores = matching_books['autor'].unique()
                autores_str = ', '.join(autores)
                session['messages'].append({'sender': 'bot', 'text': f"Encontrei vários autores para '{livro_nome}'. Qual autor você prefere? Opções: {autores_str}"})
                session['esperando_autor'] = True
                session['livro_nome'] = livro_nome
            else:
                # Se houver apenas um autor, continue com o fluxo normal
                livro_descricao = matching_books['descricao'].iloc[0]
                livro_genero = matching_books['genero'].iloc[0]
                livro_autor = matching_books['autor'].iloc[0]
                # Pergunta se o usuário quer livros apenas do mesmo autor
                session['messages'].append({'sender': 'bot', 'text': "Gostaria de apenas ver livros do mesmo autor? (sim/não)"})
                session['esperando_autor_pref'] = True
                session['livro_nome'] = livro_nome
                session['livro_descricao'] = livro_descricao
                session['livro_genero'] = livro_genero
                session['livro_autor'] = livro_autor
        else:
            session['messages'].append({'sender': 'bot', 'text': "Desculpe, não encontrei o livro que você está procurando."})

    # Verifica se o bot está esperando a escolha do autor
    elif session.get('esperando_autor'):
        autor_escolhido = user_input.strip()
        livro_nome = session.get('livro_nome', '')

        # Filtrar pelo autor escolhido
        matching_books = df[(df['normalized_title'] == livro_nome) & (df['autor'].str.lower() == autor_escolhido.lower())]
        if not matching_books.empty:
            livro_descricao = matching_books['descricao'].iloc[0]
            livro_genero = matching_books['genero'].iloc[0]
            livro_autor = matching_books['autor'].iloc[0]
            # Pergunta se o usuário quer livros apenas do mesmo autor
            session['messages'].append({'sender': 'bot', 'text': "Gostaria de apenas ver livros do mesmo autor? (sim/não)"})
            session['esperando_autor_pref'] = True
            session['livro_nome'] = livro_nome
            session['livro_descricao'] = livro_descricao
            session['livro_genero'] = livro_genero
            session['livro_autor'] = livro_autor
        else:
            session['messages'].append({'sender': 'bot', 'text': "Desculpe, não encontrei o autor que você escolheu."})
        
        # Limpa a variável de sessão relacionada à escolha do autor
        session.pop('esperando_autor', None)

    # Verifica se o bot está esperando a resposta sobre a preferência de autor
    elif session.get('esperando_autor_pref'):
        if user_input.strip().lower() == "sim":
            autor_pref = True
        else:
            autor_pref = False
        
        livro_nome = session['livro_nome']
        livro_descricao = session['livro_descricao']
        livro_genero = session['livro_genero']
        livro_autor = session['livro_autor']
        
        similar_books = find_similar_books(df, livro_descricao, livro_genero, livro_autor, autor_pref)
        similar_books = similar_books[similar_books['normalized_title'] != livro_nome]

        if not similar_books.empty:
            recommended_book = similar_books.iloc[0]
            session['recommended_title'] = recommended_book['titulo']
            session['recommended_description'] = recommended_book['descricao']
            session['recommended_author'] = recommended_book['autor']
            return redirect(url_for('recommendations_bp.recommendations'))
        else:
            session['messages'].append({'sender': 'bot', 'text': f"Não encontrei um livro para recomendar com base em '{livro_nome}'."})
        
        # Limpa as variáveis de sessão relacionadas à preferência de autor
        session.pop('esperando_autor_pref', None)
        session.pop('livro_nome', None)
        session.pop('livro_descricao', None)
        session.pop('livro_genero', None)
        session.pop('livro_autor', None)  

    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
