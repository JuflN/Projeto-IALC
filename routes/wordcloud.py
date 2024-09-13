from flask import Blueprint, render_template
from utils import generate_wordcloud

wordcloud_bp = Blueprint('wordcloud_bp', __name__)

@wordcloud_bp.route("/wordcloud")
def wordcloud():
    return render_template("wordcloud.html", show_logo=True, show_credits=True)
