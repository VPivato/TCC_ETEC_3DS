from flask import Blueprint, render_template, request, session, jsonify
from ..models.usuario import Usuarios
from ..models.produto import Produtos
from ..models.pedido import Pedido
from ..models.item_pedido import ItemPedido
from ..extensions import db

loja_bp = Blueprint("loja", __name__, url_prefix="/loja")

@loja_bp.route('/')
def loja():
    salgados = Produtos.query.filter_by(categoria_produto="SALGADO").all()
    doces = Produtos.query.filter_by(categoria_produto="DOCE").all()
    bebidas = Produtos.query.filter_by(categoria_produto="BEBIDA").all()
    return render_template("loja/loja.html", salgados=salgados, doces=doces, bebidas=bebidas)

@loja_bp.route('/finalizar-compra', methods=['POST'])
def finalizar_compra():
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({'erro': 'JSON inválido ou header Content-Type não é application/json'}), 400

    carrinho = dados.get('carrinho')
    if not isinstance(carrinho, dict) or not carrinho:
        return jsonify({'erro': 'Carrinho vazio ou formato incorreto'}), 400

    usuario = Usuarios.query.filter_by(email_usuario=session.get('email')).first()
    if not usuario:
        return jsonify({'erro': 'Usuário não autenticado'}), 403

    total = 0
    pedido = Pedido(total=0, id_usuario=usuario.id)
    db.session.add(pedido)

    for id_str, item in carrinho.items():
        produto = Produtos.query.get(int(id_str))
        if not produto:
            return jsonify({'erro': f'Produto ID {id_str} não encontrado'}), 404

        qt = item.get('quantidade', 0)
        if produto.estoque_produto < qt:
            return jsonify({'erro': f'Estoque insuficiente para {produto.descricao_produto}'}), 400

        total += produto.preco_produto * qt

        db.session.add(ItemPedido(
            pedido=pedido,
            produto_id=produto.id,
            quantidade=qt,
            preco_unitario=produto.preco_produto
        ))
        produto.estoque_produto -= qt

    pedido.total = total
    db.session.commit()

    return jsonify({'mensagem': 'Compra registrada com sucesso!', 'pedido_id': pedido.id}), 200