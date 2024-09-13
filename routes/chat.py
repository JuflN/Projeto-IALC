from flask import Blueprint, render_template, request, session, redirect, url_for
from utils import normalize_text, find_similar_books, process_dataframe
from aiml_engine import initialize_aiml_engine, load_aiml_for_step

chat_bp = Blueprint('chat_bp', __name__)

# Carregando o kernel AIML ao inicializar o engine
kernel = initialize_aiml_engine()

# Carregar o DataFrame de livros
df = process_dataframe()

@chat_bp.route("/", methods=["GET", "POST"])
def chat():
    # Limpa a sessão para reiniciar o bot ao acessar a página
    if request.method == "GET":
        # Quando o usuário entra pela primeira vez, iniciar o bot com o comando 'INICIAR'
        load_aiml_for_step("1", kernel)
        response = kernel.respond("INICIAR")
        session['messages'] = [{'sender': 'bot', 'text': response}]

    # Inicializa a sessão de mensagens caso ainda não tenha sido feita
    if 'messages' not in session:
        session['messages'] = []

    # Processa a entrada do usuário
    if request.method == "POST":
        u_input = request.form.get("user_input", "")
        user_input = normalize_text(u_input)
        session['messages'].append({'sender': 'user', 'text': user_input})

        # Obter o step atual do kernel
        step = kernel.getPredicate("step")

        # Carregar o arquivo AIML correspondente ao step atual
        load_aiml_for_step(step, kernel)

        # Processar a entrada do usuário com AIML
        response = kernel.respond(user_input)

        # Adiciona a resposta do bot às mensagens
        session['messages'].append({'sender': 'bot', 'text': response})

        # Verificação para o step 2: busca do livro no banco de dados
        if "Estou procurando o livro em nossa base de dados..." in response:
            livro_nome = kernel.getPredicate("livro").lower()

            # Busca o livro no DataFrame
            matching_books = df[df['normalized_title'] == livro_nome]
            if not matching_books.empty:
                # Se o livro foi encontrado, continue no step 3
                response = kernel.respond("func ENCONTREI O LIVRO")
            else:
                # Se o livro não foi encontrado, continue no step 7
                response = kernel.respond("func NAO ENCONTREI O LIVRO")
            session['messages'].append({'sender': 'bot', 'text': response})

        # Verificação para quando o usuário diz "sim" para querer livros do mesmo autor
        if "Ótimo! Qual nota você daria para o livro" in response:
            same_author = int(kernel.getPredicate("same_author"))
            livro_nome = normalize_text(kernel.getPredicate("livro"))

            if same_author == 1:  # Se o usuário quer livros do mesmo autor
                matching_books = df[df['normalized_title'] == livro_nome]
                livro_base_autor = matching_books['autor'].iloc[0]
                load_aiml_for_step("4", kernel)
                # Verificar quantos livros do autor existem
                autor_books = df[df['autor'].str.lower() == livro_base_autor.lower()]
                if len(autor_books) == 1:
                    # Informar que há apenas um livro do autor
                    response = kernel.respond("func TEM SO ESSE FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
                elif len(autor_books) == 0:
                    # Informar que não há livros do autor no DF
                    response = kernel.respond("func NAO TEM FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
                else:
                    # Continuar com a recomendação de livros do mesmo autor
                    top_books = autor_books.head(5).to_dict('records')
                    session['top_books'] = top_books

        # Caso o usuário esteja dando feedback após o step 5
        if "Obrigado por sua avaliação! Já tenho as informações necessárias para te indicar livros." in response:
            existe = int(kernel.getPredicate("existe"))

            if existe == 1:
                livro_nome = normalize_text(kernel.getPredicate("livro"))
                matching_books = df[df['normalized_title'] == livro_nome]
                livro_descricao = matching_books['descricao'].iloc[0]
                livro_base_autor = matching_books['autor'].iloc[0]

                # Continuar com a recomendação de livros similares
                similar_books = find_similar_books(livro_nome, existe, same_author=0, descricao=livro_descricao)
                top_books = similar_books.head(6)
                # Armazenando apenas os livros, excluindo o próprio livro base
                # Aplicar a função normalize_text usando lambda corretamente
                top_books_reduced = top_books.loc[top_books['normalized_title'] != livro_nome, ['titulo', 'autor']].head(5)


                # Armazenando apenas título e autor na sessão
                session['top_books'] = top_books_reduced.to_dict('records')
                session['livro_nome'] = livro_nome
                session['livro_autor'] = livro_base_autor
                session['same_author'] = kernel.getPredicate("same_author")
                session['messages'].clear()
                # Redirecionar para recommendations sem passar descrição e gênero, pois o livro está no DataFrame
                return redirect(url_for('recommendations_bp.recommendations'))

            else:
                # Caso o livro não exista, obter as informações fornecidas pelo usuário
                livro_nome = normalize_text(kernel.getPredicate("livro"))
                livro_descricao = kernel.getPredicate("descricao")
                livro_base_autor = kernel.getPredicate("autor")
                livro_base_genero = kernel.getPredicate("genero")

                # Filtrar por autor
                autor_books = df[df['autor'].str.lower() == livro_base_autor.lower()]

                if autor_books.empty:
                    response = kernel.respond("func NAO TEM FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                elif len(autor_books) == 1:
                    response = kernel.respond("func TEM SO ESSE FI")
                    session['messages'].append({'sender': 'bot', 'text': response})
                else:
                    # Recomendação para livros do mesmo autor
                    similar_books = find_similar_books(livro_nome, existe, same_author=1, descricao=livro_descricao)
                    top_books_reduced = top_books.loc[top_books['normalized_title'] != livro_nome, ['titulo', 'autor']].head(5)

                    # Armazenando apenas título e autor na sessão
                    session['top_books'] = top_books_reduced.to_dict('records')
                    session['livro_nome'] = livro_nome
                    session['livro_autor'] = livro_base_autor
                    session['same_author'] = kernel.getPredicate("same_author")
                    session['messages'].clear()
                    # Redirecionar para recommendations passando descrição e gênero pela URL
                    return redirect(url_for('recommendations_bp.recommendations', descricao=livro_descricao, genero=livro_base_genero))


    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)