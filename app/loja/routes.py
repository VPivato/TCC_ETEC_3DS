from flask import Blueprint, render_template, request, session, jsonify, url_for
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

    # checar sessão / usuário
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'erro': 'Usuário não autenticado'}), 403

    usuario = Usuarios.query.get(user_id)
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 403

    total = 0.0
    pedido = Pedido(total=0.0, id_usuario=usuario.id)
    db.session.add(pedido)

    itens_resposta = []

    # percorre itens do carrinho
    for id_str, item in carrinho.items():
        try:
            produto_id = int(id_str)
        except ValueError:
            db.session.rollback()
            return jsonify({'erro': f'ID de produto inválido: {id_str}'}), 400

        produto = Produtos.query.get(produto_id)
        if not produto:
            db.session.rollback()
            return jsonify({'erro': f'Produto ID {id_str} não encontrado'}), 404

        qt = int(item.get('quantidade', 0))
        if qt <= 0:
            db.session.rollback()
            return jsonify({'erro': f'Quantidade inválida para {produto.descricao_produto}'}), 400

        if produto.estoque_produto < qt:
            db.session.rollback()
            return jsonify({'erro': f'Estoque insuficiente para {produto.descricao_produto}'}), 400

        preco_unit = float(produto.preco_produto)  # transforma Decimal -> float
        subtotal = preco_unit * qt
        total += subtotal

        ip = ItemPedido(
            pedido=pedido,
            produto_id=produto.id,
            quantidade=qt,
            preco_unitario=preco_unit
        )
        db.session.add(ip)

        # decrementa estoque
        produto.estoque_produto -= qt

        itens_resposta.append({
            'produto_id': produto.id,
            'descricao': produto.descricao_produto,
            'quantidade': qt,
            'preco_unitario': f"{preco_unit:.2f}",
            'subtotal': f"{subtotal:.2f}"
        })

    pedido.total = float(total)
    db.session.commit()

    comprovante_url = url_for('perfil.baixar_comprovante', pedido_id=pedido.id)  # rota abaixo

    resposta = {
        'mensagem': 'Compra registrada com sucesso!',
        'pedido': {
            'id': pedido.id,
            'total': f"{total:.2f}",
            'data_hora': pedido.data_hora.isoformat(),
            'itens': itens_resposta,
            'usuario': {
                'id': usuario.id,
                'nome': usuario.nome_usuario,
                'email': usuario.email_usuario
            }
        },
        'comprovante_url': comprovante_url
    }

    return jsonify(resposta), 200


@loja_bp.route('/comprovante/<int:pedido_id>')
def comprovante(pedido_id):
    # rota que renderiza um HTML imprimível (para abrir em nova aba e salvar como PDF)
    pedido = Pedido.query.get_or_404(pedido_id)
    usuario = pedido.usuario
    itens = []
    for ip in pedido.itens:
        produto = ip.produto
        itens.append({
            'descricao': produto.descricao_produto,
            'quantidade': ip.quantidade,
            'preco_unitario': f"{ip.preco_unitario:.2f}",
            'subtotal': f"{(ip.preco_unitario * ip.quantidade):.2f}"
        })

    return render_template('loja/comprovante.html', pedido=pedido, usuario=usuario, itens=itens)