from flask import Blueprint, session, render_template, redirect, url_for, request
from utils import process_dataframe, gerar_histograma, normalize_text

recommendations_bp = Blueprint('recommendations_bp', __name__)

df = process_dataframe()

@recommendations_bp.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    messages = session.get('messages', [])
    top_books = session.get('top_books', [])

    # Primeiro, verificamos se a descrição e o gênero foram passados pela URL
    descricao = request.args.get('descricao', None)
    genero = request.args.get('genero', None)

    # Se não recebemos a descrição pela URL, tentamos buscar no DataFrame pelo título e autor
    if not descricao:
        livro_nome = session.get('livro_nome', None)
        livro_autor = session.get('livro_autor', None)

        # Certifique-se de que temos o título e autor disponíveis na sessão
        if livro_nome and livro_autor:
            # Procura o livro pelo título normalizado e autor
            matching_books = df[(df['normalized_title'] == livro_nome) & (df['autor'] == livro_autor)]
            if not matching_books.empty:
                descricao = matching_books['cleaned_description'].iloc[0]
                session['descricao_base']=descricao
                genero = matching_books['genero'].iloc[0]  # Garantimos que também buscamos o gênero
            else:
                messages.append({'sender': 'bot', 'text': "Não consegui encontrar a descrição do livro no banco de dados."})
        else:
            messages.append({'sender': 'bot', 'text': "As informações do livro não foram encontradas."})

    if request.method == "GET":
        if top_books:
            # Exibir os livros recomendados
            messages.append({'sender': 'bot', 'text': "<b>Aqui estão alguns livros que podem te interessar!</b>"})

            # Criar a lista de livros recomendados
            book_list = "<br>".join([f"{i+1}. {book['titulo']} - {book['autor']}" for i, book in enumerate(top_books)])

            # Adicionar a lista de livros às mensagens
            messages.append({'sender': 'bot', 'text': book_list})

            # Perguntar se o usuário deseja ver um histograma ou mais detalhes sobre um dos livros
            messages.append({'sender': 'bot', 'text': "Gostaria de ver um histograma de palavras? Se não, me diga qual dos livros acima você gostaria de saber mais sobre."})

            session['histogram_choice'] = True # Define estado para saber que é uma escolha de Histograma

    elif request.method == "POST":
        user_input = request.form.get("user_input", "")
        messages.append({'sender': 'user', 'text': user_input})

        # Verificação para saída do chat
        if user_input == "sair":
            session.clear()
            return redirect(url_for('chat_bp.chat'))

        # Responder "sim" gera o wordcloud
        if user_input == "sim" and "wordcloud_choice" in session:
            session['descricao_base'] = descricao
            chosen_book = session.get('chosen_book', None)
            return redirect(url_for('wordcloud_bp.wordcloud', book_title=chosen_book))

        if user_input == "sim" and "histogram_choice" in session:
            # Gera o histograma apenas se a descrição estiver disponível
            if descricao:
                histograma_link = url_for('histograma_bp.histograma')  # Aqui, 'wordcloud_bp.wordcloud' deve corresponder ao nome da rota registrada
                messages.append({'sender': 'bot', 'text': f"Aqui está o seu histograma: <a href='{histograma_link}'>hist.bookworm.com</a>"})
            else:
                messages.append({'sender': 'bot', 'text': "Algo deu errado, não foi possível gerar o histograma."})
            session.pop("histogram_choice", None)  # Limpa o estado do histograma para o próximo fluxo

        else:
            # Verificar se o usuário escolheu um livro da lista
            for book in top_books:
                if normalize_text(book['titulo']) == normalize_text(user_input):

                    respective = df[(df['normalized_title'] == normalize_text(book['titulo'])) & (df['autor'] == book['autor'])]
                    if not respective.empty:
                        choosen_descricao = respective['descricao'].iloc[0]

                    book_details = f"<b>Título:</b> {book['titulo']}<br><b>Descrição:</b> {choosen_descricao}<br><b>Autor:</b> {book['autor']}"
                    messages.append({'sender': 'bot', 'text': book_details})
                    capa_provisoria = url_for('static', filename='capa_provisoria.jpg')
                    capa_message = f"<img src='{capa_provisoria}' alt='Capa do Livro' style='max-width: 200px; height: auto;'/>"
                    capa_message += "<br>Se liga na capa!"
                    messages.append({'sender': 'bot', 'text': capa_message})

                    # Armazena o título e descrição do livro escolhido para o WordCloud
                    session['chosen_book'] = normalize_text(user_input)
                    session['chosen_description'] = choosen_descricao

                    # Pergunta se o usuário deseja ver o WordCloud
                    messages.append({'sender': 'bot', 'text': "Gostaria de ver um WordCloud do livro? Digite 'sim' para ver o WordCloud, ou 'não' para voltar ao menu anterior."})
                    session['wordcloud_choice'] = True  # Define estado para saber que é uma escolha de WordCloud
                    session['histogram_choice'] = False # Define estado para saber que é uma escolha de WordCloud
                    break
            else:
                messages.append({'sender': 'bot', 'text': "Desculpe, não encontrei o livro que você mencionou."})

        # Verifica se o usuário escolheu voltar ao menu
        if user_input == "não":
            session.pop("wordcloud_choice", None)  # Limpa o estado do WordCloud
            return redirect(url_for('recommendations_bp.recommendations'))

    session['messages'] = messages
    return render_template("recommendations.html", messages=messages,  show_logo=True, show_credits=True)
