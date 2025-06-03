from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from sqlalchemy import func
from datetime import datetime
from ..models.usuario import Usuarios
from ..models.notificacao import Notificacoes
from ..models.feedback import Feedbacks
from ..extensions import db

database_bp = Blueprint("database", __name__, url_prefix="/database")

MODELOS = {
    'Usuarios': Usuarios,
    "Notificacoes": Notificacoes,
    "Feedbacks": Feedbacks
}

@database_bp.route('/', methods=["POST", "GET"])
def database():
    return render_template("admin/database/database.html", modelos=MODELOS.keys())



@database_bp.route('/get_colunas', methods=['POST'])
def get_colunas():
    nome_modelo = request.json.get("modelo")
    modelo = MODELOS.get(nome_modelo)
    if not modelo:
        return jsonify({'erro': 'Modelo não encontrado'}), 400
    colunas = [col.name for col in modelo.__table__.columns]
    return jsonify(colunas)



@database_bp.route('/get_registros', methods=['POST'])
def get_registros():
    nome_modelo = request.json.get('modelo')
    modelo = MODELOS.get(nome_modelo)

    if not modelo:
        return jsonify({'erro': 'Modelo não encontrado'}), 400

    colunas = [col.name for col in modelo.__table__.columns]
    registros = db.session.query(modelo).all()

    # Converte para lista de dicionários
    registros_json = [
        {col: getattr(r, col) for col in colunas}
        for r in registros
    ]

    return jsonify({
        'colunas': colunas,
        'registros': registros_json
    })



@database_bp.route('/excluir/<modelo>/<int:id>', methods=['POST'])
def excluir_registro(modelo, id):
    modelo_classe = MODELOS.get(modelo)
    if not modelo_classe:
        return jsonify({'erro': 'Modelo inválido'}), 400

    registro = db.session.get(modelo_classe, id)
    if not registro:
        return jsonify({'erro': 'Registro não encontrado'}), 404

    try:
        db.session.delete(registro)
        db.session.commit()
        return jsonify({'sucesso': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao excluir: {str(e)}'}), 500



@database_bp.route('/filtrar', methods=['POST'])
def filtrar():
    dados = request.json
    modelo_nome = dados.get('modelo')
    coluna = dados.get('coluna')
    operador = dados.get('operador')
    valor = dados.get('valor')

    modelo = MODELOS.get(modelo_nome)
    if not modelo:
        return jsonify({'erro': 'Modelo inválido'}), 400

    if coluna not in [c.name for c in modelo.__table__.columns]:
        return jsonify({'erro': 'Coluna inválida'}), 400

    try:
        col = getattr(modelo, coluna)
        tipo_coluna = str(col.property.columns[0].type)
        is_date = "DATE" in tipo_coluna.upper()
        if is_date:
            try:
                valor_dt = datetime.strptime(valor, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"erro": "Data inválida"}), 400
            
            # Usa func.date para comparar apenas a data (sem hora)
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
            # Filtros normais para texto/número
            if operador == '=':
                filtro = col == valor
            elif operador == '!=':
                filtro = col != valor
            elif operador == '>':
                filtro = col > valor
            elif operador == '<':
                filtro = col < valor
            elif operador.upper() == 'LIKE':
                filtro = col.like(f"%{valor}%")
            else:
                return jsonify({'erro': 'Operador inválido'}), 400

        registros = db.session.query(modelo).filter(filtro).all()
        colunas = [c.name for c in modelo.__table__.columns]

        return jsonify({
            'colunas': colunas,
            'registros': [
                {col: getattr(r, col) for col in colunas}
                for r in registros
            ]
        })
    except Exception as e:
        return jsonify({'erro': f'Erro ao filtrar: {str(e)}'}), 500