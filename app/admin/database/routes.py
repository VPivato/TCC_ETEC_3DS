import os
from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import func
from datetime import datetime

from ...models.usuario import Usuarios
from ...models.notificacao import Notificacoes
from ...models.feedback import Feedbacks
from ...models.produto import Produtos
from ...models.pedido import Pedido
from ...models.item_pedido import ItemPedido
from ...models.aluno import Alunos
from ...extensions import db

from utils.decorators import admin_required

database_bp = Blueprint("database", __name__, url_prefix="/database")

MODELOS = {
    'Usuarios': Usuarios,
    "Notificacoes": Notificacoes,
    "Feedbacks": Feedbacks,
    "Produtos": Produtos,
    "Pedidos": Pedido,
    "ItemPedido": ItemPedido,
    "Alunos": Alunos
}

@database_bp.route('/', methods=["POST", "GET"])
@admin_required
def database():
    return render_template("admin/database/database.html", modelos=MODELOS.keys())



@database_bp.route('/get_colunas', methods=['POST'])
@admin_required
def get_colunas():
    nome_modelo = request.json.get("modelo")
    modelo = MODELOS.get(nome_modelo)
    if not modelo:
        return jsonify({'erro': 'Modelo não encontrado'}), 400
    colunas = [col.name for col in modelo.__table__.columns]
    return jsonify(colunas)



@database_bp.route('/get_registros', methods=['POST'])
@admin_required
def get_registros():
    payload = request.json or {}
    nome_modelo = payload.get('modelo')
    page = int(payload.get('page', 1))
    per_page = int(payload.get('per_page', 25))

    # limitar per_page para evitar abuso
    per_page = max(1, min(per_page, 200))

    modelo = MODELOS.get(nome_modelo)
    if not modelo:
        return jsonify({'erro': 'Modelo não encontrado'}), 400

    colunas = [col.name for col in modelo.__table__.columns]

    # Query básica: ordena por id para consistência
    query = db.session.query(modelo).order_by(getattr(modelo, 'id').asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    registros_json = [
        {col: getattr(r, col) for col in colunas}
        for r in pagination.items
    ]

    return jsonify({
        'colunas': colunas,
        'registros': registros_json,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages
    })



@database_bp.route('/excluir/<modelo>/<int:id>', methods=['POST'])
@admin_required
def excluir_registro(modelo, id):
    try:
        modelo_classe = MODELOS.get(modelo)
        if not modelo_classe:
            return jsonify({'erro': 'Modelo inválido'}), 400

        registro = db.session.get(modelo_classe, id)
        if not registro:
            return jsonify({'erro': 'Registro não encontrado'}), 404

        # 🔹 Caso especial: se for um Pedido, devolver o estoque
        if modelo_classe.__tablename__ == "pedido":
            if registro.status == 'pendente':
                for item in registro.itens:
                    produto = Produtos.query.get(item.produto_id)
                    if produto:
                        produto.estoque_produto += item.quantidade

        # Busca e exclui imagem, se houver
        for attr_name in dir(registro):
            if 'imagem' in attr_name.lower():
                imagem_path = getattr(registro, attr_name, None)
                if isinstance(imagem_path, str) and imagem_path.strip():
                    caminho_imagem = os.path.join(current_app.static_folder, imagem_path)
                    if os.path.exists(caminho_imagem) and os.path.normpath(imagem_path) != os.path.normpath('uploads/pfp/default.jpg'):
                        os.remove(caminho_imagem)
                break  # remove apenas a primeira imagem

        db.session.delete(registro)
        db.session.commit()
        return jsonify({'sucesso': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao excluir: {str(e)}'}), 500



@database_bp.route('/filtrar', methods=['POST'])
@admin_required
def filtrar():
    dados = request.json or {}
    modelo_nome = dados.get('modelo')
    coluna = dados.get('coluna')
    operador = dados.get('operador')
    valor = dados.get('valor')
    page = int(dados.get('page', 1))
    per_page = int(dados.get('per_page', 25))
    per_page = max(1, min(per_page, 200))

    modelo = MODELOS.get(modelo_nome)
    if not modelo:
        return jsonify({'erro': 'Modelo inválido'}), 400

    colunas = [c.name for c in modelo.__table__.columns]
    if coluna not in colunas:
        return jsonify({'erro': 'Coluna inválida'}), 400

    try:
        col = getattr(modelo, coluna)
        tipo_coluna = str(col.property.columns[0].type)
        is_date = "DATE" in tipo_coluna.upper()

        if is_date:
            try:
                valor_dt = datetime.strptime(valor, "%Y-%m-%d").date()
            except Exception:
                return jsonify({"erro": "Data inválida"}), 400

            if operador == '=':
                filtro = func.date(col) == valor_dt
            elif operador == '!=':
                filtro = func.date(col) != valor_dt
            elif operador == '>':
                filtro = func.date(col) > valor_dt
            elif operador == '<':
                filtro = func.date(col) < valor_dt
            else:
                return jsonify({'erro': 'Operador inválido para data'}), 400
        else:
            if operador == '=':
                filtro = col == valor
            elif operador == '!=':
                filtro = col != valor
            elif operador == '>':
                filtro = col > valor
            elif operador == '<':
                filtro = col < valor
            elif operador.upper() == 'LIKE':
                filtro = col.ilike(f"%{valor}%")
            else:
                return jsonify({'erro': 'Operador inválido'}), 400

        query = db.session.query(modelo).filter(filtro).order_by(getattr(modelo, 'id').asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        registros_json = [
            {c: getattr(r, c) for c in colunas}
            for r in pagination.items
        ]

        return jsonify({
            'colunas': colunas,
            'registros': registros_json,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'erro': f'Erro ao filtrar: {str(e)}'}), 500



@database_bp.route('/excluir_varios', methods=['POST'])
@admin_required
def excluir_varios():
    dados = request.json
    modelo_nome = dados.get('modelo')
    ids = dados.get('ids', [])

    modelo = MODELOS.get(modelo_nome)
    if not modelo:
        return jsonify({'erro': 'Modelo inválido'}), 400

    try:
        registros = db.session.query(modelo).filter(modelo.id.in_(ids)).all()
        for registro in registros:
            # 🔹 Caso especial: devolução de estoque se for Pedido
            if modelo.__tablename__ == "pedido":
                if registro.status == 'pendente':
                    for item in registro.itens:
                        produto = Produtos.query.get(item.produto_id)
                        if produto:
                            produto.estoque_produto += item.quantidade

            # Busca e exclui imagem, se houver
            for attr_name in dir(registro):
                if 'imagem' in attr_name.lower():
                    imagem_path = getattr(registro, attr_name, None)
                    if isinstance(imagem_path, str) and imagem_path.strip():
                        caminho_imagem = os.path.join(current_app.static_folder, imagem_path)
                        if os.path.exists(caminho_imagem) and os.path.normpath(imagem_path) != os.path.normpath('uploads/pfp/default.jpg'):
                            os.remove(caminho_imagem)
                    break  # remove apenas a primeira imagem

            db.session.delete(registro)

        db.session.commit()
        return jsonify({'sucesso': True, 'mensagem': f'{len(registros)} registros excluídos.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao excluir: {str(e)}'}), 500