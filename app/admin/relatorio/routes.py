import pandas as pd
from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, send_file, session

from utils.relatorio_utils import (filtrar_pedidos, calcular_kpis_geral, vendas_por_produto, analisar_movimento_diario,
                                   analisar_produtos, info_mais_vendidos, info_menos_vendidos, analisar_faturamento_diario,
                                   analisar_categorias, calcular_kpis_produtos, buscar_produto, analisar_vendas_produto,
                                   calcular_kpis_clientes, calcular_kpis_pedidos, grafico_faturamento_por_dia, ajustar_periodo,
                                   grafico_pedidos_por_status, filtrar_feedbacks, calcular_kpis_feedbacks, top_clientes_por_faturamento,
                                   grafico_feedbacks_por_tipo, grafico_feedbacks_por_dia, crescimento_clientes_por_dia
                                   )
from utils.relatorio_export_utils import (exportar_relatorio_geral_excel, exportar_relatorio_produtos_excel,
                                          exportar_relatorio_clientes_excel, exportar_relatorio_pedidos_excel,
                                          exportar_relatorio_feedbacks_excel, exportar_relatorio_geral_pdf,
                                          exportar_relatorio_produtos_pdf, exportar_relatorio_clientes_pdf,
                                          exportar_relatorio_pedidos_pdf, exportar_relatorio_feedbacks_pdf)

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet

from ...models.produto import Produtos
from utils.decorators import admin_required

relatorio_bp = Blueprint("relatorio", __name__, url_prefix="/relatorio")

@relatorio_bp.route('/')
@admin_required
def relatorio():
    session.pop('produto_especifico', None)

    periodo = request.args.get("periodo", "ultima_semana")
    data_inicio_arg = request.args.get("dataInicio")
    data_fim_arg = request.args.get("dataFim")

    data_inicio, data_fim, _, _, periodo_formatado = ajustar_periodo(periodo, data_inicio_arg, data_fim_arg)
    
    session['data_inicio'] = data_inicio
    session['data_fim'] = data_fim
    session['periodo_formatado'] = periodo_formatado

    pedidos_periodo = filtrar_pedidos(data_inicio, data_fim)
    feedbacks_periodo = filtrar_feedbacks(data_inicio, data_fim)
    
    dados_geral = gerar_relatorio_geral(pedidos_periodo, data_inicio, data_fim)
    dados_produtos = gerar_relatorio_produtos(pedidos_periodo)
    dados_clientes = gerar_relatorio_clientes(data_inicio, data_fim)
    dados_pedidos = gerar_relatorio_pedidos(pedidos_periodo)
    dados_feedbacks = gerar_relatorio_feedbacks(feedbacks_periodo)

    session['relatorios_cache'] = {
        "geral": dados_geral,
        "produtos": dados_produtos,
        "clientes": dados_clientes,
        "pedidos": dados_pedidos,
        "feedbacks": dados_feedbacks
    }

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

def gerar_relatorio_geral(_pedidos_periodo, data_inicio=None, data_fim=None):
    # Query de todos os pedidos entre o periodo definido
    pedidos_periodo = _pedidos_periodo

    # KPIs geral
    kpis_geral = calcular_kpis_geral(data_inicio, data_fim)

    # Gráfico top_X produtos mais vendidos
    labels_produtos, valores_produtos = vendas_por_produto(5, data_inicio, data_fim)

    # Pico e menor volume (qnt.) de pedidos
    dia_pico, pico_valor, dia_menor, menor_valor = analisar_movimento_diario(pedidos_periodo)

    # Dicionário de produtos vendidos (qnt.) e seu respectivo faturamento (R$)
    vendas_produtos, faturamento_produtos = analisar_produtos(pedidos_periodo)

    # Produtos mais vendidos e mais lucrativos
    produto_mais_vendido, percentual_vendas, produto_mais_lucro, percentual_lucro = info_mais_vendidos(vendas_produtos, faturamento_produtos)

    # Produtos menos vendidos e menos lucrativos
    produto_menos_vendido, percentual_vendas_min, produto_menos_lucro, percentual_lucro_min = info_menos_vendidos(vendas_produtos, faturamento_produtos)

    # dia de maior/menor faturamento diário
    dia_pico_fat, pico_fat_valor, dia_menor_fat, menor_fat_valor = analisar_faturamento_diario(pedidos_periodo)

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

def gerar_relatorio_produtos(_pedidos_periodo):
    # KPIs produtos
    kpis_estoque = calcular_kpis_produtos()

    # Gráfico estoque baixo
    labels_estoque_baixo = [p.descricao_produto for p in kpis_estoque.get('lista_produtos_estoque_baixo')]
    valores_estoque_baixo = [p.estoque_produto for p in kpis_estoque.get('lista_produtos_estoque_baixo')]

    pedidos = _pedidos_periodo
    _, faturamento_dict = analisar_produtos(pedidos)

    # Gráfico vendas por categorias
    produtos_ref = {p.descricao_produto: p for p in Produtos.query.all()}
    vendas_por_categoria = analisar_categorias(faturamento_dict, produtos_ref)

    return {
        "kpis": kpis_estoque,
        "grafico_estoque_baixo": {
            "labels": labels_estoque_baixo,
            "valores": valores_estoque_baixo
        },
        "grafico_vendas_categoria": {
            "labels": list(vendas_por_categoria.keys()),
            "valores": list(vendas_por_categoria.values())
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

    # Ajuste do periodo
    try:
        data_inicio, data_fim, inicio_anterior, fim_anterior, _ = ajustar_periodo(periodo, data_inicio, data_fim)
    except Exception:
        return jsonify({"erro": "Datas inválidas."}), 400

    # Buscar produto
    produto = buscar_produto(produto_busca)
    if not produto:
        return jsonify({"erro": "Produto não encontrado."}), 404
    
    # Vendas produto
    total_vendas, total_faturamento_produto, vendas_por_dia = analisar_vendas_produto(produto, data_inicio, data_fim)

    # Pedidos no período (todos os produtos)
    pedidos = filtrar_pedidos(data_inicio, data_fim, status="retirado")
    total_pedidos = len(pedidos)
    pedidos_com_produto = sum(1 for p in pedidos if any(i.produto_id == produto.id for i in p.itens))
    percentual_pedidos = round((pedidos_com_produto / total_pedidos) * 100, 1) if total_pedidos > 0 else 0

    faturamento_total = sum(i.quantidade * i.preco_unitario for p in pedidos for i in p.itens)
    percentual_participacao = round((total_faturamento_produto / faturamento_total) * 100, 1) if faturamento_total > 0 else 0

    # Variação faturamento
    variacao_faturamento = None
    if inicio_anterior and fim_anterior:
        _, faturamento_anterior, _ = analisar_vendas_produto(produto, inicio_anterior, fim_anterior)
        variacao_faturamento = round(
            ((total_faturamento_produto - faturamento_anterior) / faturamento_anterior) * 100, 1
        ) if faturamento_anterior > 0 else 0

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

def gerar_relatorio_clientes(data_inicio, data_fim):
    kpis_clientes = calcular_kpis_clientes(data_inicio, data_fim)
    crescimento_por_dia = crescimento_clientes_por_dia(data_inicio, data_fim)
    top_clientes = top_clientes_por_faturamento(data_inicio, data_fim)

    return {
        "kpis": kpis_clientes,
        "grafico": {
            "labels": list(crescimento_por_dia.keys()),
            "valores": list(crescimento_por_dia.values())
        },
        "top_clientes": top_clientes
    }

def gerar_relatorio_pedidos(_pedidos_periodo):
    # Buscar pedidos do período
    pedidos = _pedidos_periodo

    # KPIs pedidos
    kpis = calcular_kpis_pedidos(pedidos)

    # Gráfico de donut por status
    grafico_status = grafico_pedidos_por_status(pedidos)

    # Gráfico de vendas por dia
    grafico_vendas_dia = grafico_faturamento_por_dia(pedidos)

    return {
        "kpis": kpis,
        "grafico_status": grafico_status,
        "grafico_vendas_dia": grafico_vendas_dia
    }

def gerar_relatorio_feedbacks(_feedbacks_periodo):
    feedbacks = _feedbacks_periodo

    # KPIs feedbacks
    kpis = calcular_kpis_feedbacks(feedbacks)

    # Gráfico por tipo
    grafico_tipo = grafico_feedbacks_por_tipo(kpis)

    # Gráfico de evolução no tempo
    grafico_tempo = grafico_feedbacks_por_dia(feedbacks)

    return {
        "kpis": kpis,
        "grafico_tipo": grafico_tipo,
        "grafico_tempo": grafico_tempo
    }


@relatorio_bp.route('/exportar/excel', methods=['POST'])
@admin_required
def exportar_relatorio_excel():
    relatorio_ativo = request.form.get('relatorio')
    dados = session['relatorios_cache'].get(relatorio_ativo)

    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if relatorio_ativo == 'geral':
            exportar_relatorio_geral_excel(writer, dados)

        elif relatorio_ativo == 'produtos':
            exportar_relatorio_produtos_excel(writer, dados)

        elif relatorio_ativo == 'clientes':
            exportar_relatorio_clientes_excel(writer, dados)

        elif relatorio_ativo == 'pedidos':
            exportar_relatorio_pedidos_excel(writer, dados)
            
        elif relatorio_ativo == 'feedbacks':
            exportar_relatorio_feedbacks_excel(writer, dados)

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
    dados = session['relatorios_cache'].get(relatorio_ativo)

    if relatorio_ativo == "geral":
        elementos = exportar_relatorio_geral_pdf(dados, styles)

    if relatorio_ativo == "produtos":
        elementos = exportar_relatorio_produtos_pdf(dados, styles)

    if relatorio_ativo == "clientes":
        elementos = exportar_relatorio_clientes_pdf(dados, styles)

    if relatorio_ativo == "pedidos":
        elementos = exportar_relatorio_pedidos_pdf(dados, styles)

    if relatorio_ativo == "feedbacks":
        elementos = exportar_relatorio_feedbacks_pdf(dados, styles)

    # Construir PDF
    doc.build(elementos)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"relatorio_{relatorio_ativo}.pdf",
        mimetype="application/pdf"
    )
