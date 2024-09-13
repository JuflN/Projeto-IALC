from flask import Blueprint, render_template, request, url_for
from utils import gerar_histograma, process_dataframe, stop_words_portuguese
from flask import session
import time
import os

histograma_bp = Blueprint('histograma_bp', __name__)

@histograma_bp.route("/histograma")
def histograma():
    df = process_dataframe()
    descricao_base = session.get('descricao_base', None)
    if not descricao_base:
        return "Descrição base não foi encontrada."

    # Continue com sua lógica para gerar o histograma
    descricao_similar = df['cleaned_description']

    # Definir o caminho para salvar o histograma
    output_path = r'/home/jufln/Projeto-IALC/static/histograma.png'

    # Verificar se o diretório existe e criar, se necessário
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    # Gerar histograma comparando a descrição base com a descrição dos livros mais similares
    gerar_histograma(descricao_base, descricao_similar, stop_words=stop_words_portuguese, output_path=output_path)

    # Adicionar um timestamp para evitar cache do navegador
    timestamp = int(time.time())
    hist_url = url_for('static', filename='histograma.png') + f"?t={timestamp}"

    return render_template("histograma.html", hist_url=hist_url, show_logo=True, show_credits=True)
