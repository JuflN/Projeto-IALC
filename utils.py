import pandas as pd
from flask import session
import nltk
from nltk.corpus import stopwords as nltk_stopwords
from wordcloud import WordCloud
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import matplotlib.pyplot as plt
from collections import Counter

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
    # Carregar o DataFrame completo em uma variável temporária
    temp = pd.read_csv("/home/jufln/Projeto-IALC/dados.csv", encoding='UTF-8', sep=',')

    # Filtrar apenas as colunas que serão utilizadas
    columns_to_use = ['titulo', 'descricao', 'autor', 'genero']
    df = temp[columns_to_use]

    # Preencher valores nulos e normalizar a coluna 'titulo'
    df['titulo'] = df['titulo'].fillna('').astype(str)
    df['normalized_title'] = df['titulo'].apply(normalize_text)

    # Preencher valores nulos e limpar a coluna 'descricao'
    df['descricao'] = df['descricao'].astype(str).fillna('')
    df['cleaned_description'] = df['descricao'].apply(preprocess)

    # Preencher valores nulos na coluna 'autor'
    df['autor'] = df['autor'].astype(str).fillna('')

    # Normalizar a coluna 'genero' (sem modificar o conteúdo, apenas aplicando o normalizer)
    df['genero'] = df['genero'].fillna('').apply(normalize_text)

    return df


def find_similar_books(livro_base, existe, same_author=False, descricao=None):
    df = process_dataframe()  # Carregar o DataFrame

    if existe == 1:
        # Livro base existe no DataFrame
        livro_base_info = df[df['normalized_title'] == livro_base].iloc[0]
        livro_base_descricao = livro_base_info['cleaned_description']
        livro_base_genero = livro_base_info['genero']
        livro_base_autor = livro_base_info['autor']
    else:
        # Livro base não existe no DataFrame, usar as informações fornecidas
        if descricao is None:
            raise ValueError("Descrição é necessária quando o livro não existe no DataFrame.")
        livro_base_descricao = descricao
        livro_base_genero = session.get('genre', None)
        livro_base_autor = None

    # Filtra por autor, se necessário
    if same_author and livro_base_autor:
        df_filtered = df[df['autor'] == livro_base_autor]
        if df_filtered.empty or len(df_filtered) == 1:  # Caso tenha apenas um livro do autor
            return None  # Retorna None para indicar que não há livros suficientes
    else:
        df_filtered = df

    # Calcula a similaridade
    similaridade = calcular_similaridade(
        livro_base_descricao=livro_base_descricao,
        livro_base_genero=livro_base_genero,
        livro_base_autor=livro_base_autor,
        preferencia_autor=same_author
    )

    # Garante que os índices de similaridade estejam alinhados com o DataFrame filtrado
    num_livros_disponiveis = len(df_filtered)
    top_indices = np.argsort(similaridade)[::-1][:min(10, num_livros_disponiveis)]

    # Filtra os livros mais similares e adiciona a coluna de similaridade
    livros_similares = df_filtered.iloc[top_indices].copy()
    livros_similares['similaridade'] = similaridade[top_indices]  # Adiciona a coluna de similaridade com os índices corretos

    return livros_similares


def gerar_histograma(cleaned_description, cleaned_similar_description, stop_words, output_path):
    """
    Função para gerar um histograma de palavras comuns entre a descrição do livro fornecido e a descrição de um livro similar.

    Parâmetros:
    - cleaned_description: Descrição do livro fornecido pelo usuário, já processada.
    - cleaned_similar_description: Descrição do livro similar encontrado, já processada.
    - stop_words: Lista de palavras a serem ignoradas.
    - output_path: Caminho de saída para salvar o histograma.

    Retorno:
    - output_path: Caminho onde o histograma foi salvo.
    """

    # Verifique se o input é uma Series e pegue o primeiro valor se for o caso
    if isinstance(cleaned_description, pd.Series):
        cleaned_description = cleaned_description.iloc[0]
    if isinstance(cleaned_similar_description, pd.Series):
        cleaned_similar_description = cleaned_similar_description.iloc[0]

    # Tokenizar as descrições
    words_description = cleaned_description.split()
    words_similar_description = cleaned_similar_description.split()

    # Contar frequências
    freq_description = Counter(words_description)
    freq_similar_description = Counter(words_similar_description)

    # Encontrar palavras comuns
    common_words = set(freq_description.keys()).intersection(set(freq_similar_description.keys()))

    # Criar DataFrame com as palavras comuns e suas frequências
    data = {
        'Palavra': list(common_words),
        'Frequência no Livro Fornecido': [freq_description[word] for word in common_words],
        'Frequência no Livro Similar': [freq_similar_description[word] for word in common_words]
    }
    df_common_words = pd.DataFrame(data)

    # Gerar histograma
    df_common_words.plot(kind='bar', x='Palavra', figsize=(10, 6))
    plt.xlabel('Palavra')
    plt.ylabel('Frequência')
    plt.title('Frequência de Palavras Comuns')
    plt.tight_layout()

    # Salvar histograma no caminho especificado
    plt.savefig(output_path)
    plt.close()

    return output_path


# Função para gerar o WordCloud
def generate_wordcloud(cleaned_description, stop_words):
    """
    Gera um WordCloud a partir da descrição do livro.

    Parâmetros:
    - cleaned_description: Descrição do livro já processada.

    - stop_words: Lista de palavras a serem ignoradas no WordCloud.
    - output_path: Caminho de saída para salvar a imagem do WordCloud.

    Retorno:
    - O caminho do arquivo gerado.
    """
    font_path = r'/home/jufln/Projeto-IALC/static/fonts/Roboto-Regular.ttf'
    output_path = r'/home/jufln/Projeto-IALC/static/wordcloud.png'

    if os.path.exists(output_path):
        os.remove(output_path)

    wordcloud = WordCloud(stopwords=stop_words, background_color="white", font_path=font_path).generate(cleaned_description)
    wordcloud.to_file(output_path)  # Salva o arquivo da wordcloud no caminho especificado
    return output_path


def calcular_similaridade(livro_base_descricao, livro_base_genero=None, livro_base_autor=None, preferencia_autor=False):
    df = process_dataframe()  # Carregar o DataFrame

    if livro_base_descricao is None or livro_base_descricao.strip() == "":
        raise ValueError("A descrição do livro base não pode ser None ou vazia.")

    descricoes = df['cleaned_description'].tolist()

    # Vetorização com TF-IDF nas descrições limpas
    vectorizer = TfidfVectorizer(stop_words=stop_words_portuguese)
    tfidf_matrix = vectorizer.fit_transform(descricoes + [livro_base_descricao])  # Adiciona a descrição do livro base para a matriz TF-IDF

    # Calcula a similaridade de todos os livros com a descrição do livro base
    similaridade = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()  # Calcula com a última linha (livro base)

    # Se o usuário quer prioridade para o mesmo autor
    if preferencia_autor and livro_base_autor:
        mesmo_autor = df['autor'] == livro_base_autor
        similaridade += np.where(mesmo_autor, 0.2, 0)  # Aumenta a similaridade em 20% para o mesmo autor

    # Sempre adicionar peso de 10% para o mesmo gênero, se aplicável
    if livro_base_genero:
        mesmo_genero = df['genero'] == livro_base_genero
        similaridade += np.where(mesmo_genero, 0.1, 0)  # Aumenta a similaridade em 10% para o mesmo gênero

    return similaridade