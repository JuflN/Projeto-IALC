from flask import Blueprint, render_template

credits_bp = Blueprint('credits_bp', __name__)

@credits_bp.route("/credits")
def credits():
    return render_template("credits.html", show_logo=False, show_credits=False)
