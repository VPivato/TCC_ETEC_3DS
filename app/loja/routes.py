from flask import Blueprint, render_template
from ..models.produto import Produtos
from ..extensions import db

loja_bp = Blueprint("loja", __name__, url_prefix="/loja")

@loja_bp.route('/')
def loja():
    salgados = Produtos.query.filter_by(categoria_produto="SALGADO").all()
    return render_template("loja/loja.html", salgados=salgados)