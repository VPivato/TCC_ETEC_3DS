from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from ..models.usuario import Usuarios
from ..extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/")

# Rota Tela de Login/Cadastro
@auth_bp.route('/')
def login():
    return render_template('auth/login.html')

# Rota para entrar
@auth_bp.route('/entrar', methods=["POST"])
def entrar():
    # Coletar informações do formulário entrar
    codigo = request.form["codigo-entrar"]
    nome = request.form["nome-entrar"]
    senha = request.form["senha-entrar"]
    usuario_bd = Usuarios.query.filter_by(nome_usuario=nome).first() # Verifica se usuario existe no BD, se não, retorna None
    codigo_bd = usuario_bd.codigo_etec_usuario if usuario_bd else None # Pega o codigo do usuario se ele existir, se não, retorna None

    # Se usuario existir, senha descriptografada coincidir com a digitada, e codigo estiver correto
    if usuario_bd and usuario_bd.check_senha(senha) and codigo_bd == codigo:
        session['username'] = nome
        session["email"] = usuario_bd.email_usuario
        return redirect(url_for("home.home")) # Direciona para página Home
    # Se não existir
    else:
        flash("Usuário não cadastrado" if not usuario_bd else None)
        flash(("Senha incorreta" if usuario_bd.check_senha(senha) != senha else None) if usuario_bd else None)
        return redirect("/")

# Rota para registrar
@auth_bp.route('/registrar', methods=["POST"])
def registrar():
    # Coletar informação do formulário registrar
    email = request.form["email-registrar"]
    codigo = request.form["codigo-registrar"]
    nome = request.form["nome-registrar"]
    senha = request.form["senha-registrar"]
    nome_cadastrado = True if Usuarios.query.filter_by(nome_usuario=nome).first() else False # Verifica se nome existe no BD
    email_cadastrado = True if Usuarios.query.filter_by(email_usuario=email).first() else False # Verifica se email existe no BD

    if nome_cadastrado or email_cadastrado:
        return redirect(url_for("auth.login"))
    else:
        novo_usuario = Usuarios(nome_usuario=nome, email_usuario=email, codigo_etec_usuario=codigo) # Define usuario para adicionar
        novo_usuario.set_senha(senha) # Criptografa a senha e manda para o BD
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            session["username"] = nome
            session["email"] = email
            return redirect(url_for("home.home")) # Redireciona para pagina Home
        except Exception as e:
            return f"ERROR: {e}"