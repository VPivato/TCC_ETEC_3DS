from flask import Blueprint, render_template, request, jsonify
from ...models.produto import Produtos
from ...extensions import db
from utils.decorators import admin_required

estoque_bp = Blueprint("estoque", __name__, url_prefix="/estoque")

@estoque_bp.route('/')
@admin_required
def estoque():
    info = calcular_informacoes()
    return render_template('admin/estoque/estoque.html', info=info)

@estoque_bp.route('/repor', methods=['POST'])
@admin_required
def repor_estoque():
    data = request.get_json()
    produto_id = data.get('produto_id')
    quantidade = data.get('quantidade', 0)

    produto = Produtos.query.get(produto_id)
    if not produto:
        return jsonify({"success": False, "message": "Produto não encontrado"}), 404

    try:
        produto.estoque_produto += int(quantidade)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@admin_required
def calcular_informacoes():
    # Consulta todos os produtos
    produtos = Produtos.query.all()

    # KPIs
    total_estoque = sum(p.estoque_produto for p in produtos)
    produtos_esgotados = [p for p in produtos if p.estoque_produto == 0]
    produtos_baixo_estoque = [p for p in produtos if 0 < p.estoque_produto <= 5]

    valor_total_estoque = sum(
        float(p.preco_produto) * p.estoque_produto for p in produtos
    )

    kpis = {
        "total_estoque": total_estoque,
        "produtos_esgotados": len(produtos_esgotados),
        "produtos_baixo_estoque": len(produtos_baixo_estoque),
        "valor_total_estoque": valor_total_estoque,
    }

    # Dados para gráfico de estoque baixo (barras)
    grafico_estoque_baixo = {
        "labels": [p.descricao_produto for p in produtos_baixo_estoque],
        "valores": [p.estoque_produto for p in produtos_baixo_estoque],
    }

    # Filtrar produtos que ainda têm estoque
    produtos_com_estoque = [p for p in produtos if p.estoque_produto > 0]
    # Ordenar por estoque (crescente)
    produtos_ordenados = sorted(produtos_com_estoque, key=lambda p: p.estoque_produto)


    return {
        "kpis": kpis,
        "grafico": grafico_estoque_baixo,
        "lista_esgotados": produtos_esgotados,
        "produtos_ordenados": produtos_ordenados
    }
