from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from ..extensions import db
from ..models.notificacao import Notificacoes
from ..models.usuario import Usuarios

notificacao_bp = Blueprint("notificacao", __name__, url_prefix="/notificacao")

@notificacao_bp.route('/')
def controle_notificacao():
    notificacoes = Notificacoes.query.order_by(Notificacoes.data.desc()).all()
    return render_template ("admin/notifications/controle_notificacao.html", notificacoes=notificacoes)

@notificacao_bp.route("/enviar", methods=["POST"])
def enviar():
    if request.method == "POST":
        Usuarios.query.update({Usuarios.ultima_notificacao_vista: False})
        mensagem = request.form["mensagem-notificacao"]
        nova_notificacao = Notificacoes(mensagem=mensagem)
        db.session.add(nova_notificacao)
        db.session.commit()
    return redirect(url_for("notificacao.controle_notificacao"))

@notificacao_bp.route('/excluir/<int:id>')
def excluir(id:int):
    excluir_notificacao = Notificacoes.query.get_or_404(id)
    try:
        db.session.delete(excluir_notificacao)
        db.session.commit()
        return redirect(url_for("notificacao.controle_notificacao"))
    except Exception as e:
        return f"ERROR: {e}"

@notificacao_bp.route('/marcar_como_vista', methods=["POST", "GET"])
def marcar_como_vista():
    user = Usuarios.query.filter_by(email_usuario=session["email"]).first()
    if user:
        user.ultima_notificacao_vista = True
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@notificacao_bp.route('/atualizar_notificacoes', methods=['POST'])
def atualizar_notificacoes():
    data = request.get_json()
    estado = data.get('notificacoes_ativas')

    usuario = Usuarios.query.filter_by(email_usuario=session["email"]).first()
    if usuario:
        usuario.notificacoes_ativas = estado
        db.session.commit()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'erro', 'mensagem': 'Usuário não encontrado'}), 404