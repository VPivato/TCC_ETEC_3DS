from flask import Blueprint, render_template, url_for

sobre_bp = Blueprint('sobre', __name__, url_prefix='/sobre')

@sobre_bp.route('/')
def sobre():
    return render_template('sobre/sobre.html')