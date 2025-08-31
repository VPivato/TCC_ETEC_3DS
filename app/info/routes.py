from flask import Blueprint, render_template

info_bp = Blueprint('info', __name__, url_prefix='/info')

@info_bp.route('/sobre')
def sobre():
    return render_template('info/sobre.html')

@info_bp.route('/politica')
def politica():
    return render_template('info/politica.html')

@info_bp.route('/termos')
def termos():
    return render_template('info/termos.html')