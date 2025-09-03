from flask import Blueprint, render_template, redirect, url_for, request
from datetime import datetime
from sqlalchemy.orm import joinedload

from ...models.produto import Produtos
from ...models.pedido import Pedido
from ...models.usuario import Usuarios
from ...models.item_pedido import ItemPedido
from ...extensions import db

from utils.decorators import admin_required

pedido_bp = Blueprint('pedido', __name__, url_prefix='/pedido')

@pedido_bp.route('/')
@admin_required
def visualizar_pedidos():
    ordenar = request.args.get('ordenar', 'desc')
    filtro_status = request.args.get('status', 'pendente')
    campo_busca = request.args.get('campo')
    termo_busca = request.args.get('busca')

    # --- Datas (strings no formato YYYY-MM-DD vindas dos inputs type=date) ---
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    data_inicio = data_fim = None

    try:
        if data_inicio_str:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
    except ValueError:
        data_inicio = None

    try:
        if data_fim_str:
            # incluir o dia inteiro: 23:59:59
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        data_fim = None

    # --- Query base com joinedload para evitar N+1 ao acessar usuario/itens/produto ---
    query = Pedido.query.options(
        joinedload(Pedido.usuario),
        joinedload(Pedido.itens).joinedload(ItemPedido.produto)
    )

    # status
    if filtro_status != 'todos':
        query = query.filter(Pedido.status == filtro_status)

    # aplicar filtro de datas NO BANCO (muito mais rápido que carregar tudo e filtrar em Python)
    if data_inicio and data_fim:
        query = query.filter(Pedido.data_hora.between(data_inicio, data_fim))
    elif data_inicio:
        query = query.filter(Pedido.data_hora >= data_inicio)
    elif data_fim:
        query = query.filter(Pedido.data_hora <= data_fim)

    # busca textual/lógica (mantém comportamento atual)
    if campo_busca and termo_busca:
        if campo_busca == 'id_pedido':
            query = query.filter(Pedido.id == termo_busca)
        elif campo_busca == 'id_usuario':
            query = query.filter(Pedido.id_usuario == termo_busca)
        elif campo_busca == 'rm':
            query = query.join(Usuarios).filter(Usuarios.rm_usuario.ilike(f'%{termo_busca}%'))
        elif campo_busca == 'codigo_etec':
            query = query.join(Usuarios).filter(Usuarios.codigo_etec_usuario.ilike(f'%{termo_busca}%'))

    # ordenação e paginação (mantém paginação)
    if ordenar == 'asc':
        query = query.order_by(Pedido.data_hora.asc())
    else:
        query = query.order_by(Pedido.data_hora.desc())

    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'admin/pedido/pedido.html',
        pedidos=pagination.items,
        pagination=pagination,
        filtro_status=filtro_status,
        ordenar=ordenar,
        campo_busca=campo_busca,
        termo_busca=termo_busca,
        # mantém valores de datas para o template (pré-preenchimento)
        data_inicio=data_inicio_str,
        data_fim=data_fim_str
    )



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
