import re
import pandas as pd
from io import BytesIO
from flask import session
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, PageBreak

def escrever_dataframe(writer, df, sheet_name):
    df.to_excel(writer, index=False, sheet_name=sheet_name)

def limpar_html(texto):
    return re.sub(r'<.*?>', '', texto)

def criar_kpis_df(kpis_dict):
    return pd.DataFrame([{"KPI": k, "Valor": v} for k, v in kpis_dict.items()])

def criar_grafico_df(labels, valores, col1="Label", col2="Valor"):
    return pd.DataFrame({col1: labels, col2: valores})


def adicionar_logo(elementos, path="app/static/images/shared/favicon.png"):
    try:
        logo = Image(path, width=2*cm, height=2*cm)
        tabela_logo = Table([[logo]], colWidths=[6*cm])
        tabela_logo.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(tabela_logo)
        elementos.append(Spacer(1, 12))
    except:
        pass

def adicionar_titulo(elementos, titulo, styles):
    elementos.append(Paragraph(titulo, styles["Title"]))
    elementos.append(Spacer(1, 1))

def adicionar_subtitulo(elementos, styles):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    periodo = session.get("periodo_formatado", "Período não informado")
    estilo_info = ParagraphStyle(
        "info", parent=styles["Normal"], fontSize=8,
        textColor=colors.grey, alignment=1
    )
    elementos.append(Paragraph(f"Gerado em {agora} • Período: {periodo}", estilo_info))
    elementos.append(Spacer(1, 15))

def titulo_centralizado(elementos, texto, styles):
    estilo_heading4_centralizado = ParagraphStyle(
                "Heading2Centralizado",
                parent=styles["Heading4"],
                alignment=TA_CENTER
        )
    elementos.append(Paragraph(texto, estilo_heading4_centralizado))

def tabela_df(df):
    tabela = Table([df.columns.tolist()] + df.values.tolist())
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    return tabela

def grafico_pizza(labels, valores, cores=plt.cm.Pastel1.colors, title=None, width=300, height=225):
    fig, ax = plt.subplots(figsize=(5, 4))
    if sum(valores) != 0:
        ax.pie(valores, labels=labels, autopct="%1.1f%%", startangle=90, colors=cores)
    if title: ax.set_title(title)
    return salvar_fig_em_buffer(fig, width, height)

def grafico_barra(labels, valores, title="", xlabel="", ylabel="", width=300, height=225):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(labels, valores, color="orange")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45)
    return salvar_fig_em_buffer(fig, width, height)

def grafico_linha(labels, valores, title="", ylabel="", width=300, height=225):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(labels, valores, marker="o", color="skyblue")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    return salvar_fig_em_buffer(fig, width, height)

def salvar_fig_em_buffer(fig, width=300, height=225):
    img_buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)
    return Image(img_buffer, width=width, height=height)


def exportar_relatorio_geral_excel(writer, dados):
    # KPIs
    df_kpis = criar_kpis_df(dados.get('kpis', []))
    escrever_dataframe(writer, df_kpis, 'KPIS gerais')

    # Gráfico: Vendas por Produto
    df_vendas_produto = criar_grafico_df(
        dados['grafico_produtos']['labels'],
        dados['grafico_produtos']['valores'],
        col1='Produto',
        col2='Vendas (un.)'
    )
    escrever_dataframe(writer, df_vendas_produto, "Vendas por produto")

    # Frases de destaques
    frases_puras = [limpar_html(f) for f in dados['frases']]
    df_frases = pd.DataFrame({"Destaques": frases_puras})
    escrever_dataframe(writer, df_frases, "Insights")


def exportar_relatorio_produtos_excel(writer, dados):
    # KPIs produtos
    kpis = dados.get('kpis', [])
    kpis.pop('lista_produtos_estoque_baixo')
    df_kpis = criar_kpis_df(kpis)
    escrever_dataframe(writer, df_kpis, "KPIs produtos")

    # Vendas por categoria
    df_categoria = criar_grafico_df(
        dados['grafico_vendas_categoria']['labels'],
        dados['grafico_vendas_categoria']['valores'],
        col1='Categoria',
        col2='Vendas (R$)'
    )
    escrever_dataframe(writer, df_categoria, 'Vendas por categoria')

    # Estoque baixo
    df_estoque_baixo = criar_grafico_df(
        dados['grafico_estoque_baixo']['labels'],
        dados['grafico_estoque_baixo']['valores'],
        col1='Produto',
        col2='Estoque'
    )
    escrever_dataframe(writer, df_estoque_baixo, "Estoque baixo")

    # Verificar se existe produto pesquisado
    produto_especifico = session.get("produto_especifico")
    if produto_especifico:
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
        escrever_dataframe(writer, df_info, "Produto selecionado")

        # Gráfico do produto específico
        df_grafico_prod = criar_grafico_df(
            produto_especifico['grafico']['labels'],
            produto_especifico['grafico']['valores'],
            col1="Dia",
            col2="Vendas (R$)"
        )
        escrever_dataframe(writer, df_grafico_prod, "Vendas selecionado")


def exportar_relatorio_clientes_excel(writer, dados):
    # KPIs clientes
    df_kpis = criar_kpis_df(dados.get('kpis', []))
    escrever_dataframe(writer, df_kpis, 'KPIs clientes')

    # Gráfico de Crescimento (labels/valores -> linhas no Excel)
    df_crescimento = criar_grafico_df(
        dados['grafico']['labels'],
        dados['grafico']['valores'],
        col1="Dia",
        col2="Novos Clientes"
    )
    escrever_dataframe(writer, df_crescimento, 'Crescimento clientes')

    # Top Clientes (por faturamento)
    top_clientes = dados.get('top_clientes', [])
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
    escrever_dataframe(writer, df_top, 'Top clientes')


def exportar_relatorio_pedidos_excel(writer, dados):
    # KPIs
    df_kpis = criar_kpis_df(dados.get('kpis', []))
    escrever_dataframe(writer, df_kpis, 'KPIs pedidos')

    # Gráfico de status dos pedidos
    df_status = criar_grafico_df(
        dados['grafico_status']['labels'],
        dados['grafico_status']['valores'],
        col1="Status",
        col2="Quantidade"
    )
    escrever_dataframe(writer, df_status, 'Status dos Pedidos')

    # Gráfico: Vendas por Dia
    df_vendas_dia = criar_grafico_df(
        dados['grafico_vendas_dia']['labels'],
        dados['grafico_vendas_dia']['valores'],
        col1="Data",
        col2="Vendas (R$)"
    )
    escrever_dataframe(writer, df_vendas_dia, 'Vendas por Dia')


def exportar_relatorio_feedbacks_excel(writer, dados):
    # KPIs
    df_kpis = criar_kpis_df(dados.get('kpis', []))
    escrever_dataframe(writer, df_kpis, 'KPIs Feedbacks')

    # Gráfico de Pizza - Distribuição por Tipo
    df_tipo = criar_grafico_df(
        dados["grafico_tipo"]["labels"],
        dados["grafico_tipo"]["valores"],
        col1="Tipo",
        col2="Quantidade"
    )
    escrever_dataframe(writer, df_tipo, 'Distribuição por Tipo')

    # Gráfico de Linha - Evolução ao longo do Tempo
    df_tempo = criar_grafico_df(
        dados["grafico_tempo"]["labels"],
        dados["grafico_tempo"]["valores"],
        col1="Data",
        col2="Quantidade"
    )
    escrever_dataframe(writer, df_tempo, 'Evolução no Tempo')


def exportar_relatorio_geral_pdf(dados, styles):
    elementos = []
    adicionar_logo(elementos)
    adicionar_titulo(elementos, "FoodPay - Relatório Geral", styles)
    adicionar_subtitulo(elementos, styles)

    # KPIs
    kpis = dados["kpis"]
    df = pd.DataFrame([
        ["Vendas Totais", f"R${kpis['vendas_totais']:.2f}"],
        ["Total de Pedidos", kpis["total_pedidos"]],
        ["Clientes Atendidos", kpis["clientes_atendidos"]],
        ["Venda Média", f"R${kpis['venda_media']:.2f}"]
    ], columns=["KPI", "Valor"])
    elementos.append(tabela_df(df))
    elementos.append(Spacer(1, 15))

    # Gráfico
    graf = dados["grafico_produtos"]
    elementos.append(grafico_pizza(graf["labels"], graf["valores"], plt.cm.Paired.colors, title="Top produtos vendidos por un."))
    elementos.append(Spacer(1, 15))

    # Frases
    titulo_centralizado(elementos, "Visão geral:", styles)
    for frase in dados.get("frases", []):
        elementos.append(Paragraph(frase, styles["Normal"]))
        elementos.append(Spacer(1, 6))

    return elementos


def exportar_relatorio_produtos_pdf(dados, styles):
    elementos = []
    adicionar_logo(elementos)
    adicionar_titulo(elementos, "FoodPay - Relatório de Produtos", styles)
    adicionar_subtitulo(elementos, styles)

    # KPIs
    kpis = dados["kpis"]
    tabela_kpis = pd.DataFrame([
        ["Total de Produtos", kpis["total_produtos"]],
        ["Produtos Esgotados", kpis["produtos_esgotados"]],
        ["Produtos com Estoque Baixo", kpis["produtos_estoque_baixo"]],
        ["Estoque Total", kpis["estoque_total"]],
    ], columns=["Indicador", "Valor"])
    elementos.append(tabela_df(tabela_kpis))
    elementos.append(Spacer(1, 10))

    # Gráfico de estoque baixo
    graf_estoque = dados["grafico_estoque_baixo"]
    if graf_estoque["labels"]:
        elementos.append(grafico_barra(
            graf_estoque["labels"],
            graf_estoque["valores"],
            title="Produtos com Estoque Baixo",
            xlabel="Produto",
            ylabel="Quantidade em Estoque"
        ))
        elementos.append(Spacer(1, 5))

    # Gráfico de vendas por categoria
    graf_categoria = dados["grafico_vendas_categoria"]
    if graf_categoria["labels"]:
        elementos.append(grafico_pizza(
            graf_categoria["labels"],
            graf_categoria["valores"],
            title="Distribuição de Vendas por Categoria"
        ))

    # Caso produto específico tenha sido filtrado
    produto_espec = session.get("produto_especifico")
    if produto_espec:
        elementos.append(PageBreak())
        elementos.append(Spacer(1, 5))

        # Subtítulo do produto
        titulo_centralizado(elementos, f"Produto filtrado: <b>{produto_espec['descricao']}</b>"f"(Categoria: {produto_espec['categ']})", styles)
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

        elementos.append(tabela_df(tabela_kpis))
        elementos.append(Spacer(1, 15))

        # Gráfico de vendas por dia (produto específico)
        graf = produto_espec["grafico"]
        elementos.append(grafico_linha(
            graf["labels"],
            graf["valores"],
            title="Vendas do Produto por Dia",
            ylabel="Quantidade Vendida"
        ))
        elementos.append(Spacer(1, 15))
    
    return elementos


def exportar_relatorio_clientes_pdf(dados, styles):
    elementos = []
    adicionar_logo(elementos)
    adicionar_titulo(elementos, "FoodPay - Relatório de Clientes", styles)
    adicionar_subtitulo(elementos, styles)

    # KPIs
    kpis = dados["kpis"]
    tabela_kpis = pd.DataFrame([
        ["Total de Clientes", kpis["total_clientes"]],
        ["Novos Clientes", kpis["novos_clientes"]],
        ["Clientes Ativos", kpis.get("clientes_ativos", "To do")],
        ["Clientes Inativos", kpis.get("clientes_inativos", "To do")]
    ], columns=["KPI", "Valor"])
    elementos.append(tabela_df(tabela_kpis))
    elementos.append(Spacer(1, 10))

    # Gráfico de crescimento de clientes
    graf = dados["grafico"]
    elementos.append(grafico_linha(graf['labels'], graf['valores'], title='Crescimento de clientes'))
    elementos.append(Spacer(1, 10))

    # ===== Tabela Top Clientes =====
    top_clientes = dados.get("top_clientes", [])
    if top_clientes:
        estilo_heading2_centralizado = ParagraphStyle(
            "Heading2Centralizado",
            parent=styles["Heading2"],
            alignment=TA_CENTER
        )
        elementos.append(Paragraph("Top Clientes", estilo_heading2_centralizado))
        elementos.append(Spacer(1, 5))

        tabela_top_df = pd.DataFrame([
            [c["nome"], c['rm'], c["codigo_etec"], c["email"], c["total_pedidos"], f"R${c['faturamento_total']:.2f}"]
            for c in top_clientes
        ], columns=["Nome","RM", "Código ETEC", "Email", "Total Pedidos", "Faturamento Total"])

        elementos.append(tabela_df(tabela_top_df))
    
    return elementos


def exportar_relatorio_pedidos_pdf(dados, styles):
    elementos = []
    adicionar_logo(elementos)
    adicionar_titulo(elementos, "FoodPay - Relatório de Pedidos", styles)
    adicionar_subtitulo(elementos, styles)

    # KPIs em tabela
    kpis = dados["kpis"]
    tabela_kpis = pd.DataFrame([
        ["Faturamento", f"R${kpis['faturamento']:.2f}"],
        ["Total de Pedidos", kpis["total_pedidos"]],
        ["Taxa de Cancelamento", f"{kpis['taxa_cancelamento']:.2f}%"],
        ["Valor Médio por Pedido", f"R${kpis['valor_medio_pedido']:.2f}"]
    ], columns=["KPI", "Valor"])
    elementos.append(tabela_df(tabela_kpis))
    elementos.append(Spacer(1, 5))

    # Gráfico de status dos pedidos
    graf_status = dados["grafico_status"]
    elementos.append(grafico_pizza(graf_status['labels'], graf_status['valores'], title='Status dos pedidos'))
    elementos.append(Spacer(1, 5))

    # Gráfico de vendas por dia
    graf_vendas_dia = dados["grafico_vendas_dia"]
    elementos.append(grafico_linha(graf_vendas_dia['labels'], graf_vendas_dia['valores'], title='Vendas por dia'))

    return elementos


def exportar_relatorio_feedbacks_pdf(dados, styles):
    elementos = []
    adicionar_logo(elementos)
    adicionar_titulo(elementos, "FoodPay - Relatório de Feedbacks", styles)
    adicionar_subtitulo(elementos, styles)

    # KPIs
    kpis = dados["kpis"]
    tabela_kpis = pd.DataFrame([
        ["Total de Feedbacks", kpis["total_feedbacks"]],
        ["Dúvidas", kpis["duvidas"]],
        ["Reclamações", kpis["reclamacoes"]],
        ["Sugestões", kpis["sugestoes"]],
        ["Elogios", kpis["elogios"]],
    ], columns=["KPI", "Valor"])
    elementos.append(tabela_df(tabela_kpis))

    # ===== Gráfico por tipo de feedback =====
    graf_tipo = dados["grafico_tipo"]
    elementos.append(grafico_pizza(graf_tipo['labels'], graf_tipo['valores'], title='Distribuição por tipo', width=270, height=200))

    # ===== Gráfico de feedbacks ao longo do tempo =====
    graf_tempo = dados["grafico_tempo"]
    elementos.append(grafico_linha(graf_tempo['labels'], graf_tempo['valores'], title='Feedbacks ao longo do tempo'))

    return elementos
