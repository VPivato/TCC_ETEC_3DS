# app/utils/relatorio_utils.py
from datetime import datetime, timedelta
from io import BytesIO
import re

from sqlalchemy import func
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from app.extensions import db
from app.models import Pedido, ItemPedido, Produtos, Usuarios


def filtrar_pedidos(data_inicio, data_fim):
    pedidos_query = Pedido.query
    if data_inicio:
        pedidos_query = pedidos_query.filter(Pedido.data_hora >= data_inicio)
    if data_fim:
        pedidos_query = pedidos_query.filter(Pedido.data_hora <= data_fim)
    return pedidos_query.all()


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
