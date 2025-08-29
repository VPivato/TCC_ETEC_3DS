from flask import Blueprint, render_template, request, jsonify, send_file, session
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # backend para geração de imagens sem interface gráfica
from io import BytesIO
import pandas as pd
import re
from sqlalchemy import func

from utils.relatorio_utils import (filtrar_pedidos, calcular_kpis_geral, vendas_por_produto, analisar_movimento_diario,
                                   analisar_produtos, info_mais_vendidos, info_menos_vendidos, analisar_faturamento_diario,
                                   analisar_categorias, calcular_kpis_produtos, buscar_produto, analisar_vendas_produto,
                                   contar_clientes_ativos_inativos, top_clientes_por_faturamento, ajustar_periodo,
                                   novos_clientes_no_periodo, crescimento_clientes_por_dia, calcular_kpis_pedidos,
                                   grafico_faturamento_por_dia, grafico_pedidos_por_status, filtrar_feedbacks,
                                   calcular_kpis_feedbacks, grafico_feedbacks_por_tipo, grafico_feedbacks_por_dia
                                   )

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

def gerar_relatorio_geral(data_inicio, data_fim):
    # Query de todos os pedidos entre o periodo definido
    pedidos_periodo = filtrar_pedidos(data_inicio, data_fim)

    # KPIs geral
    kpis_geral = calcular_kpis_geral(pedidos_periodo)

    # Gráfico top_X produtos mais vendidos
    labels_produtos, valores_produtos = vendas_por_produto(pedidos_periodo, 5)

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

def gerar_relatorio_produtos(data_inicio=None, data_fim=None):
    # KPIs produtos
    kpis_estoque = calcular_kpis_produtos()

    # Gráfico estoque baixo
    labels_estoque_baixo = [p.descricao_produto for p in kpis_estoque.get('lista_produtos_estoque_baixo')]
    valores_estoque_baixo = [p.estoque_produto for p in kpis_estoque.get('lista_produtos_estoque_baixo')]

    pedidos = filtrar_pedidos(data_inicio, data_fim)
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
        data_inicio, data_fim, inicio_anterior, fim_anterior = ajustar_periodo(periodo, data_inicio, data_fim)
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
    total_clientes = Usuarios.query.count()
    novos_clientes = novos_clientes_no_periodo(data_inicio, data_fim)
    ativos, inativos = contar_clientes_ativos_inativos()
    crescimento_por_dia = crescimento_clientes_por_dia(data_inicio, data_fim)
    top_clientes = top_clientes_por_faturamento(data_inicio, data_fim)

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

def gerar_relatorio_pedidos(data_inicio, data_fim):
    # Buscar pedidos do período
    pedidos = filtrar_pedidos(data_inicio, data_fim)

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

def gerar_relatorio_feedbacks(data_inicio, data_fim):
    feedbacks = filtrar_feedbacks(data_inicio, data_fim)

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
                    "RM": c.get('rm'),
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
                [["Nome","RM", "Código ETEC", "Email", "Total Pedidos", "Faturamento Total"]] +
                [[c["nome"], c['rm'], c["codigo_etec"], c["email"], c["total_pedidos"], f"R${c['faturamento_total']:.2f}"]
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
