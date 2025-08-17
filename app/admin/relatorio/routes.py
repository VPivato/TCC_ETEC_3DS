from flask import Blueprint, render_template, request, jsonify
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
    
    dados_geral = gerar_relatorio_geral(data_inicio, data_fim)
    dados_produtos = gerar_relatorio_produtos(data_inicio, data_fim)
    dados_clientes = gerar_relatorio_clientes(data_inicio, data_fim)
    dados_pedidos = gerar_relatorio_pedidos(data_inicio, data_fim)

    return render_template('admin/relatorio/relatorio.html', 
                           periodo=periodo,
                           periodo_formatado=periodo_formatado,
                           data_inicio=data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
                           data_fim=data_fim.strftime("%Y-%m-%d") if data_fim else "",

                           geral=dados_geral,
                           produto=dados_produtos,
                           clientes=dados_clientes,
                           pedidos=dados_pedidos
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

    return jsonify({
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
    })


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

    kpis_clientes = {
        "total_clientes": total_clientes,
        "novos_clientes": novos_clientes
    }

    return {
        "kpis": kpis_clientes,
        "grafico": {
            "labels": list(crescimento_por_dia.keys()),
            "valores": list(crescimento_por_dia.values())
        },
        "top_clientes": top_clientes
    }


def gerar_relatorio_pedidos(data_inicio, data_fim):
    # --- Período anterior ---
    delta = data_fim - data_inicio
    periodo_anterior_inicio = data_inicio - delta - timedelta(days=1)
    periodo_anterior_fim = data_inicio - timedelta(days=1)

    # --- Pedidos do período atual ---
    pedidos = Pedido.query.filter(
        Pedido.data_hora >= data_inicio,
        Pedido.data_hora <= data_fim,
    ).all()

    # --- Pedidos do período anterior ---
    pedidos_anteriores = Pedido.query.filter(
        Pedido.data_hora >= periodo_anterior_inicio,
        Pedido.data_hora <= periodo_anterior_fim
    ).all()

    # --- KPIs ---
    def calcular_kpis(pedidos_periodo, pedidos_periodo_ant):
        faturamento = sum(sum(item.quantidade * item.preco_unitario for item in p.itens) for p in pedidos_periodo if p.status == "retirado")
        total_pedidos = len([p for p in pedidos_periodo if p.status == 'retirado'])
        cancelados = len([p for p in pedidos_periodo if p.status == "cancelado"])
        taxa_cancelamento = round((cancelados / total_pedidos) * 100, 1) if total_pedidos else 0
        valor_medio = round(faturamento / total_pedidos, 2) if total_pedidos else 0

        # Período anterior
        faturamento_ant = sum(sum(item.quantidade * item.preco_unitario for item in p.itens) for p in pedidos_periodo_ant)
        total_pedidos_ant = len(pedidos_periodo_ant)
        cancelados_ant = len([p for p in pedidos_periodo_ant if p.status == "cancelado"])
        taxa_cancelamento_ant = round((cancelados_ant / total_pedidos_ant) * 100, 1) if total_pedidos_ant else 0
        valor_medio_ant = round(faturamento_ant / total_pedidos_ant, 2) if total_pedidos_ant else 0

        # Variações
        def calcular_variacao(atual, anterior):
            if anterior == 0:
                return 0
            return round(((atual - anterior) / anterior) * 100, 1)

        return {
            "faturamento": faturamento,
            "variacao_faturamento": calcular_variacao(faturamento, faturamento_ant),
            "total_pedidos": total_pedidos,
            "variacao_pedidos": calcular_variacao(total_pedidos, total_pedidos_ant),
            "taxa_cancelamento": taxa_cancelamento,
            "variacao_cancelamento": calcular_variacao(taxa_cancelamento, taxa_cancelamento_ant),
            "valor_medio_pedido": valor_medio,
            "variacao_valor_medio": calcular_variacao(valor_medio, valor_medio_ant)
        }

    kpis = calcular_kpis(pedidos, pedidos_anteriores)

    # --- Gráfico de donut por status ---
    status_contagem = {"pendente": 0, "retirado": 0, "cancelado": 0}
    for p in pedidos:
        if p.status in status_contagem:
            status_contagem[p.status] += 1

    # --- Frases destacadas ---
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
        "kpis": kpis,
        "grafico": {
            "labels": list(status_contagem.keys()),
            "valores": list(status_contagem.values())
        },
        "frases": frases
    }
