from flask import Blueprint, render_template, request, redirect, url_for
from ..extensions import socketio
from ..extensions import db
from ..models.notificacao import Notificacoes

notificacao_bp = Blueprint("notificacao", __name__, url_prefix="/notificacao")

@notificacao_bp.route('/')
def controle_notificacao():
    notificacoes = Notificacoes.query.order_by(Notificacoes.data.desc()).all()
    return render_template ("admin/notifications/controle_notificacao.html", notificacoes=notificacoes)

@notificacao_bp.route("/enviar", methods=["POST"])
def enviar():
    if request.method == "POST":
        mensagem = request.form["mensagem-notificacao"]
        nova_notificacao = Notificacoes(mensagem=mensagem)
        db.session.add(nova_notificacao)
        db.session.commit()
        socketio.emit("nova_notificacao", {"mensagem": nova_notificacao.mensagem})
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