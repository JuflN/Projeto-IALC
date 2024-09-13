from flask import Flask
from routes.chat import chat_bp
from routes.credits import credits_bp
from routes.wordcloud import wordcloud_bp
from routes.histograma import histograma_bp
from routes.recommendations import recommendations_bp
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Registro de Blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(credits_bp)
app.register_blueprint(wordcloud_bp)
app.register_blueprint(histograma_bp)
app.register_blueprint(recommendations_bp)

if __name__ == "__main__":
    app.run()
