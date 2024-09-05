from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords as nltk_stopwords
from wordcloud import WordCloud
import aiml
import secrets
import unicodedata
import re
#nltk.data.path.append('./nltk_data')


app = Flask(__name__)
# Definir a chave secreta
app.secret_key = secrets.token_hex(16)

# Definir o caminho da fonte TrueType
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

#Instalar / Carregar a base de dados
#file_id = "1enaXPre4GrRN3GYWRMo0tovVE_FyPgu2"
#url = f"https://drive.google.com/uc?id={file_id}"
#output = "dados.csv"
#gdown.download(url, output, quiet=False)

def normalize_text(text):
    # Remover acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Converter para minúsculas para uniformidade
    return text.lower()
# Preprocessamento
df_total = pd.read_csv("/home/jufln/Projeto-IALC/dados.csv")

# Filtrando colunas de interesse
df = df_total[['titulo', 'autor', 'descricao', 'genero', 'male', 'female']]

# Normalizar os títulos no DataFrame para garantir uma comparação justa
df['normalized_title'] = df['titulo'].apply(normalize_text)

# Garantir que a coluna 'descricao' seja uma string e tratar valores ausentes
df['descricao'] = df['descricao'].astype(str).fillna('')

nltk.download('punkt')
stop_words_portuguese = nltk_stopwords.words('portuguese')

# Função para remover acentos e caracteres especiais
def normalize_input(text):
    # Remover acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Remover números e caracteres especiais (manter letras e espaços)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text.lower()  # Converter para minúsculas para uniformidade

def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words_portuguese and t.isalnum()]  # Verificar se a palavra não é stopword e é alfanumérica
    return ' '.join(tokens)

# Aplicar o pré-processamento na coluna 'descricao'
df['cleaned_description'] = df['descricao'].apply(preprocess)

# TF-IDF
vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
tfidf_matrix = vectorizer.fit_transform(df['cleaned_description'])

def find_similar_books(description, top_n=5):
    query_tfidf = vectorizer.transform([preprocess(description)])
    cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    similar_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return df.iloc[similar_indices]

def preprocess_text(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalnum()]
    return ' '.join(tokens)

def expand_query(query):
    # Expansão simples de palavras (usar uma técnica mais avançada como Word2Vec seria ideal)
    return query  # Por enquanto, retornamos a query original, mas aqui você pode usar sinônimos ou embeddings.

def find_books_based_on_description(user_description, df, top_n=5):
    processed_description = preprocess_text(user_description)
    # Expande a descrição (por enquanto apenas um placeholder)
    expanded_description = expand_query(processed_description)
    # Aplica TF-IDF na descrição do usuário e no DataFrame
    vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
    tfidf_matrix = vectorizer.fit_transform(df['cleaned_description'])
    query_tfidf = vectorizer.transform([expanded_description])
    cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    similar_indices = cosine_similarities.argsort()[-top_n:][::-1]

    return df.iloc[similar_indices]

# AIML
kernel = aiml.Kernel()
kernel.learn("/home/jufln/Projeto-IALC/book_bot.aiml")

@app.route("/credits")
def credits():
    return render_template("credits.html",show_logo=False, show_credits=False)

@app.route("/", methods=["GET", "POST"])
def chat():
    bot_response = "Olá! Eu sou o seu assistente de recomendações de livros. Gostaria de receber uma indicação com base em um livro que você goste?"

    if request.method == "POST":
        user_input = request.form.get("user_input", "")

        # Preprocessar a entrada do usuário (normalizar removendo acentos e colocando em minúsculas)
        normalized_input = normalize_text(user_input)

        # Passar a entrada para o AIML
        response = kernel.respond(normalized_input)

        if "Estou procurando o livro" in response:
            livro_nome = kernel.getPredicate("livro").lower()

            # Verificar se o livro normalizado está no banco de dados com os títulos normalizados
            if livro_nome in df['normalized_title'].values:
                livro_descricao = df[df['normalized_title'] == livro_nome]['descricao'].iloc[0]
                similar_books = find_similar_books(livro_descricao)
                similar_books = similar_books[similar_books['normalized_title'] != livro_nome]

                if not similar_books.empty:
                    recommended_book = similar_books.iloc[0]
                    session['recommended_title'] = recommended_book['titulo']  # O título original, com acentos
                    session['recommended_description'] = recommended_book['descricao']
                    session['recommended_author'] = recommended_book['autor']

                    wordcloud = WordCloud(stopwords=stop_words_portuguese, background_color="white", font_path=font_path).generate(recommended_book['cleaned_description'])
                    wordcloud_path = "/home/jufln/Projeto-IALC/static/wordcloud.png"
                    wordcloud.to_file(wordcloud_path)

                    session['wordcloud_path'] = wordcloud_path
                    return redirect(url_for('recommendations'))
                else:
                    bot_response = f"Não encontrei um livro para recomendar com base em '{livro_nome}'."
            else:
                bot_response = f"Não encontrei o livro '{livro_nome}' no meu banco de dados. Você pode descrever o livro para que eu tente recomendar algo similar?"
                session['esperando_descricao'] = True

        elif session.get('esperando_descricao'):
            descricao_usuario = normalized_input
            if descricao_usuario.strip() != "":
                similar_books = find_similar_books(descricao_usuario)
                if not similar_books.empty:
                    recommended_book = similar_books.iloc[0]
                    session['recommended_title'] = recommended_book['titulo']  # O título original, com acentos
                    session['recommended_description'] = recommended_book['descricao']
                    session['recommended_author'] = recommended_book['autor']

                    wordcloud = WordCloud(stopwords=stop_words_portuguese, background_color="white", font_path=font_path).generate(recommended_book['cleaned_description'])
                    wordcloud_path = "/home/jufln/Projeto-IALC/static/wordcloud.png"
                    wordcloud.to_file(wordcloud_path)

                    session['wordcloud_path'] = wordcloud_path
                    session.pop('esperando_descricao', None)
                    return redirect(url_for('recommendations'))
                else:
                    bot_response = "Não encontrei livros semelhantes com base na descrição fornecida."
            else:
                bot_response = "Por favor, descreva o livro para que eu possa buscar algo similar."
        else:
            bot_response = response

    return render_template("index.html", bot_response=bot_response, show_logo=True, show_credits=True)

@app.route("/recommendations")
def recommendations():
    return render_template("recommendations.html",
                           recommended_title=session.get('recommended_title'),
                           recommended_description=session.get('recommended_description'),
                           wordcloud_path=session.get('wordcloud_path'),
                           recommended_author=session.get('recommended_author'),
                           show_logo=True, show_credits=True)

@app.route('/wordcloud')
def wordcloud():
    # Lógica para exibir a wordcloud
    return render_template("wordcloud.html",show_logo=True, show_credits=True)


if __name__ == "__main__":
    app.run()
