import re
import pandas as pd
from flask import session

def escrever_dataframe(writer, df, sheet_name):
    df.to_excel(writer, index=False, sheet_name=sheet_name)

def limpar_html(texto):
    return re.sub(r'<.*?>', '', texto)

def criar_kpis_df(kpis_dict):
    return pd.DataFrame([{"KPI": k, "Valor": v} for k, v in kpis_dict.items()])

def criar_grafico_df(labels, valores, col1="Label", col2="Valor"):
    return pd.DataFrame({col1: labels, col2: valores})


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