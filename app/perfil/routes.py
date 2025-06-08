from flask import Blueprint, render_template, session, redirect, url_for
from ..models.usuario import Usuarios
from ..models.notificacao import Notificacoes
from ..extensions import db

perfil_bp = Blueprint("perfil", __name__, url_prefix="/perfil")

@perfil_bp.route('/')
def perfil():
    user = Usuarios.query.filter_by(email_usuario=session["email"]).first()
    notificacoes = Notificacoes.query.order_by(Notificacoes.data_notificacao.desc()).all()
    return render_template("perfil/perfil.html", notificacoes=notificacoes, user=user, header_mode='perfil')

@perfil_bp.route('/sair')
def sair():
    session.clear()
    return redirect(url_for("auth.login"))

@perfil_bp.route('/excluir_perfil', methods=["POST"])
def excluir_perfil():
    email = session['email']
    usuario = Usuarios.query.filter_by(email_usuario=email).first()

    if usuario:
        try:
            db.session.delete(usuario)
            db.session.commit()
            session.clear()
            return redirect(url_for("auth.login"))
        except Exception as e:
            return f"ERROR: {e}"