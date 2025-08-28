from flask import Blueprint, render_template, redirect, url_for, request
from datetime import datetime

from ...models.produto import Produtos
from ...models.pedido import Pedido
from ...models.usuario import Usuarios
from ...extensions import db

from utils.decorators import admin_required

pedido_bp = Blueprint('pedido', __name__, url_prefix='/pedido')

@pedido_bp.route('/')
@admin_required
def visualizar_pedidos():
    ordenar = request.args.get('ordenar', 'desc')  # padrão decrescente

    # Filtro de status
    filtro_status = request.args.get('status', 'pendente')

    # Query inicial
    query = Pedido.query

    if filtro_status != 'todos':
        query = query.filter_by(status=filtro_status)

    # Ordenação
    if ordenar == 'asc':
        query = query.order_by(Pedido.data_hora.asc())
    else:
        query = query.order_by(Pedido.data_hora.desc())

    # Busca
    campo_busca = request.args.get('campo')
    termo_busca = request.args.get('busca')

    if campo_busca and termo_busca:
        if campo_busca == 'id_pedido':
            query = query.filter(Pedido.id == termo_busca)
        elif campo_busca == 'id_usuario':
            query = query.filter(Pedido.id_usuario == termo_busca)
        elif campo_busca == 'rm':
            query = query.join(Usuarios).filter(Usuarios.rm_usuario.ilike(f'%{termo_busca}%'))
        elif campo_busca == 'codigo_etec':
            query = query.join(Usuarios).filter(Usuarios.codigo_etec_usuario.ilike(f'%{termo_busca}%'))

    # Resultado final
    pedidos = query.all()

    return render_template('admin/pedido/pedido.html', pedidos=pedidos, filtro_status=filtro_status, ordenar=ordenar, campo_busca=campo_busca, termo_busca=termo_busca)



@pedido_bp.route('/finalizar/<int:pedido_id>', methods=['POST', 'GET'])
@admin_required
def finalizar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.status != 'pendente':
        return redirect(url_for('pedido.visualizar_pedidos'))
    
    try:
        pedido.status = 'retirado'
        pedido.data_retirada = datetime.now()
        db.session.commit()
        return redirect(url_for('pedido.visualizar_pedidos', toast=f'Pedido #{pedido.id} marcado como retirado!'))
    except Exception as e:
        db.session.rollback()
        return f"ERROR:: {e}"



@pedido_bp.route('/cancelar/<int:pedido_id>', methods=['POST', 'GET'])
@admin_required
def cancelar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    # só permite cancelar pedidos pendentes
    if pedido.status != 'pendente':
        return redirect(url_for('pedido.visualizar_pedidos'))

    try:
        # devolve o estoque de cada produto comprado
        for item in pedido.itens:
            produto = Produtos.query.get(item.produto_id)
            if produto:  # só por segurança
                produto.estoque_produto += item.quantidade

        # atualiza status do pedido
        pedido.status = 'cancelado'
        pedido.data_cancelamento = datetime.now()

        db.session.commit()
        return redirect(url_for(
            'pedido.visualizar_pedidos',
            toast=f'Pedido #{pedido.id} foi cancelado com sucesso!'
        ))
    except Exception as e:
        db.session.rollback()
        return f"ERROR:: {e}"
