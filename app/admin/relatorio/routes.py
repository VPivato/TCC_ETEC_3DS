from flask import Blueprint, render_template

from ...models.notificacao import Notificacoes
from ...models.pedido import Pedido
from ...models.produto import Produtos
from ...models.item_pedido import ItemPedido
from ...models.usuario import Usuarios
from ...models.feedback import Feedbacks

from ...extensions import db

relatorio_bp = Blueprint("relatorio", __name__, url_prefix="/relatorio")

@relatorio_bp.route('/')
def relatorio():
    return render_template('admin/relatorio/relatorio.html')