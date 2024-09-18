# app.py
from flask import Flask
from cache_config import cache, init_cache
import config

# Criação da instância do aplicativo Flask
app = Flask(__name__)

# Carregar configurações
app.config.from_object(config.Config)

# Inicializar o cache
init_cache(app)

# Importar e registrar blueprints depois da configuração completa
from routes.chat import chat_bp
from routes.credits import credits_bp
from routes.wordcloud import wordcloud_bp
from routes.histograma import histograma_bp
from routes.recommendations import recommendations_bp

# Registro de Blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(credits_bp)
app.register_blueprint(wordcloud_bp)
app.register_blueprint(histograma_bp)
app.register_blueprint(recommendations_bp)

if __name__ == "__main__":
    app.run()
