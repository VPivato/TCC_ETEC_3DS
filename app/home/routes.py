from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__, url_prefix="/home")

# Rota Home, depois de entrar ou registrar com sucesso
@home_bp.route('/home')
def home():
    return render_template("home/home.html")