from flask import Blueprint, render_template, request
from datetime import datetime, timedelta
from collections import defaultdict

from ...models.pedido import Pedido
from ...models.produto import Produtos
from ...models.item_pedido import ItemPedido
from ...models.usuario import Usuarios
from ...models.feedback import Feedbacks
from ...extensions import db

relatorio_bp = Blueprint("relatorio", __name__, url_prefix="/relatorio")

@relatorio_bp.route('/')
def relatorio():
    periodo = request.args.get("periodo", "ultima_semana")  # valor padrão
    periodo_formatado = ''
    data_inicio = None
    data_fim = datetime.now()

    # Definindo intervalo conforme seleção do filtro
    if periodo == "ultima_semana":
        data_inicio = datetime.now() - timedelta(days=7)
        periodo_formatado = 'Nos últimos 7 dias'
    elif periodo == "ultimo_mes":
        data_inicio = datetime.now() - timedelta(days=30)
        periodo_formatado = 'No últimos 30 dias'
    elif periodo == "comeco_ano":
        data_inicio = datetime(datetime.now().year, 1, 1)
        periodo_formatado = 'Desde o começo do ano'
    elif periodo == "personalizado":
        try:
            data_inicio_str = request.args.get("dataInicio")
            data_fim_str = request.args.get("dataFim")
            
            if data_inicio_str:
                data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            if data_fim_str:
                data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            periodo_formatado = f'Nos últimos {(data_fim-data_inicio).days} dias'
        except ValueError:
            pass
    
    dados_geral = gerar_relatorio_geral(data_inicio, data_fim)

    return render_template('admin/relatorio/relatorio.html', 
                           periodo=periodo,
                           periodo_formatado=periodo_formatado,
                           data_inicio=data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
                           data_fim=data_fim.strftime("%Y-%m-%d") if data_fim else "",

                           geral=dados_geral
                           )



def gerar_relatorio_geral(data_inicio, data_fim):
    # Query base com filtro aplicado
    pedidos_query = db.session.query(Pedido)
    if data_inicio:
        pedidos_query = pedidos_query.filter(Pedido.data_hora >= data_inicio)
    if data_fim:
        pedidos_query = pedidos_query.filter(Pedido.data_hora <= data_fim)
    
    pedidos_filtrados = pedidos_query.all()

    # KPIs
    vendas_totais = sum(p.total for p in pedidos_filtrados if p.status == "retirado")
    total_pedidos = len(pedidos_filtrados)
    clientes_atendidos = sum(1 for p in pedidos_filtrados if p.status == "retirado")
    ticket_medio = vendas_totais / clientes_atendidos if clientes_atendidos > 0 else 0

    kpis_geral = {
        "vendas_totais": vendas_totais,
        "total_pedidos": total_pedidos,
        "clientes_atendidos": clientes_atendidos,
        "venda_media": ticket_medio
    }

    # Vendas por dia
    vendas_por_dia = defaultdict(float)
    for pedido in pedidos_filtrados:
        if pedido.status == "retirado":
            dia = pedido.data_hora.date()
            vendas_por_dia[dia] += pedido.total
    vendas_por_dia = dict(sorted(vendas_por_dia.items()))
    labels_vendas_dia = [d.strftime("%d/%m") for d in vendas_por_dia.keys()]
    valores_vendas_dia = list(vendas_por_dia.values())

    # Vendas por produto (top 5)
    vendas_por_produto = defaultdict(float)
    for pedido in pedidos_filtrados:
        if pedido.status == "retirado":
            for item in pedido.itens:
                vendas_por_produto[item.produto.descricao_produto] += item.quantidade
    produtos_ordenados = sorted(vendas_por_produto.items(), key=lambda x: x[1], reverse=True)
    labels_produtos = [p[0] for p in produtos_ordenados[:5]]
    valores_produtos = [p[1] for p in produtos_ordenados[:5]]

    return {
        "kpis": kpis_geral,
        "grafico_vendas_dia": {
            "labels": labels_vendas_dia,
            "valores": valores_vendas_dia
        },
        "grafico_produtos": {
            "labels": labels_produtos,
            "valores": valores_produtos
        }
    }