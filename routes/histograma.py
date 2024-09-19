from flask import Blueprint, render_template, request, url_for, session
from utils import gerar_histograma, stop_words_portuguese
import time
import os
import json

histograma_bp = Blueprint('histograma_bp', __name__)

@histograma_bp.route("/histograma")
def histograma():
    descricao_base = request.args.get('descricao', '')
    top_books_str = request.args.get('top_books', '')

    # Converter a string de descrições dos top_books para uma lista
    top_books = json.loads(top_books_str)

    # Definir o caminho para salvar o histograma
    output_path = r'/home/jufln/Projeto-IALC/static/histograma.png'

    # Verificar se o diretório existe e criar, se necessário
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    # Gerar histograma comparando a descrição base com a descrição dos livros mais similares
    gerar_histograma(cleaned_description=descricao_base, stop_words=stop_words_portuguese, top_books=top_books, output_path=output_path)

    # Adicionar um timestamp para evitar cache do navegador
    timestamp = int(time.time())
    hist_url = url_for('static', filename='histograma.png') + f"?t={timestamp}"

    return render_template("histograma.html", hist_url=hist_url, show_logo=True, show_credits=True)

