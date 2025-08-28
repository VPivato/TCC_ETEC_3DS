from flask import Blueprint, render_template, request, jsonify, send_file, session
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # backend para geração de imagens sem interface gráfica
from io import BytesIO
import pandas as pd
import re

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

from ...models.pedido import Pedido
from ...models.produto import Produtos
from ...models.usuario import Usuarios
from ...models.feedback import Feedbacks
from ...extensions import db

from utils.decorators import admin_required

relatorio_bp = Blueprint("relatorio", __name__, url_prefix="/relatorio")

@relatorio_bp.route('/')
@admin_required
def relatorio():
    session.pop('produto_especifico', None)
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
        periodo_formatado = 'Nos últimos 30 dias'
    elif periodo == "comeco_ano":
        data_inicio = datetime(datetime.now().year, 1, 1)
        periodo_formatado = 'Desde o começo do ano'
    elif periodo == "hoje":
        data_inicio = datetime.now().replace(hour=0, minute=0, second=0)
        data_fim = datetime.now().replace(hour=23, minute=59, second=59)
        periodo_formatado = 'Apenas hoje'
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
    session['data_inicio'] = data_inicio
    session['data_fim'] = data_fim
    session['periodo_formatado'] = periodo_formatado
    
    dados_geral = gerar_relatorio_geral(data_inicio, data_fim)
    dados_produtos = gerar_relatorio_produtos(data_inicio, data_fim)
    dados_clientes = gerar_relatorio_clientes(data_inicio, data_fim)
    dados_pedidos = gerar_relatorio_pedidos(data_inicio, data_fim)
    dados_feedbacks = gerar_relatorio_feedbacks(data_inicio, data_fim)

    return render_template('admin/relatorio/relatorio.html', 
                           periodo=periodo,
                           periodo_formatado=periodo_formatado,
                           data_inicio=data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
                           data_fim=data_fim.strftime("%Y-%m-%d") if data_fim else "",

                           geral=dados_geral,
                           produto=dados_produtos,
                           clientes=dados_clientes,
                           pedidos=dados_pedidos,
                           feedbacks=dados_feedbacks
                           )

@relatorio_bp.route('/limpar_produto_especifico', methods=["POST"])
@admin_required
def limpar_produto_especifico():
    session.pop('produto_especifico', None)
    return jsonify({"status": "ok"})

@admin_required
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

    # Vendas por produto (top 5)
    vendas_por_produto = defaultdict(float)
    for pedido in pedidos_filtrados:
        if pedido.status == "retirado":
            for item in pedido.itens:
                vendas_por_produto[item.produto.descricao_produto] += item.quantidade
    produtos_ordenados = sorted(vendas_por_produto.items(), key=lambda x: x[1], reverse=True)
    labels_produtos = [p[0] for p in produtos_ordenados[:5]]
    valores_produtos = [p[1] for p in produtos_ordenados[:5]]

    # --- Frases destacadas ---

    # --- Pedidos do período atual ---
    pedidos = Pedido.query.filter(
        Pedido.data_hora >= data_inicio,
        Pedido.data_hora <= data_fim,
    ).all()

    # Pico e menor volume de pedidos
    pedidos_por_dia = {}
    for p in pedidos:
        dia = p.data_hora.strftime("%d/%m")
        pedidos_por_dia[dia] = pedidos_por_dia.get(dia, 0) + 1

    if pedidos_por_dia:
        dia_pico = max(pedidos_por_dia, key=pedidos_por_dia.get)
        pico_valor = pedidos_por_dia[dia_pico]
        dia_menor = min(pedidos_por_dia, key=pedidos_por_dia.get)
        menor_valor = pedidos_por_dia[dia_menor]
    else:
        dia_pico = dia_menor = "--"
        pico_valor = menor_valor = 0

    # Produto mais vendido e que mais contribui para faturamento
    vendas_produtos = {}
    faturamento_produtos = {}
    for p in pedidos:
        if p.status != "retirado":
            continue  # ignora pedidos pendentes ou cancelados
        for item in p.itens:
            vendas_produtos[item.produto.descricao_produto] = vendas_produtos.get(item.produto.descricao_produto, 0) + item.quantidade
            faturamento_produtos[item.produto.descricao_produto] = faturamento_produtos.get(item.produto.descricao_produto, 0) + item.quantidade * item.preco_unitario

    if vendas_produtos:
        # Mais vendidos e mais lucrativos
        produto_mais_vendido = max(vendas_produtos, key=vendas_produtos.get)
        percentual_vendas = round((vendas_produtos[produto_mais_vendido] / sum(vendas_produtos.values())) * 100, 1)
        produto_mais_lucro = max(faturamento_produtos, key=faturamento_produtos.get)
        percentual_lucro = round((faturamento_produtos[produto_mais_lucro] / sum(faturamento_produtos.values())) * 100, 1)

        # Menos vendidos e menos lucrativos
        produto_menos_vendido = min(vendas_produtos, key=vendas_produtos.get)
        percentual_vendas_min = round((vendas_produtos[produto_menos_vendido] / sum(vendas_produtos.values())) * 100, 1)
        produto_menos_lucro = min(faturamento_produtos, key=faturamento_produtos.get)
        percentual_lucro_min = round((faturamento_produtos[produto_menos_lucro] / sum(faturamento_produtos.values())) * 100, 1)
    else:
        produto_mais_vendido = produto_mais_lucro = "--"
        produto_menos_vendido = produto_menos_lucro = "--"
        percentual_vendas = percentual_lucro = 0
        percentual_vendas_min = percentual_lucro_min = 0
    
    # Pico e menor faturamento
    faturamento_por_dia = {}
    for p in pedidos:
        if p.status != "retirado":
            continue
        dia = p.data_hora.strftime("%d/%m")
        valor_pedido = sum(item.quantidade * item.preco_unitario for item in p.itens)
        faturamento_por_dia[dia] = faturamento_por_dia.get(dia, 0) + valor_pedido

    if faturamento_por_dia:
        dia_pico_fat = max(faturamento_por_dia, key=faturamento_por_dia.get)
        pico_fat_valor = faturamento_por_dia[dia_pico_fat]
        dia_menor_fat = min(faturamento_por_dia, key=faturamento_por_dia.get)
        menor_fat_valor = faturamento_por_dia[dia_menor_fat]
    else:
        dia_pico_fat = dia_menor_fat = "--"
        pico_fat_valor = menor_fat_valor = 0

    frases = [
        f'<i class="bi bi-currency-dollar text-success"></i> O pico de faturamento ocorreu no dia <strong>{dia_pico_fat}</strong> com <strong>R${pico_fat_valor:,.2f}</strong> vendidos.',
        f'<i class="bi bi-currency-exchange text-danger"></i> O menor faturamento ocorreu no dia <strong>{dia_menor_fat}</strong> com apenas <strong>R${menor_fat_valor:,.2f}</strong> vendidos.',
        f'<i class="bi bi-graph-up-arrow text-success"></i> O pico de pedidos ocorreu no dia <strong>{dia_pico}</strong> com <strong>{pico_valor}</strong> pedidos realizados.',
        f'<i class="bi bi-graph-down-arrow text-danger"></i> O menor volume foi no dia <strong>{dia_menor}</strong> com apenas <strong>{menor_valor}</strong> pedidos.',
        f'<i class="bi bi-cash-coin text-success"></i> O produto que mais contribui para o lucro é <strong>{produto_mais_lucro}</strong>, representando <strong>{percentual_lucro}%</strong> do faturamento total.',
        f'<i class="bi bi-box-seam text-primary"></i> O produto com a maior quantidade vendida é <strong>{produto_mais_vendido}</strong>, representando <strong>{percentual_vendas}%</strong> do total de itens vendidos.',
        f'<i class="bi bi-cash-stack text-warning"></i> O produto que menos contribui para o lucro é <strong>{produto_menos_lucro}</strong>, representando apenas <strong>{percentual_lucro_min}%</strong> do faturamento total.',
        f'<i class="bi bi-box text-secondary"></i> O produto com a menor quantidade de vendas é <strong>{produto_menos_vendido}</strong>, representando apenas <strong>{percentual_vendas_min}%</strong> do total de itens vendidos.'
    ]

    return {
        "kpis": kpis_geral,
        "grafico_produtos": {
            "labels": labels_produtos,
            "valores": valores_produtos
        },
        "frases": frases
    }

@admin_required
def gerar_relatorio_produtos(data_inicio, data_fim):
    todos_produtos = db.session.query(Produtos).all()

    # KPIs
    total_produtos = len(todos_produtos)
    produtos_esgotados = sum(1 for p in todos_produtos if p.estoque_produto == 0)
    produtos_estoque_baixo = [p for p in todos_produtos if 0 < p.estoque_produto <= 5]
    estoque_total = sum(p.estoque_produto for p in todos_produtos)

    kpis_estoque = {
        "total_produtos": total_produtos,
        "produtos_esgotados": produtos_esgotados,
        "produtos_estoque_baixo": len(produtos_estoque_baixo),
        "estoque_total": estoque_total
    }

    # Dados para gráfico de barras (estoque baixo)
    labels_estoque_baixo = [p.descricao_produto for p in produtos_estoque_baixo]
    valores_estoque_baixo = [p.estoque_produto for p in produtos_estoque_baixo]

    # Dados para gráfico donut (vendas por categoria) - agora respeitando datas
    query_pedidos = db.session.query(Pedido).filter(Pedido.status == "retirado")

    if data_inicio:
        query_pedidos = query_pedidos.filter(Pedido.data_hora >= data_inicio)
    if data_fim:
        query_pedidos = query_pedidos.filter(Pedido.data_hora <= data_fim)

    pedidos_retirados = query_pedidos.all()

    vendas_por_categoria = {"SALGADO": 0, "DOCE": 0, "BEBIDA": 0}

    for pedido in pedidos_retirados:
        for item in pedido.itens:
            categoria = item.produto.categoria_produto
            if categoria in vendas_por_categoria:
                valor_item = item.quantidade * item.produto.preco_produto
                vendas_por_categoria[categoria] += valor_item

    labels_vendas_categoria = list(vendas_por_categoria.keys())
    valores_vendas_categoria = list(vendas_por_categoria.values())

    return {
        "kpis": kpis_estoque,
        "grafico_estoque_baixo": {
            "labels": labels_estoque_baixo,
            "valores": valores_estoque_baixo
        },
        "grafico_vendas_categoria": {
            "labels": labels_vendas_categoria,
            "valores": valores_vendas_categoria
        }
    }

@relatorio_bp.route("/produto", methods=["POST"])
@admin_required
def relatorio_produto():
    dados = request.get_json()
    produto_busca = dados.get("produtoBusca")
    periodo = dados.get("periodo")
    data_inicio = dados.get("dataInicio")
    data_fim = dados.get("dataFim")

    # --- Ajuste do período ---
    try:
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
            # Período personalizado
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            inicio_anterior = fim_anterior = None  # sem variação
    except Exception:
        return jsonify({"erro": "Datas inválidas."}), 400

    # --- Buscar produto ---
    if produto_busca.isdigit():
        produto = Produtos.query.get(int(produto_busca))
    else:
        produto = Produtos.query.filter(Produtos.descricao_produto.ilike(f"%{produto_busca}%")).first()
    if not produto:
        return jsonify({"erro": "Produto não encontrado."}), 404

    # --- Pedidos retirados no período ---
    pedidos = Pedido.query.filter(
        Pedido.status == "retirado",
        Pedido.data_hora >= data_inicio,
        Pedido.data_hora <= data_fim
    ).all()

    total_vendas = 0
    total_faturamento_produto = 0
    pedidos_com_produto = 0
    vendas_por_dia = {}

    for p in pedidos:
        itens_produto = [i for i in p.itens if i.produto_id == produto.id]
        if itens_produto:
            pedidos_com_produto += 1
            total_vendas += sum(i.quantidade for i in itens_produto)
            total_faturamento_produto += sum(i.quantidade * i.preco_unitario for i in itens_produto)

            dia = p.data_hora.strftime("%d/%m")
            vendas_por_dia[dia] = vendas_por_dia.get(dia, 0) + sum(i.quantidade * i.preco_unitario for i in itens_produto)

    total_pedidos = len(pedidos)
    percentual_pedidos = round((pedidos_com_produto / total_pedidos) * 100, 1) if total_pedidos > 0 else 0

    # --- Faturamento total do período (todos os produtos) ---
    faturamento_total = sum(
        i.quantidade * i.preco_unitario
        for p in pedidos
        for i in p.itens
    )
    percentual_participacao = round((total_faturamento_produto / faturamento_total) * 100, 1) if faturamento_total > 0 else 0

    # --- Variação de faturamento em relação ao período anterior ---
    if inicio_anterior and fim_anterior:
        pedidos_anteriores = Pedido.query.filter(
            Pedido.status == "retirado",
            Pedido.data_hora >= inicio_anterior,
            Pedido.data_hora <= fim_anterior
        ).all()

        faturamento_anterior = sum(
            i.quantidade * i.preco_unitario
            for p in pedidos_anteriores
            for i in p.itens
            if i.produto_id == produto.id
        )

        variacao_faturamento = round(
            ((total_faturamento_produto - faturamento_anterior) / faturamento_anterior) * 100,
            1
        ) if faturamento_anterior > 0 else 0
    else:
        variacao_faturamento = None  # período personalizado
    
    resposta = {
        "descricao": produto.descricao_produto,
        "id_prod": int(produto.id),
        "categ": produto.categoria_produto,
        "faturamento": total_faturamento_produto,
        "variacaoFaturamento": variacao_faturamento,
        "vendas": total_vendas,
        "estoque": produto.estoque_produto,
        "percentualPedidos": percentual_pedidos,
        "percentualParticipacao": percentual_participacao,
        "grafico": {
            "labels": list(vendas_por_dia.keys()),
            "valores": list(vendas_por_dia.values())
        }
    }
    
    session['produto_especifico'] = resposta

    return jsonify(resposta)

@admin_required
def gerar_relatorio_clientes(data_inicio, data_fim):
    # --- Total de clientes ---
    total_clientes = Usuarios.query.count()

    # --- Novos no período ---
    novos_clientes = Usuarios.query.filter(
        Usuarios.data_criacao_usuario >= data_inicio,
        Usuarios.data_criacao_usuario <= data_fim
    ).count()

    # --- Gráfico de crescimento ---
    crescimento_por_dia = {}
    clientes_no_periodo = Usuarios.query.filter(
        Usuarios.data_criacao_usuario >= data_inicio,
        Usuarios.data_criacao_usuario <= data_fim
    ).all()
    
    for cliente in clientes_no_periodo:
        dia = cliente.data_criacao_usuario.strftime("%d/%m")
        crescimento_por_dia[dia] = crescimento_por_dia.get(dia, 0) + 1

    # --- Top 3 clientes por faturamento ---
    pedidos = Pedido.query.filter(
        Pedido.status == "retirado",
        Pedido.data_hora >= data_inicio,
        Pedido.data_hora <= data_fim
    ).all()

    faturamento_por_cliente = {}
    pedidos_por_cliente = {}

    for p in pedidos:
        if p.id_usuario:
            # Soma faturamento
            faturamento_por_cliente[p.id_usuario] = faturamento_por_cliente.get(p.id_usuario, 0) + sum(
                item.quantidade * item.preco_unitario for item in p.itens
            )
            # Conta pedidos
            pedidos_por_cliente[p.id_usuario] = pedidos_por_cliente.get(p.id_usuario, 0) + 1

    # Pega os 3 maiores por faturamento
    top_clientes_ids = sorted(faturamento_por_cliente, key=faturamento_por_cliente.get, reverse=True)[:3]

    top_clientes = []
    for cid in top_clientes_ids:
        cliente = Usuarios.query.get(cid)
        top_clientes.append({
            "nome": cliente.nome_usuario,
            "codigo_etec": cliente.codigo_etec_usuario,
            "email": cliente.email_usuario,
            "total_pedidos": pedidos_por_cliente.get(cid, 0),
            "faturamento_total": faturamento_por_cliente[cid]
        })
    
    ativos = db.session.query(Usuarios).filter_by(conta_ativa="sim").count()
    inativos = db.session.query(Usuarios).filter_by(conta_ativa="nao").count()

    kpis_clientes = {
        "total_clientes": total_clientes,
        "novos_clientes": novos_clientes,
        "clientes_ativos": ativos,
        "clientes_inativos": inativos
    }

    return {
        "kpis": kpis_clientes,
        "grafico": {
            "labels": list(crescimento_por_dia.keys()),
            "valores": list(crescimento_por_dia.values())
        },
        "top_clientes": top_clientes
    }

@admin_required
def gerar_relatorio_pedidos(data_inicio, data_fim):
    # --- Pedidos do período atual ---
    pedidos = Pedido.query.filter(
        Pedido.data_hora >= data_inicio,
        Pedido.data_hora <= data_fim,
    ).all()

    # --- KPIs ---
    def calcular_kpis(pedidos_periodo):
        pedidos_retirados = len([p for p in pedidos if p.status == "retirado"])
        faturamento = sum(sum(item.quantidade * item.preco_unitario for item in p.itens) for p in pedidos_periodo if p.status == "retirado")
        total_pedidos = len([p for p in pedidos_periodo])
        cancelados = len([p for p in pedidos_periodo if p.status == "cancelado"])
        taxa_cancelamento = round((cancelados / total_pedidos) * 100, 1) if total_pedidos else 0
        valor_medio = round(faturamento / pedidos_retirados, 2) if pedidos_retirados else 0

        return {
            "faturamento": faturamento,
            "total_pedidos": total_pedidos,
            "taxa_cancelamento": taxa_cancelamento,
            "valor_medio_pedido": valor_medio,
        }

    kpis = calcular_kpis(pedidos)

    # --- Gráfico de donut por status ---
    status_contagem = {"pendente": 0, "retirado": 0, "cancelado": 0}
    for p in pedidos:
        if p.status in status_contagem:
            status_contagem[p.status] += 1
    
    # Vendas por dia
    vendas_por_dia = defaultdict(float)
    for pedido in pedidos:
        if pedido.status == "retirado":
            dia = pedido.data_hora.date()
            vendas_por_dia[dia] += pedido.total
    vendas_por_dia = dict(sorted(vendas_por_dia.items()))
    labels_vendas_dia = [d.strftime("%d/%m") for d in vendas_por_dia.keys()]
    valores_vendas_dia = list(vendas_por_dia.values())

    return {
        "kpis": kpis,
        "grafico_status": {
            "labels": list(status_contagem.keys()),
            "valores": list(status_contagem.values())
        },
        "grafico_vendas_dia": {
            "labels": labels_vendas_dia,
            "valores": valores_vendas_dia
        }
    }

@admin_required
def gerar_relatorio_feedbacks(data_inicio, data_fim):
    # Query base com filtro de datas
    query = db.session.query(Feedbacks)
    if data_inicio:
        query = query.filter(Feedbacks.data_feedback >= data_inicio)
    if data_fim:
        query = query.filter(Feedbacks.data_feedback <= data_fim)
    
    feedbacks_filtrados = query.all()

    # KPIs
    total_feedbacks = len(feedbacks_filtrados)
    kpi_duvidas = sum(1 for f in feedbacks_filtrados if f.tipo_feedback == "duvida")
    kpi_reclamacoes = sum(1 for f in feedbacks_filtrados if f.tipo_feedback == "reclamacao")
    kpi_sugestoes = sum(1 for f in feedbacks_filtrados if f.tipo_feedback == "sugestao")
    kpi_elogios = sum(1 for f in feedbacks_filtrados if f.tipo_feedback == "elogio")

    kpis = {
        "total_feedbacks": total_feedbacks,
        "duvidas": kpi_duvidas,
        "reclamacoes": kpi_reclamacoes,
        "sugestoes": kpi_sugestoes,
        "elogios": kpi_elogios
    }

    # Gráfico: distribuição por tipo
    tipos = ["duvida", "reclamacao", "sugestao", "elogio"]
    valores_tipo = [kpis[t] for t in ["duvidas", "reclamacoes", "sugestoes", "elogios"]]

    # Gráfico: evolução ao longo do tempo (quantidade por dia)
    feedbacks_por_dia = defaultdict(int)
    for f in feedbacks_filtrados:
        dia = f.data_feedback.date()
        feedbacks_por_dia[dia] += 1
    feedbacks_por_dia = dict(sorted(feedbacks_por_dia.items()))
    labels_tempo = [d.strftime("%d/%m") for d in feedbacks_por_dia.keys()]
    valores_tempo = list(feedbacks_por_dia.values())

    return {
        "kpis": kpis,
        "grafico_tipo": {
            "labels": tipos,
            "valores": valores_tipo
        },
        "grafico_tempo": {
            "labels": labels_tempo,
            "valores": valores_tempo
        }
    }


@relatorio_bp.route('/exportar/excel', methods=['POST'])
@admin_required
def exportar_relatorio_excel():
    relatorio_ativo = request.form.get('relatorio')

    data_inicio = session.get('data_inicio')
    data_fim = session.get('data_fim')

    # Inicializa o BytesIO para o Excel
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Relatório Geral
        if relatorio_ativo == 'geral':
            geral = gerar_relatorio_geral(data_inicio, data_fim)
            # KPIs
            dados_kpis = [
                {"KPI": "Vendas Totais", "Valor": geral['kpis']['vendas_totais']},
                {"KPI": "Pedidos", "Valor": geral['kpis']['total_pedidos']},
                {"KPI": "Clientes Atendidos", "Valor": geral['kpis']['clientes_atendidos']},
                {"KPI": "Venda Média", "Valor": geral['kpis']['venda_media']}
            ]
            df_kpis = pd.DataFrame(dados_kpis)
            df_kpis.to_excel(writer, index=False, sheet_name='KPIs Gerais')

            # Gráfico: Vendas por Produto
            df_vendas_produto = pd.DataFrame({
                "Produto": geral['grafico_produtos']['labels'],
                "Vendas (un.)": geral['grafico_produtos']['valores']
            })
            df_vendas_produto.to_excel(writer, index=False, sheet_name='Vendas por Produto')

            def limpar_html(texto):
                return re.sub(r'<.*?>', '', texto)
            # Frases de destaques
            frases_puras = [limpar_html(f) for f in geral['frases']]
            df_frases = pd.DataFrame({"Destaques": frases_puras})
            df_frases.to_excel(writer, index=False, sheet_name='Insights')

        # Relatório de Produtos
        elif relatorio_ativo == 'produtos':
            produtos = gerar_relatorio_produtos(data_inicio, data_fim)
            # KPIs produtos
            kpis_produtos = [
                {"KPI": "Total de Produtos", "Valor": produtos['kpis']['total_produtos']},
                {"KPI": "Produtos Esgotados", "Valor": produtos['kpis']['produtos_esgotados']},
                {"KPI": "Estoque Baixo", "Valor": produtos['kpis']['produtos_estoque_baixo']},
                {"KPI": "Estoque Total", "Valor": produtos['kpis']['estoque_total']}
            ]
            df_kpis = pd.DataFrame(kpis_produtos)
            df_kpis.to_excel(writer, index=False, sheet_name='KPIs Produtos')

            # Vendas por categoria
            df_categoria = pd.DataFrame({
                "Categoria": produtos['grafico_vendas_categoria']['labels'],
                "Vendas (R$)": produtos['grafico_vendas_categoria']['valores']
            })
            df_categoria.to_excel(writer, index=False, sheet_name='Vendas por Categoria')

            # Estoque baixo
            df_estoque_baixo = pd.DataFrame({
                "Produto": produtos['grafico_estoque_baixo']['labels'],
                "Estoque": produtos['grafico_estoque_baixo']['valores']
            })
            df_estoque_baixo.to_excel(writer, index=False, sheet_name='Estoque Baixo')

            # Verificar se existe produto pesquisado
            produto_especifico = session.get("produto_especifico")  # armazenar após busca no frontend
            if produto_especifico:
                # Informações gerais do produto
                df_info = pd.DataFrame([{
                    "ID": produto_especifico['id_prod'],
                    "Descrição": produto_especifico['descricao'],
                    "Categoria": produto_especifico['categ'],
                    "Faturamento (R$)": produto_especifico['faturamento'],
                    "Variação Faturamento (%)": produto_especifico['variacaoFaturamento'],
                    "Total Vendas": produto_especifico['vendas'],
                    "Estoque Atual": produto_especifico['estoque'],
                    "% Pedidos": produto_especifico['percentualPedidos'],
                    "% Participação": produto_especifico['percentualParticipacao']
                }])
                df_info.to_excel(writer, index=False, sheet_name='Produto Selecionado')

                # Gráfico do produto específico
                df_grafico_prod = pd.DataFrame({
                    "Dia": produto_especifico['grafico']['labels'],
                    "Vendas (R$)": produto_especifico['grafico']['valores']
                })
                df_grafico_prod.to_excel(writer, index=False, sheet_name='Vendas Produto')

        # Relatório de Clientes
        elif relatorio_ativo == 'clientes':
            clientes = gerar_relatorio_clientes(data_inicio, data_fim)
            # KPIs de Clientes (com .get para evitar KeyError)
            df_kpis = pd.DataFrame([
                {"KPI": "Total de Clientes", "Valor": clientes['kpis'].get('total_clientes', 0)},
                {"KPI": "Novos no Período", "Valor": clientes['kpis'].get('novos_clientes', 0)},
                {"KPI": "Clientes Ativos", "Valor": clientes['kpis'].get('clientes_ativos', 0)},
                {"KPI": "Clientes Inativos", "Valor": clientes['kpis'].get('clientes_inativos', 0)},
            ])
            df_kpis.to_excel(writer, index=False, sheet_name='KPIs Clientes')

            # Gráfico de Crescimento (labels/valores -> linhas no Excel)
            df_crescimento = pd.DataFrame({
                "Dia": clientes['grafico']['labels'],
                "Novos Clientes": clientes['grafico']['valores']
            })
            df_crescimento.to_excel(writer, index=False, sheet_name='Crescimento Clientes')

            # Top Clientes (por faturamento)
            top_clientes = clientes.get('top_clientes', [])
            df_top = pd.DataFrame([
                {
                    "Nome": c.get('nome'),
                    "Código ETEC": c.get('codigo_etec'),
                    "Email": c.get('email'),
                    "Total de Pedidos": c.get('total_pedidos'),
                    "Faturamento Total (R$)": c.get('faturamento_total')
                } for c in top_clientes
            ])
            df_top.to_excel(writer, index=False, sheet_name='Top Clientes')

        # Relatório de Pedidos
        elif relatorio_ativo == 'pedidos':
            pedidos = gerar_relatorio_pedidos(data_inicio, data_fim)
            # KPIs
            df_kpis = pd.DataFrame([
                {"KPI": "Faturamento", "Valor": pedidos['kpis']['faturamento']},
                {"KPI": "Total de Pedidos", "Valor": pedidos['kpis']['total_pedidos']},
                {"KPI": "Taxa de Cancelamento", "Valor": pedidos['kpis']['taxa_cancelamento']},
                {"KPI": "Venda Média", "Valor": pedidos['kpis']['valor_medio_pedido']}
            ])
            df_kpis.to_excel(writer, index=False, sheet_name='KPIs Pedidos')

            # Gráfico de status dos pedidos
            df_status = pd.DataFrame({
                "Status": pedidos['grafico_status']['labels'],
                "Quantidade": pedidos['grafico_status']['valores']
            })
            df_status.to_excel(writer, index=False, sheet_name='Status dos Pedidos')

            # Gráfico: Vendas por Dia
            df_vendas_dia = pd.DataFrame({
                "Data": pedidos['grafico_vendas_dia']['labels'],
                "Vendas (R$)": pedidos['grafico_vendas_dia']['valores']
            })
            df_vendas_dia.to_excel(writer, index=False, sheet_name='Vendas por Dia')

        # Relatório de Feedbacks
        elif relatorio_ativo == 'feedbacks':
            feedbacks = gerar_relatorio_feedbacks(data_inicio, data_fim)
            # KPIs
            df_kpis = pd.DataFrame([
                {"KPI": "Total de Feedbacks", "Valor": feedbacks['kpis']['total_feedbacks']},
                {"KPI": "Dúvidas", "Valor": feedbacks['kpis']['duvidas']},
                {"KPI": "Reclamações", "Valor": feedbacks['kpis']['reclamacoes']},
                {"KPI": "Sugestões", "Valor": feedbacks['kpis']['sugestoes']},
                {"KPI": "Elogios", "Valor": feedbacks['kpis']['elogios']}
            ])
            df_kpis.to_excel(writer, index=False, sheet_name='KPIs Feedbacks')

            # Gráfico de Pizza - Distribuição por Tipo
            df_tipo = pd.DataFrame({
                "Tipo": feedbacks["grafico_tipo"]["labels"],
                "Quantidade": feedbacks["grafico_tipo"]["valores"]
            })
            df_tipo.to_excel(writer, index=False, sheet_name='Distribuição por Tipo')

            # Gráfico de Linha - Evolução ao longo do Tempo
            df_tempo = pd.DataFrame({
                "Data": feedbacks["grafico_tempo"]["labels"],
                "Quantidade": feedbacks["grafico_tempo"]["valores"]
            })
            df_tempo.to_excel(writer, index=False, sheet_name='Evolução no Tempo')


    output.seek(0)

    return send_file(
        output,
        download_name=f'relatorio_{relatorio_ativo}.xlsx',
        as_attachment=True
    )

@relatorio_bp.route("/exportar/pdf", methods=['POST'])
@admin_required
def exportar_relatorio_pdf():
    relatorio_ativo = request.form.get('relatorio')
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()
    data_inicio = session.get('data_inicio')
    data_fim = session.get('data_fim')

    # ========= RELATÓRIO GERAL =========
    if relatorio_ativo == "geral":
        dados = gerar_relatorio_geral(data_inicio, data_fim)

        # ===== Logotipo centralizado =====
        try:
            logo = Image('app/static/images/shared/favicon.png', width=2*cm, height=2*cm)
            tabela_logo = Table([[logo]], colWidths=[6*cm])  # largura ajustável
            tabela_logo.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabela_logo)
            elementos.append(Spacer(1, 12))
        except:
            pass

        # Título
        elementos.append(Paragraph("FoodPay - Relatório Geral", styles["Title"]))
        elementos.append(Spacer(1, 1))

        # Subtítulo com data/hora e período
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        periodo = session.get("periodo_formatado", "Período não informado")

        estilo_info = ParagraphStyle(
            "info",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # centralizado
        )

        info_texto = f"Gerado em {agora} • Período: {periodo}"
        elementos.append(Paragraph(info_texto, estilo_info))
        elementos.append(Spacer(1, 20))

        # ===== KPIs em tabela =====
        kpis = dados["kpis"]
        tabela_kpis = pd.DataFrame([
            ["Vendas Totais", f"R${kpis['vendas_totais']:.2f}"],
            ["Total de Pedidos", kpis["total_pedidos"]],
            ["Clientes Atendidos", kpis["clientes_atendidos"]],
            ["Venda Média", f"R${kpis['venda_media']:.2f}"]
        ], columns=["KPI", "Valor"])

        tabela = Table([tabela_kpis.columns.tolist()] + tabela_kpis.values.tolist())
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 15))

        # ===== Gráfico de pizza dos produtos =====
        graf_produtos = dados["grafico_produtos"]

        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(
            graf_produtos["valores"],
            labels=graf_produtos["labels"],
            autopct="%1.1f%%",
            startangle=90,
            colors=plt.cm.Paired.colors  # paleta de cores agradável
        )

        img_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)

        elementos.append(Image(img_buffer, width=300, height=225))
        elementos.append(Spacer(1, 15))

        # ===== Frases do relatório =====
        for frase in dados.get("frases", []):
            elementos.append(Paragraph(frase, styles["Normal"]))
            elementos.append(Spacer(1, 6))

    # ========= RELATÓRIO DE PRODUTOS =========
    if relatorio_ativo == "produtos":
        dados = gerar_relatorio_produtos(data_inicio, data_fim)

        # ===== Logotipo centralizado =====
        try:
            logo = Image('app/static/images/shared/favicon.png', width=2*cm, height=2*cm)
            tabela_logo = Table([[logo]], colWidths=[6*cm])
            tabela_logo.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabela_logo)
            elementos.append(Spacer(1, 12))
        except:
            pass

        # ===== Título =====
        elementos.append(Paragraph("FoodPay - Relatório de Produtos", styles["Title"]))
        elementos.append(Spacer(1, 1))

        # ===== Subtítulo com data/hora e período =====
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        periodo = session.get("periodo_formatado", "Período não informado")

        estilo_info = ParagraphStyle(
            "info",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )

        info_texto = f"Gerado em {agora} • Período: {periodo}"
        elementos.append(Paragraph(info_texto, estilo_info))
        elementos.append(Spacer(1, 10))

        # ===== KPIs gerais de estoque =====
        kpis = dados["kpis"]
        tabela_kpis = pd.DataFrame([
            ["Total de Produtos", kpis["total_produtos"]],
            ["Produtos Esgotados", kpis["produtos_esgotados"]],
            ["Produtos com Estoque Baixo", kpis["produtos_estoque_baixo"]],
            ["Estoque Total", kpis["estoque_total"]],
        ], columns=["Indicador", "Valor"])

        tabela = Table([tabela_kpis.columns.tolist()] + tabela_kpis.values.tolist())
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 15))

        # ===== Gráfico de estoque baixo =====
        graf_estoque = dados["grafico_estoque_baixo"]
        if graf_estoque["labels"]:
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.bar(graf_estoque["labels"], graf_estoque["valores"], color="orange")
            ax.set_title("Produtos com Estoque Baixo")
            ax.set_xlabel("Produto")
            ax.set_ylabel("Quantidade em Estoque")
            plt.xticks(rotation=45)

            img_buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buffer, format="png")
            plt.close(fig)
            img_buffer.seek(0)

            elementos.append(Image(img_buffer, width=300, height=225))
            elementos.append(Spacer(1, 5))

        # ===== Gráfico de vendas por categoria =====
        graf_categoria = dados["grafico_vendas_categoria"]
        if graf_categoria["labels"]:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.pie(
                graf_categoria["valores"],
                labels=graf_categoria["labels"],
                autopct="%1.1f%%",
                startangle=90,
                colors=plt.cm.Pastel1.colors
            )
            ax.set_title("Distribuição de Vendas por Categoria")

            img_buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buffer, format="png")
            plt.close(fig)
            img_buffer.seek(0)

            elementos.append(Image(img_buffer, width=300, height=225))
            elementos.append(Spacer(1, 15))
        
        elementos.append(PageBreak())

        # ===== Caso produto específico tenha sido filtrado =====
        produto_espec = session.get("produto_especifico")
        if produto_espec:
            estilo_heading2_centralizado = ParagraphStyle(
                "Heading2Centralizado",
                parent=styles["Heading2"],
                alignment=TA_CENTER
            )
            # Subtítulo do produto
            elementos.append(Paragraph(
                f"Produto filtrado: <b>{produto_espec['descricao']}</b> "
                f"(Categoria: {produto_espec['categ']})", 
                estilo_heading2_centralizado
            ))
            elementos.append(Spacer(1, 10))

            # KPIs do produto específico
            tabela_kpis = pd.DataFrame([
                ["Faturamento", f"R${produto_espec['faturamento']:.2f}"],
                ["Variação do Faturamento", f"{produto_espec['variacaoFaturamento']}%"],
                ["Vendas", produto_espec["vendas"]],
                ["Estoque Atual", produto_espec["estoque"]],
                ["% dos Pedidos", f"{produto_espec['percentualPedidos']}%"],
                ["% de Participação no Faturamento", f"{produto_espec['percentualParticipacao']}%"],
            ], columns=["Indicador", "Valor"])

            tabela = Table([tabela_kpis.columns.tolist()] + tabela_kpis.values.tolist())
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            elementos.append(tabela)
            elementos.append(Spacer(1, 15))

            # Gráfico de vendas por dia (produto específico)
            graf = produto_espec["grafico"]
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.plot(graf["labels"], graf["valores"], marker="o")
            ax.set_title("Vendas do Produto por Dia")
            ax.set_xlabel("Data")
            ax.set_ylabel("Quantidade Vendida")
            plt.xticks(rotation=45)

            img_buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buffer, format="png")
            plt.close(fig)
            img_buffer.seek(0)

            elementos.append(Image(img_buffer, width=400, height=250))
            elementos.append(Spacer(1, 15))

    # ========= RELATÓRIO DE CLIENTES =========
    if relatorio_ativo == "clientes":
        dados = gerar_relatorio_clientes(data_inicio, data_fim)

        # ===== Logotipo centralizado =====
        try:
            logo = Image('app/static/images/shared/favicon.png', width=2*cm, height=2*cm)
            tabela_logo = Table([[logo]], colWidths=[6*cm])
            tabela_logo.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabela_logo)
            elementos.append(Spacer(1, 12))
        except:
            pass

        # Título
        elementos.append(Paragraph("FoodPay - Relatório de Clientes", styles["Title"]))
        elementos.append(Spacer(1, 1))

        # Subtítulo com data/hora e período
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        periodo = session.get("periodo_formatado", "Período não informado")

        estilo_info = ParagraphStyle(
            "info",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )

        info_texto = f"Gerado em {agora} • Período: {periodo}"
        elementos.append(Paragraph(info_texto, estilo_info))
        elementos.append(Spacer(1, 20))

        # ===== KPIs em tabela =====
        kpis = dados["kpis"]
        tabela_kpis = pd.DataFrame([
            ["Total de Clientes", kpis["total_clientes"]],
            ["Novos Clientes", kpis["novos_clientes"]],
            ["Clientes Ativos", kpis.get("clientes_ativos", "To do")],
            ["Clientes Inativos", kpis.get("clientes_inativos", "To do")]
        ], columns=["KPI", "Valor"])

        tabela = Table([tabela_kpis.columns.tolist()] + tabela_kpis.values.tolist())
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 15))

        # ===== Gráfico de crescimento de clientes =====
        graf = dados["grafico"]
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(graf["labels"], graf["valores"], marker='o', linestyle='-', color="skyblue")
        ax.set_title("Crescimento de Clientes")
        ax.set_ylabel("Quantidade")
        plt.xticks(rotation=30, ha="right")

        img_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)

        elementos.append(Image(img_buffer, width=400, height=250))
        elementos.append(Spacer(1, 20))

        # ===== Tabela Top Clientes =====
        top_clientes = dados.get("top_clientes", [])
        if top_clientes:
            estilo_heading2_centralizado = ParagraphStyle(
                "Heading2Centralizado",
                parent=styles["Heading2"],
                alignment=TA_CENTER
            )
            elementos.append(Paragraph("Top Clientes", estilo_heading2_centralizado))
            tabela_top = Table(
                [["Nome", "Código ETEC", "Email", "Total Pedidos", "Faturamento Total"]] +
                [[c["nome"], c["codigo_etec"], c["email"], c["total_pedidos"], f"R${c['faturamento_total']:.2f}"]
                for c in top_clientes]
            )
            tabela_top.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            elementos.append(tabela_top)
            elementos.append(Spacer(1, 20))

    # ========= RELATÓRIO DE PEDIDOS =========
    if relatorio_ativo == "pedidos":
        dados = gerar_relatorio_pedidos(data_inicio, data_fim)

        # ===== Logotipo centralizado =====
        try:
            logo = Image('app/static/images/shared/favicon.png', width=2*cm, height=2*cm)
            tabela_logo = Table([[logo]], colWidths=[6*cm])
            tabela_logo.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabela_logo)
            elementos.append(Spacer(1, 12))
        except:
            pass

        # Título
        elementos.append(Paragraph("FoodPay - Relatório de Pedidos", styles["Title"]))
        elementos.append(Spacer(1, 1))

        # Subtítulo com data/hora e período
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        periodo = session.get("periodo_formatado", "Período não informado")
        estilo_info = ParagraphStyle(
            "info",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # centralizado
        )
        info_texto = f"Gerado em {agora} • Período: {periodo}"
        elementos.append(Paragraph(info_texto, estilo_info))
        elementos.append(Spacer(1, 20))

        # ===== KPIs em tabela =====
        kpis = dados["kpis"]
        tabela_kpis = pd.DataFrame([
            ["Faturamento", f"R${kpis['faturamento']:.2f}"],
            ["Total de Pedidos", kpis["total_pedidos"]],
            ["Taxa de Cancelamento", f"{kpis['taxa_cancelamento']:.2f}%"],
            ["Valor Médio por Pedido", f"R${kpis['valor_medio_pedido']:.2f}"]
        ], columns=["KPI", "Valor"])

        tabela = Table([tabela_kpis.columns.tolist()] + tabela_kpis.values.tolist())
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 15))

        # ===== Gráfico de status dos pedidos =====
        graf_status = dados["grafico_status"]
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(
            graf_status["valores"],
            labels=graf_status["labels"],
            autopct="%1.1f%%",
            startangle=90,
            colors=plt.cm.Paired.colors
        )
        img_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)
        elementos.append(Image(img_buffer, width=280, height=210))
        elementos.append(Spacer(1, 15))

        # ===== Gráfico de vendas por dia =====
        graf_vendas_dia = dados["grafico_vendas_dia"]
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(graf_vendas_dia["labels"], graf_vendas_dia["valores"], marker="o", color="skyblue")
        ax.set_title("Vendas por Dia")
        ax.set_ylabel("Quantidade")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)
        elementos.append(Image(img_buffer, width=280, height=210))

    # ========= RELATÓRIO DE FEEDBACKS =========
    if relatorio_ativo == "feedbacks":
        dados = gerar_relatorio_feedbacks(data_inicio, data_fim)

        # ===== Logotipo centralizado =====
        try:
            logo = Image('app/static/images/shared/favicon.png', width=2*cm, height=2*cm)
            tabela_logo = Table([[logo]], colWidths=[6*cm])
            tabela_logo.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elementos.append(tabela_logo)
            elementos.append(Spacer(1, 12))
        except:
            pass

        # Título
        elementos.append(Paragraph("FoodPay - Relatório de Feedbacks", styles["Title"]))
        elementos.append(Spacer(1, 1))

        # Subtítulo com data/hora e período
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        periodo = session.get("periodo_formatado", "Período não informado")
        estilo_info = ParagraphStyle(
            "info",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # centralizado
        )
        info_texto = f"Gerado em {agora} • Período: {periodo}"
        elementos.append(Paragraph(info_texto, estilo_info))
        elementos.append(Spacer(1, 20))

        # ===== KPIs em tabela =====
        kpis = dados["kpis"]
        tabela_kpis = pd.DataFrame([
            ["Total de Feedbacks", kpis["total_feedbacks"]],
            ["Dúvidas", kpis["duvidas"]],
            ["Reclamações", kpis["reclamacoes"]],
            ["Sugestões", kpis["sugestoes"]],
            ["Elogios", kpis["elogios"]],
        ], columns=["KPI", "Valor"])

        tabela = Table([tabela_kpis.columns.tolist()] + tabela_kpis.values.tolist())
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 10))

        # ===== Gráfico por tipo de feedback =====
        graf_tipo = dados["grafico_tipo"]
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(
            graf_tipo["valores"],
            labels=graf_tipo["labels"],
            autopct="%1.1f%%",
            startangle=90,
            colors=plt.cm.Pastel1.colors
        )
        img_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)
        elementos.append(Image(img_buffer, width=280, height=210))
        elementos.append(Spacer(1, 10))

        # ===== Gráfico de feedbacks ao longo do tempo =====
        graf_tempo = dados["grafico_tempo"]
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(graf_tempo["labels"], graf_tempo["valores"], marker="o", color="skyblue")
        ax.set_title("Feedbacks ao Longo do Tempo")
        ax.set_ylabel("Quantidade")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png")
        plt.close(fig)
        img_buffer.seek(0)
        elementos.append(Image(img_buffer, width=280, height=210))

    # Construir PDF
    doc.build(elementos)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"relatorio_{relatorio_ativo}.pdf",
        mimetype="application/pdf"
    )
