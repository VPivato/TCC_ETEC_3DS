from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from ..models.usuario import Usuarios
from ..extensions import db
from ..models import Alunos

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route('/')
def login():
    return render_template('auth/login.html')

# Rota para entrar
@auth_bp.route('/entrar', methods=["POST"])
def entrar():
    codigo_etec = request.form.get("codigo_etec_entrar")
    rm = request.form.get("rm_entrar")
    senha = request.form.get("senha_entrar")

    # Buscar aluno pelo código e RM
    aluno = Alunos.query.filter_by(
        codigo_etec_aluno=codigo_etec,
        rm_aluno=rm
    ).first()

    if not aluno:
        flash("Código ETEC ou RM inválidos.", "danger")
        return redirect(url_for("auth.login"))

    # Verificar se esse aluno já possui conta
    usuario = Usuarios.query.filter_by(aluno_id=aluno.id).first()
    if not usuario:
        flash("Este aluno ainda não possui conta cadastrada.", "warning")
        return redirect(url_for("auth.login"))
    
    if usuario.conta_ativa != "sim":
        flash("Esta conta está desativada. Crie uma nova conta ou contate o suporte.", "danger")
        return redirect(url_for("auth.login"))

    # Verificar senha
    if not usuario.check_senha(senha):
        flash("Senha incorreta.", "danger")
        return redirect(url_for("auth.login"))

    # Login bem-sucedido → salvar na sessão
    session["user_id"] = usuario.id
    return redirect(url_for("home.home"))


# Rota para registrar
@auth_bp.route('/registrar', methods=["POST"])
def registrar():
    codigo_etec = request.form.get("codigo_etec")
    rm = request.form.get("rm")
    senha = request.form.get("senha")
    confirmar = request.form.get("confirmar")

    if senha != confirmar:
        flash("As senhas devem ser iguais.", "danger")
        return redirect(url_for("auth.login"))

    aluno = Alunos.query.filter_by(
        codigo_etec_aluno=codigo_etec,
        rm_aluno=rm
    ).first()

    if not aluno:
        flash("Código ETEC ou RM inválidos.", "danger")
        return redirect(url_for("auth.login"))

    usuario = Usuarios.query.filter_by(aluno_id=aluno.id).first()
    if usuario:
        if usuario.conta_ativa == "sim":
            flash("Este aluno já possui uma conta registrada.", "warning")
            return redirect(url_for("auth.login"))
        else:
            # Reativar conta desativada
            usuario.set_senha(senha)
            usuario.conta_ativa = "sim"
            db.session.commit()
            flash("Conta reativada com sucesso! Agora você pode fazer login.", "success")
            return redirect(url_for("auth.login"))

    # Criar usuário novo
    novo_usuario = Usuarios(aluno_id=aluno.id)
    novo_usuario.set_senha(senha)
    db.session.add(novo_usuario)
    db.session.commit()

    flash("Conta criada com sucesso! Agora você pode fazer login.", "success")
    return redirect(url_for("auth.login"))