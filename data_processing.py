import pandas as pd
import nltk
from nltk.corpus import stopwords as nltk_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
# Adição
from sklearn.metrics.pairwise import cosine_similarity
import unicodedata

# Carregar stopwords
nltk.download('punkt')
stop_words_portuguese = nltk_stopwords.words('portuguese')

# Função para normalizar o texto (remover acentos, etc.)
def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

# Função para preprocessamento (tokenização, remoção de stopwords e caracteres não alfanuméricos)
def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [t for t in tokens if t not in stop_words_portuguese and t.isalnum()]
    return ' '.join(tokens)

# Carregar e processar o DataFrame
def process_dataframe():
    df = pd.read_csv("/home/jufln/Projeto-IALC/dados.csv", encoding='utf-8')
    df['normalized_title'] = df['titulo'].apply(normalize_text)
    df['descricao'] = df['descricao'].astype(str).fillna('')
    df['cleaned_description'] = df['descricao'].apply(preprocess)
    df['normalized_genre'] = df['genero'].apply(normalize_text)
    df['normalized_author'] = df['autor'].apply(normalize_text)
    return df

# Função para encontrar livros semelhantes usando TF-IDF
def find_similar_books(df, description, genres, author, top_n=5):
    # Vetorização TF-IDF das descrições
    vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
    tfidf_matrix = vectorizer.fit_transform(df['cleaned_description'])
    query_tfidf = vectorizer.transform([preprocess(description)])
    
    #Similaridade cosseno das descrições
    cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    
    # Similaridade de gênero (1 se igual, 0 se diferente)
    genre_similarity = df['normalized_genre'].apply(lambda x: 1 if any(genre in x for genre in genres) else 0)

    #Similaridade de autor (1 se igual, 0 se diferente)
    author_similarity = df['normalized_author'].apply(lambda x: 1 if x == author else 0)

    # Pesos
    weight_cosine = 3
    weight_genre = 2
    weight_author = 1

    # Similaridade ponderada, futuramente será usada como eixo do histograma
    weighted_similarity = (weight_cosine * cosine_similarities) + (weight_genre * genre_similarity) + (weight_author * author_similarity)

    # Índices dos livros mais similares
    similar_indices = weighted_similarity.argsort()[-top_n:][::-1]
    return df.iloc[similar_indices]
