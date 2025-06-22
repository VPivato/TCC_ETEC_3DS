from flask import Blueprint, render_template
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlalchemy import inspect, extract

from ...models.notificacao import Notificacoes
from ...models.pedido import Pedido
from ...models.produto import Produtos
from ...models.item_pedido import ItemPedido
from ...models.usuario import Usuarios
from ...models.feedback import Feedbacks

from ...extensions import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def tempo_relativo(data):
    if not data:
        return "Nenhuma notificação"
    
    diferenca = datetime.now() - data
    dias = diferenca.days

    if dias == 0:
        return "Hoje"
    elif dias == 1:
        return "Ontem"
    elif dias < 7:
        return f"Há {dias} dias"
    elif dias < 30:
        semanas = dias // 7
        return f"Há {semanas} semana" + ("s" if semanas > 1 else "")
    else:
        meses = dias // 30
        return f"Há {meses} mês" + ("es" if meses > 1 else "")

@admin_bp.route('/')
def admin():
    # Notificações
    total_notificacoes = Notificacoes.query.count()
    ultima_notificacao = Notificacoes.query.order_by(Notificacoes.data_notificacao.desc()).first()
    ultima_notificacao_formatada = tempo_relativo(ultima_notificacao.data_notificacao) if ultima_notificacao else "Nenhuma notificação"
    ultimas_notificacoes = Notificacoes.query.order_by(Notificacoes.data_notificacao.desc()).limit(5).all()
    lista_notificacoes = [
        {
            'titulo': n.titulo_notificacao,
            'descricao': n.mensagem_notificacao,
            'tempo': tempo_relativo(n.data_notificacao)
        }
        for n in ultimas_notificacoes
    ]

    # Pedidos
    total_pedidos = Pedido.query.count()
    pedidos_finalizados = Pedido.query.filter_by(status='retirado').count()
    pedidos_pendentes = Pedido.query.filter_by(status='pendente').count()
    pedidos_cancelados = Pedido.query.filter_by(status='cancelado').count()

    valor_total_finalizados = db.session.query(
        func.sum(Pedido.total)
    ).filter_by(status='retirado').scalar() or 0

    taxa_cancelamento = round(
        (pedidos_cancelados / total_pedidos) * 100
    ) if total_pedidos > 0 else 0

    hoje = datetime.today()
    primeiro_dia_mes_atual = hoje.replace(day=1)

    # Primeiro dia do mês anterior
    primeiro_dia_mes_anterior = (primeiro_dia_mes_atual - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)

    # Pedidos no mês atual
    pedidos_mes_atual = Pedido.query.filter(
        Pedido.data_hora >= primeiro_dia_mes_atual,
        Pedido.data_hora < hoje  # ou até datetime.now()
    ).count()

    # Pedidos no mês anterior
    pedidos_mes_anterior = Pedido.query.filter(
        Pedido.data_hora >= primeiro_dia_mes_anterior,
        Pedido.data_hora <= ultimo_dia_mes_anterior
    ).count()

    # Cálculo da variação
    if pedidos_mes_anterior > 0:
        variacao_mensal = (
            (pedidos_mes_atual - pedidos_mes_anterior) / pedidos_mes_anterior
        ) * 100
    else:
        variacao_mensal = 0

    # Produtos
    total_produtos = Produtos.query.count()
    produtos_estoque_baixo = Produtos.query.filter(Produtos.estoque_produto <= 5).count()
    produtos_esgotados = Produtos.query.filter(Produtos.estoque_produto == 0).count()
    # Definir o primeiro dia do mês atual
    hoje = datetime.today()
    primeiro_dia_mes = hoje.replace(day=1)

    # Consulta
    mais_vendidos = db.session.query(
        Produtos.descricao_produto,
        func.sum(ItemPedido.quantidade).label('total_vendido')
    ).join(ItemPedido, ItemPedido.produto_id == Produtos.id) \
    .join(Pedido, ItemPedido.pedido_id == Pedido.id) \
    .filter(
        Pedido.status == 'retirado',
        Pedido.data_hora >= primeiro_dia_mes
    ) \
    .group_by(Produtos.id) \
    .order_by(func.sum(ItemPedido.quantidade).desc()) \
    .limit(3) \
    .all()

    # Produtos com menor estoque
    produtos_baixo_estoque = db.session.query(
        Produtos.descricao_produto,
        Produtos.estoque_produto
    ).order_by(Produtos.estoque_produto.asc()) \
    .limit(5).all()

    # Separar em listas para passar ao template
    labels_produtos = [p.descricao_produto for p in produtos_baixo_estoque]
    values_produtos = [p.estoque_produto for p in produtos_baixo_estoque]

    # Usuários
    total_usuarios = Usuarios.query.count()

    # Feedback
    total_feedbacks = Feedbacks.query.count()

    distribuicao_feedback = {
        'duvida': round(Feedbacks.query.filter_by(tipo_feedback='duvida').count() / Feedbacks.query.count() * 100) if Feedbacks.query.count() > 0 else 0,
        'reclamacao': round(Feedbacks.query.filter_by(tipo_feedback='reclamacao').count() / Feedbacks.query.count() * 100) if Feedbacks.query.count() > 0 else 0,
        'sugestao': round(Feedbacks.query.filter_by(tipo_feedback='sugestao').count() / Feedbacks.query.count() * 100) if Feedbacks.query.count() > 0 else 0,
        'elogio': round(Feedbacks.query.filter_by(tipo_feedback='elogio').count() / Feedbacks.query.count() * 100) if Feedbacks.query.count() > 0 else 0,
    }

    # Número de tabelas
    inspetor = inspect(db.engine)
    numero_tabelas = len(inspetor.get_table_names())

    # Dados dos gráficos
    hoje = datetime.today()
    semanas = []
    pedidos_por_semana = []

    for i in range(4):
        inicio = hoje - timedelta(weeks=i + 1)
        fim = hoje - timedelta(weeks=i)
        count = Pedido.query.filter(Pedido.data_hora >= inicio, Pedido.data_hora < fim).count()
        semanas.append(f"Semana {4 - i}")
        pedidos_por_semana.append(count)

    semanas.reverse()
    pedidos_por_semana.reverse()

    # Obter ano atual
    ano_atual = datetime.now().year

    # Lista dos meses
    meses_labels = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    # Lista de novos usuários por mês
    usuarios_por_mes = []

    for mes in range(1, 13):
        count = db.session.query(func.count()).filter(
            extract('year', Usuarios.data_criacao_usuario) == ano_atual,
            extract('month', Usuarios.data_criacao_usuario) == mes
        ).scalar()
        usuarios_por_mes.append(count)

    # Obter o mês atual
    mes_atual = datetime.now().month

    # Cortar os meses futuros
    meses_labels_atuais = meses_labels[:mes_atual]
    usuarios_por_mes_atuais = usuarios_por_mes[:mes_atual]

    # Renderizar template com dados
    return render_template(
        'admin/admin/admin.html',
        total_notificacoes=total_notificacoes,
        ultima_notificacao_formatada=ultima_notificacao_formatada,
        lista_notificacoes=lista_notificacoes,

        total_pedidos=total_pedidos,
        pedidos_finalizados=pedidos_finalizados,
        pedidos_pendentes=pedidos_pendentes,
        pedidos_cancelados=pedidos_cancelados,
        valor_total_finalizados=valor_total_finalizados,
        taxa_cancelamento=taxa_cancelamento,
        variacao_mensal=variacao_mensal,

        total_produtos=total_produtos,
        produtos_estoque_baixo=produtos_estoque_baixo,
        produtos_esgotados=produtos_esgotados,
        mais_vendidos=mais_vendidos,
        labels_produtos=labels_produtos,
        values_produtos=values_produtos,

        total_usuarios=total_usuarios,
        total_feedbacks=total_feedbacks,
        distribuicao_feedback=distribuicao_feedback,
        numero_tabelas=numero_tabelas,
        meses_labels_atuais=meses_labels_atuais,
        usuarios_por_mes_atuais=usuarios_por_mes_atuais,

        semanas=semanas,
        pedidos_por_semana=pedidos_por_semana
    )