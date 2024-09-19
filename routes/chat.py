from flask import Blueprint, render_template, request, session, redirect, url_for
from utils import normalize_text, find_similar_books, process_dataframe, save_books_to_file
from aiml_engine import initialize_aiml_engine, load_aiml_for_step

chat_bp = Blueprint('chat_bp', __name__)

# Carregando o kernel AIML ao inicializar o engine
kernel = initialize_aiml_engine()

# Carregar o DataFrame de livros
df = process_dataframe()

@chat_bp.route("/", methods=["GET", "POST"])
def chat():
    # Inicializa a sessão de mensagens se ainda não tiver sido feita
    if 'messages' not in session:
        session['messages'] = []

    if request.method == "GET":
        # Verifica se a lista de mensagens está vazia e se é a primeira visita
        if not session['messages']:
            load_aiml_for_step("1", kernel)
            response = kernel.respond("INICIAR")
            session['messages'].append({'sender': 'bot', 'text': response})

    if request.method == "POST":
        if session['messages'] and "Oi! Eu sou o bot BookWorm" in session['messages'][0]['text']:
            session['messages'].pop(0)

        u_input = request.form.get("user_input", "")
        user_input = normalize_text(u_input)
        session['messages'].append({'sender': 'user', 'text': user_input})

        if user_input == "sair":
            # Limpar arquivos temporários (arquivos de recomendação)
            clear_temp_files()
            # Limpar a sessão
            session.clear()
            return redirect(url_for('chat_bp.chat'))

        step = kernel.getPredicate("step")
        load_aiml_for_step(step, kernel)
        response = kernel.respond(user_input)
        session['messages'].append({'sender': 'bot', 'text': response})

        if "Estou procurando o livro em nossa base de dados..." in response:
            livro_nome = kernel.getPredicate("livro").lower()
            matching_books = df[df['normalized_title'] == livro_nome]
            if not matching_books.empty:
                response = kernel.respond("func ENCONTREI O LIVRO")
            else:
                response = kernel.respond("func NAO ENCONTREI O LIVRO")
            session['messages'].append({'sender': 'bot', 'text': response})

        if "Ótimo! Qual nota você daria para o livro" in response:
            same_author = int(kernel.getPredicate("same_author"))
            livro_nome = normalize_text(kernel.getPredicate("livro"))

            if same_author == 1:
                matching_books = df[df['normalized_title'] == livro_nome]
                livro_base_autor = matching_books['autor'].iloc[0]
                load_aiml_for_step("4", kernel)
                autor_books = df[df['autor'].str.lower() == livro_base_autor.lower()]
                if len(autor_books) == 1:
                    response = kernel.respond("func TEM SO ESSE FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
                elif len(autor_books) == 0:
                    response = kernel.respond("func NAO TEM FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
                else:
                    top_books_description = autor_books.head(5)[['cleaned_description']].to_dict('records')
                    file_path = save_books_to_file(top_books_description)
                    return redirect(url_for('recommendations_bp.recommendations', file_path=file_path))

        if "Obrigado por sua avaliação!" in response:
            existe = int(kernel.getPredicate("existe"))

            if existe == 1:
                livro_nome = normalize_text(kernel.getPredicate("livro"))
                matching_books = df[df['normalized_title'] == livro_nome]
                livro_descricao = matching_books['descricao'].iloc[0]
                similar_books = find_similar_books(livro_nome, existe, same_author=0, descricao=livro_descricao)
                top_books_description = similar_books.loc[similar_books['normalized_title'] != livro_nome, ['cleaned_description']].head(5).to_dict('records')
                file_path = save_books_to_file(top_books_description)
                session['messages'].clear()
                return redirect(url_for('recommendations_bp.recommendations', file_path=file_path))

            else:
                livro_nome = normalize_text(kernel.getPredicate("livro"))
                livro_descricao = kernel.getPredicate("descricao")
                livro_base_autor = kernel.getPredicate("autor")
                livro_base_genero = kernel.getPredicate("genero")
                autor_books = df[df['autor'].str.lower() == livro_base_autor.lower()]

                if autor_books.empty:
                    response = kernel.respond("func NAO TEM FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                elif len(autor_books) == 1:
                    response = kernel.respond("func TEM SO ESSE FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                else:
                    similar_books = find_similar_books(livro_nome, existe, same_author=1, descricao=livro_descricao)
                    top_books_description = similar_books.loc[similar_books['normalized_title'] != livro_nome, ['cleaned_description']].head(5).to_dict('records')
                    file_path = save_books_to_file(top_books_description)
                    session['messages'].clear()
                    return redirect(url_for('recommendations_bp.recommendations', file_path=file_path))

    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
