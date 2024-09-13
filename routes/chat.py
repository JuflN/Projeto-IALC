from flask import Blueprint, render_template, request, session, redirect, url_for
from utils import normalize_text, find_similar_books, process_dataframe
from aiml_engine import initialize_aiml_engine, load_aiml_for_step
import time  # Para o delay entre as respostas

chat_bp = Blueprint('chat_bp', __name__)

# Carregando o kernel AIML ao inicializar o engine
kernel = initialize_aiml_engine()

# Carregar o DataFrame de livros
df = process_dataframe()

@chat_bp.route("/", methods=["GET", "POST"])
def chat():
    # Limpa a sessão para reiniciar o bot ao acessar a página
    if request.method == "GET":
        session.clear()
        # Quando o usuário entra pela primeira vez, iniciar o bot com o comando 'INICIAR'
        load_aiml_for_step("1", kernel)
        response = kernel.respond("INICIAR")
        session['messages'] = [{'sender': 'bot', 'text': response}]

    # Inicializa a sessão de mensagens caso ainda não tenha sido feita
    if 'messages' not in session:
        session['messages'] = []

    # Processa a entrada do usuário
    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        normalized_input = normalize_text(user_input)
        session['messages'].append({'sender': 'user', 'text': user_input})

        # Obter o step atual do kernel
        step = kernel.getPredicate("step")

        # Carregar o arquivo AIML correspondente ao step atual
        load_aiml_for_step(step, kernel)

        # Processar a entrada do usuário com AIML
        response = kernel.respond(normalized_input)

        # Adiciona a resposta do bot às mensagens
        session['messages'].append({'sender': 'bot', 'text': response})

        # **Verificação para o step 2: busca do livro no banco de dados**
        if "Estou procurando o livro em nossa base de dados..." in response:
            livro_nome = kernel.getPredicate("livro").lower()

            # Busca o livro no DataFrame
            matching_books = df[df['normalized_title'] == livro_nome]
            if not matching_books.empty:
                # Se o livro foi encontrado, continue no step 3
                response = kernel.respond("func encontrei o livro")
            else:
                # Se o livro não foi encontrado, continue no step 7
                response = kernel.respond("func nao encontrei o livro")
            session['messages'].append({'sender': 'bot', 'text': response})

        # **Caso o usuário esteja dando feedback após o step 5**
        if "Obrigado por sua avaliação! Já tenho as informações necessárias para te indicar livros. Até a próxima!" in response:
            # Adicionar um delay de 3 segundos para mostrar a resposta final
            time.sleep(3)  # 3 segundos de atraso

            # Obter se o livro existe no DataFrame (0 ou 1)
            existe = int(kernel.getPredicate("existe"))

            # Verifica as preferências de autor e gênero
            same_author = int(kernel.getPredicate("same_author"))
            same_genre = int(kernel.getPredicate("same_genre"))

            if existe == 1:
                # Se o livro existe no DataFrame
                livro_nome = normalize_text(kernel.getPredicate("livro"))  # Normalizar o nome do livro
                matching_books = df[df['normalized_title'] == livro_nome]
                if not matching_books.empty:
                    livro_descricao = matching_books['descricao'].iloc[0]  # Obtém a descrição do DataFrame
                else:
                    livro_descricao = ""  # Caso o livro exista mas não seja encontrado corretamente
                livro_genero = matching_books['genero'].iloc[0]  # Obtém o gênero
            else:
                # Se o livro não existe, obtém as informações diretamente do AIML
                livro_nome = normalize_text(kernel.getPredicate("livro"))
                livro_descricao = kernel.getPredicate("descricao")  # Obtém a descrição fornecida pelo usuário
                livro_genero = kernel.getPredicate("genre")  # Obtém o gênero fornecido pelo usuário

            # Encontra os 5 livros mais parecidos
            similar_books = find_similar_books(livro_nome, existe, same_author=same_author, same_genre=same_genre, descricao=livro_descricao, genre=livro_genero)
            top_books = similar_books.head(5)

            # Passa os 5 livros encontrados para recommendations.py via sessão
            session['top_books'] = top_books.to_dict('records')  # Converte para uma lista de dicionários
            session['livro'] = livro_nome  # Passa o nome do livro base para recommendations.py

            # Redireciona para recommendations.py
            return redirect(url_for('recommendations_bp.recommendations'))

        # **Verificação para quando o usuário fornece uma descrição**
        if "Por favor me dê uma descrição da história para que eu possa aprender sobre ela." in response:
            livro_nome = kernel.getPredicate("livro").lower()
            livro_descricao = kernel.getPredicate("descricao")  # Obtém a descrição fornecida pelo usuário

            # Se a descrição for dada, continuar o fluxo
            if livro_descricao:
                response = kernel.respond("func descricao recebida")
                session['messages'].append({'sender': 'bot', 'text': response})

    # Renderiza o template com as mensagens
    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)
