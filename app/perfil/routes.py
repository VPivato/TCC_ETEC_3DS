from flask import Blueprint, render_template, session, redirect, url_for, flash
from ..models.usuario import Usuarios
from ..extensions import db

perfil_bp = Blueprint("perfil", __name__, url_prefix="/perfil")

@perfil_bp.route('/perfil')
def perfil():
    return render_template("perfil/perfil.html")

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