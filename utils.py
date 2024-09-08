import pandas as pd
import nltk
from nltk.corpus import stopwords as nltk_stopwords
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud

nltk.download('punkt')
stop_words_portuguese = nltk_stopwords.words('portuguese')

# Normalização de texto
def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

# Preprocessamento de descrições
def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalnum()]
    return ' '.join(tokens)

# Carregamento e processamento do DataFrame
def process_dataframe():
    df = pd.read_csv("/home/jufln/Projeto-IALC/dados.csv", encoding='UTF-8', sep=';')
    df['titulo'] = df['titulo'].fillna('').astype(str)
    df['normalized_title'] = df['titulo'].apply(normalize_text)
    df['descricao'] = df['descricao'].astype(str).fillna('')
    df['autor'] = df['autor'].astype(str).fillna('')
    df['cleaned_description'] = df['descricao'].apply(preprocess)
    return df

# Encontrar livros similares
def find_similar_books(description, top_n=5):
    df = process_dataframe()
    vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
    tfidf_matrix = vectorizer.fit_transform(df['cleaned_description'])
    query_tfidf = vectorizer.transform([preprocess(description)])
    cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    similar_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return df.iloc[similar_indices]

# Função para gerar o WordCloud
def generate_wordcloud(cleaned_description, font_path, stop_words, output_path):
    wordcloud = WordCloud(stopwords=stop_words, background_color="white", font_path=font_path).generate(cleaned_description)
    wordcloud.to_file(output_path)  # Salva o arquivo da wordcloud no caminho especificado
    return output_path