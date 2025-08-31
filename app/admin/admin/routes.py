from flask import Blueprint, request, redirect, url_for, flash, render_template
from werkzeug.security import generate_password_hash
from ...extensions import db
from ...models.usuario import Usuarios
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route('/')
@admin_required
def admin():
    return render_template('admin/admin/admin.html')

@admin_bp.route('/cadastrar_admin', methods=["POST"])
@admin_required
def cadastrar_admin():
    etec = request.form.get('etec_admin')
    usuario = request.form.get('usuario_admin')
    senha = request.form.get('senha_admin')
    confirmar = request.form.get('confirmar_senha_admin')

    # Validação das senhas
    if senha != confirmar:
        flash("As senhas não coincidem.", "danger")
        return redirect(url_for('admin.admin'))

    # Verifica se o usuário já existe
    if Usuarios.query.filter_by(codigo_etec_usuario=etec, rm_usuario=usuario).first():
        flash("Este administrador já existe.", "warning")
        return redirect(url_for('admin.admin'))

    # Cria novo admin
    novo_admin = Usuarios(
        aluno_id=None,
        codigo_etec_usuario=etec,
        rm_usuario=usuario,
        hash_senha_usuario=generate_password_hash(senha),
        nivel_conta=1  # Define como admin
    )

    db.session.add(novo_admin)
    db.session.commit()
    
    flash("Administrador cadastrado!.", "success")
    return redirect(url_for('admin.admin'))