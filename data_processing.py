import pandas as pd
import nltk
from nltk.corpus import stopwords as nltk_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
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
    df = pd.read_csv("/home/jufln/Projeto-IALC/dados.csv", encoding='utf-8', sep = ',')
    df['normalized_title'] = df['titulo'].apply(normalize_text)
    df['descricao'] = df['descricao'].astype(str).fillna('')
    df['cleaned_description'] = df['descricao'].apply(preprocess)
    return df

# Função para encontrar livros semelhantes usando TF-IDF
def find_similar_books(df, description, top_n=5):
    vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
    tfidf_matrix = vectorizer.fit_transform(df['cleaned_description'])
    query_tfidf = vectorizer.transform([preprocess(description)])
    cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    similar_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return df.iloc[similar_indices]
