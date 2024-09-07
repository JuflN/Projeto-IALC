from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords as nltk_stopwords
from wordcloud import WordCloud
import aiml
import unicodedata
import secrets

app = Flask(__name__)

#Configurando chave secreta
app.secret_key = secrets.token_hex(16)

# Definir o caminho da fonte TrueType
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# Certificar-se de que as stopwords estão carregadas
#nltk.download('punkt')
stop_words_portuguese = nltk_stopwords.words('portuguese')

# Função para normalizar o texto (remover acentos, etc.)
def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

# Função para preprocessamento (tokenização, remoção de stopwords e caracteres não alfanuméricos)
def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words_portuguese and t.isalnum()]
    return ' '.join(tokens)

# Carregar e tratar o DataFrame
def process_dataframe():
    df = pd.read_csv("/home/jufln/Projeto-IALC/dados.csv", encoding='utf-8')
    
    # Normalizar os títulos no DataFrame
    df['normalized_title'] = df['titulo'].apply(normalize_text)
    
    # Garantir que a coluna 'descricao' seja uma string e tratar valores ausentes
    df['descricao'] = df['descricao'].astype(str).fillna('')
    
    # Preprocessar a descrição para obter a versão "cleaned_description"
    df['cleaned_description'] = df['descricao'].apply(preprocess)
    
    # Retorna o DataFrame tratado
    return df

# Aplicar o tratamento no DataFrame
df = process_dataframe()

# Salvar o DataFrame tratado em um novo CSV, se necessário
df.to_csv("/home/jufln/Projeto-IALC/dados_tratados.csv", index=False, encoding='utf-8')  # Salvar com UTF-8

# TF-IDF
vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
tfidf_matrix = vectorizer.fit_transform(df['cleaned_description'])

def find_similar_books(description, top_n=5):
    query_tfidf = vectorizer.transform([preprocess(description)])
    cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    similar_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return df.iloc[similar_indices]

# AIML
kernel = aiml.Kernel()
kernel.learn("/home/jufln/Projeto-IALC/book_bot.aiml")

@app.route("/credits")
def credits():
    return render_template("credits.html", show_logo=False, show_credits=False)

@app.route("/", methods=["GET", "POST"])
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

                    wordcloud = WordCloud(stopwords=stop_words_portuguese, background_color="white", font_path=font_path).generate(recommended_book['cleaned_description'])
                    wordcloud_path = "/home/jufln/Projeto-IALC/static/wordcloud.png"
                    wordcloud.to_file(wordcloud_path)

                    session['wordcloud_path'] = wordcloud_path
                    return redirect(url_for('recommendations'))
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

                    wordcloud = WordCloud(stopwords=stop_words_portuguese, background_color="white", font_path=font_path).generate(recommended_book['cleaned_description'])
                    wordcloud_path = "/home/jufln/Projeto-IALC/static/wordcloud.png"
                    wordcloud.to_file(wordcloud_path)

                    session['wordcloud_path'] = wordcloud_path
                    session.pop('esperando_descricao', None)
                    return redirect(url_for('recommendations'))
                else:
                    session['messages'].append({'sender': 'bot', 'text': "Não encontrei livros semelhantes com base na descrição fornecida."})
            else:
                session['messages'].append({'sender': 'bot', 'text': "Por favor, descreva o livro para que eu possa buscar algo similar."})
        else:
            session['messages'].append({'sender': 'bot', 'text': response})

    return render_template("index.html", messages=session.get('messages', []), show_logo=True, show_credits=True)

@app.route("/recommendations", methods=["GET", "POST"])
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
            messages.append({'sender': 'bot', 'text': 'Aqui está o seu WordCloud: <a href="/wordcloud">wordcloud.link</a>'})
        elif user_input == "não":
            messages.append({'sender': 'bot', 'text': 'Então tchau, até a próxima!'})
            session['messages'] = messages
            return render_template("recommendations.html", messages=messages, redirect_delay=True)
        else:
            messages.append({'sender': 'bot', 'text': "Desculpe, não entendi. Responda com 'sim' ou 'não'."})

    session['messages'] = messages
    return render_template("recommendations.html", messages=messages)

@app.route('/wordcloud')
def wordcloud():
    return render_template("wordcloud.html", show_logo=True, show_credits=True)

if __name__ == "__main__":
    app.run()
