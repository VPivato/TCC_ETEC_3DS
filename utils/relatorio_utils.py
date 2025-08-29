from datetime import datetime, timedelta
from io import BytesIO
import re
import pandas as pd

from sqlalchemy import func
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from app.extensions import db
from app.models import Pedido, ItemPedido, Produtos, Usuarios, Feedbacks

def ajustar_periodo(periodo, data_inicio=None, data_fim=None):
    now = datetime.now()
    if periodo != "personalizado":
        if periodo == "hoje":
            data_inicio = now.replace(hour=0, minute=0, second=0)
            data_fim = now.replace(hour=23, minute=59, second=59)
            inicio_anterior = data_inicio - timedelta(days=1)
            fim_anterior = data_fim - timedelta(days=1)
        elif periodo == "ultima_semana":
            data_inicio = now - timedelta(days=7)
            data_fim = now
            inicio_anterior = data_inicio - timedelta(days=7)
            fim_anterior = data_inicio - timedelta(seconds=1)
        elif periodo == "ultimo_mes":
            data_inicio = now - timedelta(days=30)
            data_fim = now
            inicio_anterior = data_inicio - timedelta(days=30)
            fim_anterior = data_inicio - timedelta(seconds=1)
        elif periodo == "comeco_ano":
            data_inicio = datetime(now.year, 1, 1)
            data_fim = now
            inicio_anterior = datetime(now.year - 1, 1, 1)
            fim_anterior = datetime(now.year - 1, 12, 31)
    else:
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        inicio_anterior = fim_anterior = None
    return data_inicio, data_fim, inicio_anterior, fim_anterior


def filtrar_pedidos(data_inicio, data_fim, status=None):
    pedidos_query = Pedido.query
    if data_inicio:
        pedidos_query = pedidos_query.filter(Pedido.data_hora >= data_inicio)
    if data_fim:
        pedidos_query = pedidos_query.filter(Pedido.data_hora <= data_fim)
    if status:
        pedidos_query = pedidos_query.filter(Pedido.status == status)
    return pedidos_query.all()


def filtrar_feedbacks(data_inicio=None, data_fim=None):
    query = db.session.query(Feedbacks)
    if data_inicio:
        query = query.filter(Feedbacks.data_feedback >= data_inicio)
    if data_fim:
        query = query.filter(Feedbacks.data_feedback <= data_fim)
    return query.all()


def calcular_kpis_geral(pedidos):
    pedidos_retirados = [p for p in pedidos if p.status == "retirado"]

    vendas_totais = sum(p.total for p in pedidos_retirados)
    total_pedidos = len(pedidos)
    clientes_atendidos = len(pedidos_retirados)
    ticket_medio = vendas_totais / clientes_atendidos if clientes_atendidos else 0

    return {
        "vendas_totais": vendas_totais,
        "total_pedidos": total_pedidos,
        "clientes_atendidos": clientes_atendidos,
        "venda_media": ticket_medio
    }


def calcular_kpis_produtos():
    total_produtos = db.session.query(func.count(Produtos.id)).scalar()
    produtos_esgotados = db.session.query(func.count(Produtos.id)).filter(Produtos.estoque_produto == 0).scalar()
    estoque_total = db.session.query(func.sum(Produtos.estoque_produto)).scalar() or 0
    produtos_estoque_baixo = Produtos.query.filter(Produtos.estoque_produto > 0, Produtos.estoque_produto <= 5).all()

    return {
        "total_produtos": total_produtos,
        "produtos_esgotados": produtos_esgotados,
        "produtos_estoque_baixo": len(produtos_estoque_baixo),
        "lista_produtos_estoque_baixo": produtos_estoque_baixo,
        "estoque_total": estoque_total
    }


def calcular_kpis_clientes(data_inicio, data_fim):
    total_clientes = Usuarios.query.count()
    novos_clientes = novos_clientes_no_periodo(data_inicio, data_fim)
    ativos, inativos = contar_clientes_ativos_inativos()

    return {
        "total_clientes": total_clientes,
        "novos_clientes": novos_clientes,
        "clientes_ativos": ativos,
        "clientes_inativos": inativos
    }


def calcular_kpis_pedidos(pedidos):
    pedidos_retirados = [p for p in pedidos if p.status == "retirado"]
    pedidos_cancelados = [p for p in pedidos if p.status == "cancelado"]

    faturamento = sum(p.total for p in pedidos_retirados)
    total_pedidos = len(pedidos)
    total_retirados = len(pedidos_retirados)
    total_cancelados = len(pedidos_cancelados)

    taxa_cancelamento = round((total_cancelados / total_pedidos) * 100, 1) if total_pedidos else 0
    valor_medio = round(faturamento / total_retirados, 2) if total_retirados else 0

    return {
        "faturamento": faturamento,
        "total_pedidos": total_pedidos,
        "taxa_cancelamento": taxa_cancelamento,
        "valor_medio_pedido": valor_medio
    }


def calcular_kpis_feedbacks(feedbacks):
    total = len(feedbacks)
    tipos = ["duvida", "reclamacao", "sugestao", "elogio"]

    contagem = {t: 0 for t in tipos}
    for f in feedbacks:
        if f.tipo_feedback in contagem:
            contagem[f.tipo_feedback] += 1

    return {
        "total_feedbacks": total,
        "duvidas": contagem["duvida"],
        "reclamacoes": contagem["reclamacao"],
        "sugestoes": contagem["sugestao"],
        "elogios": contagem["elogio"]
    }


def vendas_por_produto(pedidos, top_x):
    vendas = defaultdict(float)
    for pedido in pedidos:
        if pedido.status == "retirado":
            for item in pedido.itens:
                vendas[item.produto.descricao_produto] += item.quantidade
    ordenado = sorted(vendas.items(), key=lambda x: x[1], reverse=True)
    # Retorna labels, valores
    return [p[0] for p in ordenado[:top_x]], [p[1] for p in ordenado[:top_x]]


def analisar_movimento_diario(pedidos):
    pedidos_por_dia = {}
    for p in pedidos:
        dia = p.data_hora.strftime("%d/%m")
        pedidos_por_dia[dia] = pedidos_por_dia.get(dia, 0) + 1

    if not pedidos_por_dia:
        return "--", 0, "--", 0

    dia_pico = max(pedidos_por_dia, key=pedidos_por_dia.get)
    dia_menor = min(pedidos_por_dia, key=pedidos_por_dia.get)
    return dia_pico, pedidos_por_dia[dia_pico], dia_menor, pedidos_por_dia[dia_menor]


def analisar_faturamento_diario(pedidos):
    faturamento_por_dia = {}
    for p in pedidos:
        if p.status != "retirado":
            continue
        dia = p.data_hora.strftime("%d/%m")
        valor_pedido = sum(item.quantidade * item.preco_unitario for item in p.itens)
        faturamento_por_dia[dia] = faturamento_por_dia.get(dia, 0) + valor_pedido

    dia_pico_fat = dia_menor_fat = "--"
    pico_fat_valor = menor_fat_valor = 0

    if faturamento_por_dia:
        dia_pico_fat = max(faturamento_por_dia, key=faturamento_por_dia.get)
        pico_fat_valor = faturamento_por_dia[dia_pico_fat]
        dia_menor_fat = min(faturamento_por_dia, key=faturamento_por_dia.get)
        menor_fat_valor = faturamento_por_dia[dia_menor_fat]
    
    return dia_pico_fat, pico_fat_valor, dia_menor_fat, menor_fat_valor


def analisar_produtos(pedidos):
    vendas = {}
    faturamento = {}

    for p in pedidos:
        if p.status != "retirado":
            continue
        for item in p.itens:
            vendas[item.produto.descricao_produto] = vendas.get(item.produto.descricao_produto, 0) + item.quantidade
            faturamento[item.produto.descricao_produto] = faturamento.get(item.produto.descricao_produto, 0) + item.quantidade * item.preco_unitario

    if not vendas:
        return {}, {}

    return vendas, faturamento


def analisar_categorias(faturamento_dict, produtos_ref):
    categorias = {"SALGADO": 0, "DOCE": 0, "BEBIDA": 0}
    for produto, valor in faturamento_dict.items():
        cat = produtos_ref[produto].categoria_produto
        if cat in categorias:
            categorias[cat] += valor
    return categorias


def info_mais_vendidos(vendas_dict, faturamento_dict):
    produto_mais_vendido = produto_mais_lucro = "--"
    percentual_vendas = percentual_lucro = 0

    if vendas_dict:
        produto_mais_vendido = max(vendas_dict, key=vendas_dict.get)
        percentual_vendas = round((vendas_dict[produto_mais_vendido] / sum(vendas_dict.values())) * 100, 1)
        produto_mais_lucro = max(faturamento_dict, key=faturamento_dict.get)
        percentual_lucro = round((faturamento_dict[produto_mais_lucro] / sum(faturamento_dict.values())) * 100, 1)
    
    return produto_mais_vendido, percentual_vendas, produto_mais_lucro, percentual_lucro


def info_menos_vendidos(vendas_dict, faturamento_dict):
    produto_menos_vendido = produto_menos_lucro = "--"
    percentual_vendas_min = percentual_lucro_min = 0
    
    if vendas_dict:
        produto_menos_vendido = min(vendas_dict, key=vendas_dict.get)
        percentual_vendas_min = round((vendas_dict[produto_menos_vendido] / sum(vendas_dict.values())) * 100, 1)
        produto_menos_lucro = min(faturamento_dict, key=faturamento_dict.get)
        percentual_lucro_min = round((faturamento_dict[produto_menos_lucro] / sum(faturamento_dict.values())) * 100, 1)

    return produto_menos_vendido, percentual_vendas_min, produto_menos_lucro, percentual_lucro_min


def buscar_produto(produto_busca):
    if produto_busca.isdigit(): # Se digito, busca com base no id
        return Produtos.query.get(int(produto_busca))
    # Se não, busca com base na descrição
    return Produtos.query.filter(
        Produtos.descricao_produto.ilike(f"%{produto_busca}%")
    ).first()


def analisar_vendas_produto(produto, data_inicio, data_fim):
    itens = (
        db.session.query(ItemPedido, Pedido.data_hora)
        .join(Pedido, Pedido.id == ItemPedido.pedido_id)
        .filter(
            Pedido.status == "retirado",
            Pedido.data_hora >= data_inicio,
            Pedido.data_hora <= data_fim,
            ItemPedido.produto_id == produto.id
        ).all()
    )

    total_vendas = sum(i.ItemPedido.quantidade for i in itens)
    total_faturamento = sum(i.ItemPedido.quantidade * i.ItemPedido.preco_unitario for i in itens)

    vendas_por_dia = {}
    for item, data in itens:
        dia = data.strftime("%d/%m")
        vendas_por_dia[dia] = vendas_por_dia.get(dia, 0) + (item.quantidade * item.preco_unitario)

    return total_vendas, total_faturamento, vendas_por_dia


def contar_clientes_ativos_inativos():
    ativos = db.session.query(func.count(Usuarios.id)).filter_by(conta_ativa="sim").scalar()
    inativos = db.session.query(func.count(Usuarios.id)).filter_by(conta_ativa="nao").scalar()
    return ativos, inativos


def novos_clientes_no_periodo(data_inicio, data_fim):
    return Usuarios.query.filter(
        Usuarios.data_criacao_usuario.between(data_inicio, data_fim)
    ).count()


def crescimento_clientes_por_dia(data_inicio, data_fim):
    resultados = (
        db.session.query(
            func.date(Usuarios.data_criacao_usuario).label("dia"),
            func.count(Usuarios.id)
        )
        .filter(Usuarios.data_criacao_usuario.between(data_inicio, data_fim))
        .group_by(func.date(Usuarios.data_criacao_usuario))
        .order_by("dia")
        .all()
    )

    crescimento = {datetime.strptime(r.dia, "%Y-%m-%d").strftime("%d/%m"): r[1] for r in resultados}
    return crescimento


def top_clientes_por_faturamento(data_inicio, data_fim, limite=3):
    resultados = (
        db.session.query(
            Pedido.id_usuario,
            func.count(Pedido.id).label("total_pedidos"),
            func.sum(ItemPedido.quantidade * ItemPedido.preco_unitario).label("faturamento_total")
        )
        .join(ItemPedido, ItemPedido.pedido_id == Pedido.id)
        .filter(
            Pedido.status == "retirado",
            Pedido.data_hora.between(data_inicio, data_fim),
            Pedido.id_usuario.isnot(None)
        )
        .group_by(Pedido.id_usuario)
        .order_by(func.sum(ItemPedido.quantidade * ItemPedido.preco_unitario).desc())
        .limit(limite)
        .all()
    )

    top_clientes = []
    for cid, total_pedidos, faturamento_total in resultados:
        cliente = Usuarios.query.get(cid)
        top_clientes.append({
            "nome": cliente.aluno.nome_aluno if cliente.nivel_conta == 0 else "--",
            "rm": cliente.rm_usuario,
            "codigo_etec": cliente.codigo_etec_usuario,
            "email": cliente.aluno.email_aluno if cliente.nivel_conta == 0 else "--",
            "total_pedidos": total_pedidos,
            "faturamento_total": float(faturamento_total or 0)
        })
    return top_clientes


def grafico_pedidos_por_status(pedidos):
    status_contagem = {"pendente": 0, "retirado": 0, "cancelado": 0}
    for p in pedidos:
        if p.status in status_contagem:
            status_contagem[p.status] += 1
    return {
        "labels": list(status_contagem.keys()),
        "valores": list(status_contagem.values())
    }


def grafico_faturamento_por_dia(pedidos):
    vendas_por_dia = defaultdict(float)
    for pedido in pedidos:
        if pedido.status == "retirado":
            dia = pedido.data_hora.date()
            vendas_por_dia[dia] += pedido.total

    vendas_por_dia = dict(sorted(vendas_por_dia.items()))
    return {
        "labels": [d.strftime("%d/%m") for d in vendas_por_dia.keys()],
        "valores": list(vendas_por_dia.values())
    }


def grafico_feedbacks_por_tipo(kpis):
    return {
        "labels": ["duvida", "reclamacao", "sugestao", "elogio"],
        "valores": [
            kpis["duvidas"],
            kpis["reclamacoes"],
            kpis["sugestoes"],
            kpis["elogios"]
        ]
    }


def grafico_feedbacks_por_dia(feedbacks):
    feedbacks_por_dia = defaultdict(int)
    for f in feedbacks:
        dia = f.data_feedback.date()
        feedbacks_por_dia[dia] += 1

    feedbacks_por_dia = dict(sorted(feedbacks_por_dia.items()))
    return {
        "labels": [d.strftime("%d/%m") for d in feedbacks_por_dia.keys()],
        "valores": list(feedbacks_por_dia.values())
    }

