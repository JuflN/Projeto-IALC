from flask import Blueprint, render_template

histograma_bp = Blueprint('histograma_bp', __name__)

@histograma_bp.route("/histograma")
def histograma():
    return render_template("histograma.html", show_logo=True, show_credits=True)