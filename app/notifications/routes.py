from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from ..extensions import db
from ..models.notificacao import Notificacoes
from ..models.usuario import Usuarios
from utils.decorators import admin_required

notificacao_bp = Blueprint("notificacao", __name__, url_prefix="/notificacao")

@notificacao_bp.route('/', methods=['POST', 'GET'])
@admin_required
def controle_notificacao():
    colunas = Notificacoes.__table__.columns.keys()
    registros = Notificacoes.query.order_by(Notificacoes.data_notificacao.desc()).all()
    return render_template ("admin/notifications/controle_notificacao.html", colunas=colunas, registros=registros)



@notificacao_bp.route("/enviar", methods=["POST"])
@admin_required
def enviar():
    if request.method == "POST":
        Usuarios.query.update({Usuarios.ultima_notificacao_vista: False})
        titulo = request.form['titulo-notificacao']
        mensagem = request.form["mensagem-notificacao"]
        nova_notificacao = Notificacoes(titulo_notificacao=titulo, mensagem_notificacao=mensagem)
        db.session.add(nova_notificacao)
        db.session.commit()
    return redirect(url_for("notificacao.controle_notificacao"))



@notificacao_bp.route('/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_notificacao(id:int):
    excluir_notificacao = Notificacoes.query.get_or_404(id)
    try:
        db.session.delete(excluir_notificacao)
        db.session.commit()
        return redirect(url_for("notificacao.controle_notificacao"))
    except Exception as e:
        db.session.rollback()
        return f"ERROR: {e}"



@notificacao_bp.route('/editar/<int:id>', methods=['POST', 'GET'])
@admin_required
def editar_notificacao(id):
    notificacao = Notificacoes.query.get_or_404(id)

    try:
        notificacao.mensagem_notificacao = request.form.get('mensagem')
        db.session.commit()
        return redirect(url_for('notificacao.controle_notificacao'))
    except Exception as e:
        db.session.rollback()
        return f"ERROR: {e}"



@notificacao_bp.route('/marcar_como_vista', methods=["POST", "GET"])
@admin_required
def marcar_como_vista():
    user = Usuarios.query.get(session['user_id'])
    if user:
        user.ultima_notificacao_vista = True
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400



@notificacao_bp.route('/atualizar_notificacoes', methods=['POST'])
@admin_required
def atualizar_notificacoes():
    data = request.get_json()
    estado = data.get('notificacoes_ativas')

    usuario = Usuarios.query.get(session['user_id'])
    if usuario:
        usuario.notificacoes_ativas = estado
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'erro', 'mensagem': 'Usuário não encontrado'}), 404