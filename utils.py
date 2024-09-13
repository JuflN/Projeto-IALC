import pandas as pd
import nltk
from nltk.corpus import stopwords as nltk_stopwords
from wordcloud import WordCloud
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import matplotlib.pyplot as plt

# Carregar as stopwords do português
stop_words_portuguese = nltk_stopwords.words('portuguese')

# Função para normalizar texto (remover acentos e caracteres especiais)
def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

# Função para preprocessar descrições de livros
def preprocess(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalnum()]
    return ' '.join(tokens)

# Função para carregar e preprocessar o DataFrame
def process_dataframe():
    df = pd.read_csv("C:/Users/Jufln/Desktop/projeto/Projeto-IALC/dados.csv", encoding='UTF-8', sep=',')
    df['titulo'] = df['titulo'].fillna('').astype(str)
    df['normalized_title'] = df['titulo'].apply(normalize_text)
    df['descricao'] = df['descricao'].astype(str).fillna('')
    df['autor'] = df['autor'].astype(str).fillna('')
    df['cleaned_description'] = df['descricao'].apply(preprocess)
    return df

# Função para calcular a similaridade entre descrições de livros
def calcular_similaridade(livro_base_descricao, livro_base_autor=None, preferencia_autor=False):
    df = process_dataframe()
    if livro_base_descricao is None or livro_base_descricao.strip() == "":
        raise ValueError("A descrição do livro base não pode ser None ou vazia.")

    descricoes = df['cleaned_description'].tolist()
    vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
    tfidf_matrix = vectorizer.fit_transform(descricoes + [livro_base_descricao])
    similaridade = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

    if preferencia_autor and livro_base_autor:
        mesmo_autor = df['autor'] == livro_base_autor
        similaridade += np.where(mesmo_autor, 0.2, 0)

    return similaridade

# Função para encontrar os livros mais similares
def find_similar_books(livro_base, existe, same_author=False, descricao=None):
    df = process_dataframe()

    if existe == 1:
        livro_base_info = df[df['normalized_title'] == livro_base].iloc[0]
        livro_base_descricao = livro_base_info['cleaned_description']
        livro_base_autor = livro_base_info['autor']
    else:
        if descricao is None:
            raise ValueError("A descrição é necessária quando o livro não existe no DataFrame.")
        livro_base_descricao = descricao
        livro_base_autor = None

    similaridade = calcular_similaridade(
        livro_base_descricao=livro_base_descricao,
        livro_base_autor=livro_base_autor,
        preferencia_autor=same_author
    )

    top_indices = np.argsort(similaridade)[::-1][:10]
    livros_similares = df.iloc[top_indices]
    livros_similares['similaridade'] = similaridade[top_indices]

    return livros_similares

# Função para gerar o histograma de similaridade
def gerar_histograma(livros_similares, livro_base):
    titles = livros_similares['titulo'].tolist()
    similarities = livros_similares['similaridade'].tolist()

    plt.figure(figsize=(10, 6))
    plt.barh(titles, similarities, color='skyblue')
    plt.xlabel("Similaridade")
    plt.ylabel("Livros")
    plt.title(f"Livros similares a '{livro_base}'")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    hist_dir = r"C:\Users\Jufln\Desktop\projeto\Projeto-IALC\static"
    os.makedirs(hist_dir, exist_ok=True)
    hist_path = os.path.join(hist_dir, "histograma.png")
    plt.savefig(hist_path)
    plt.close()

    return hist_path

# Função para gerar o WordCloud
def generate_wordcloud(cleaned_description, font_path, stop_words, output_path):
    """
    Gera um WordCloud a partir da descrição do livro.

    Parâmetros:
    - cleaned_description: Descrição do livro já processada.
    - font_path: Caminho para a fonte a ser utilizada.
    - stop_words: Lista de palavras a serem ignoradas no WordCloud.
    - output_path: Caminho de saída para salvar a imagem do WordCloud.

    Retorno:
    - O caminho do arquivo gerado.
    """
    wordcloud = WordCloud(stopwords=stop_words, background_color="white", font_path=font_path).generate(cleaned_description)
    wordcloud.to_file(output_path)  # Salva o arquivo da wordcloud no caminho especificado
    return output_path
