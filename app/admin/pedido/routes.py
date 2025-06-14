from flask import Blueprint, render_template, flash, redirect, url_for, request
from ...models import Pedido
from ...extensions import db

pedido_bp = Blueprint('pedido', __name__, url_prefix='/pedido')

@pedido_bp.route('/')
def visualizar_pedidos():
    filtro_status = request.args.get('status', 'pendente')  # padrão 'pendente'

    if filtro_status == 'todos':
        pedidos = Pedido.query.order_by(Pedido.data_hora.desc()).all()
    else:
        pedidos = Pedido.query.filter_by(status=filtro_status).order_by(Pedido.data_hora.desc()).all()
        
    return render_template('admin/pedido/pedido.html', pedidos=pedidos, filtro_status=filtro_status)



@pedido_bp.route('/finalizar/<int:pedido_id>', methods=['POST', 'GET'])
def finalizar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.status != 'pendente':
        return redirect(url_for('admin.visualizar_pedidos'))
    
    try:
        pedido.status = 'retirado'
        db.session.commit()
        return redirect(url_for('pedido.visualizar_pedidos', toast=f'Pedido #{pedido.id} marcado como retirado!'))
    except Exception as e:
        db.session.rollback()
        return f"ERROR:: {e}"



@pedido_bp.route('/cancelar/<int:pedido_id>', methods=['POST', 'GET'])
def cancelar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.status != 'pendente':
        return redirect(url_for('admin.visualizar_pedidos'))
    
    try:
        pedido.status = 'cancelado'
        db.session.commit()
        return redirect(url_for('pedido.visualizar_pedidos', toast=f'Pedido #{pedido.id} foi cancelado com sucesso!'))
    except Exception as e:
        db.session.rollback()
        return f"ERROR:: {e}"