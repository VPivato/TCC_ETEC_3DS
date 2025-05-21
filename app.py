# Imports
from flask import Flask, render_template, redirect, request, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Configuração básica do Flask
app = Flask(__name__)
app.secret_key = "my_secret_key"

# Configuração básica do SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banco_de_dados.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Criação do Modelo/Tabela Usuários
class Usuarios(db.Model):
    __tablename__ = "usuarios"

    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(40), nullable=False, unique=True)
    email_usuario = db.Column(db.String(70), nullable=False, unique=True)
    codigo_etec_usuario = db.Column(db.String(30), nullable=False)
    hash_senha_usuario = db.Column(db.String(100), nullable=False)
    data_criacao_usuario = db.Column(db.DateTime, default=datetime.now)

    def set_senha(self, senha):
        self.hash_senha_usuario = generate_password_hash(senha)
    
    def check_senha(self, senha):
        return check_password_hash(self.hash_senha_usuario, senha)
    
    def __repr__(self):
        return f"ID: {self.id_usuario}, Nome: {self.nome_usuario}"


class Feedbacks(db.Model):
    __tablename__ = "feedbacks"

    id_feedback = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_feedback = db.Column(db.String(40), nullable=False)
    email_feedback = db.Column(db.String(70), nullable=False)
    tipo_feedback = db.Column(db.String(15), nullable=False)
    texto_feedback = db.Column(db.String(700), nullable=False)
    data_feedback = db.Column(db.DateTime, default=datetime.now)


# Rota Tela de Login/Cadastro
@app.route('/')
def login():
    return render_template('login.html')


# Rota para entrar
@app.route('/entrar', methods=["POST"])
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
        return redirect(url_for("home")) # Direciona para página Home
    # Se não existir
    else:
        flash("Usuário não cadastrado" if not usuario_bd else None)
        flash(("Senha incorreta" if usuario_bd.check_senha(senha) != senha else None) if usuario_bd else None)
        return redirect("/")

# Rota para registrar
@app.route('/registrar', methods=["POST"])
def registrar():
    # Coletar informação do formulário registrar
    email = request.form["email-registrar"]
    codigo = request.form["codigo-registrar"]
    nome = request.form["nome-registrar"]
    senha = request.form["senha-registrar"]
    nome_cadastrado = True if Usuarios.query.filter_by(nome_usuario=nome).first() else False # Verifica se nome existe no BD
    email_cadastrado = True if Usuarios.query.filter_by(email_usuario=email).first() else False # Verifica se email existe no BD

    if nome_cadastrado or email_cadastrado:
        return redirect(url_for("login"))
    else:
        novo_usuario = Usuarios(nome_usuario=nome, email_usuario=email, codigo_etec_usuario=codigo) # Define usuario para adicionar
        novo_usuario.set_senha(senha) # Criptografa a senha e manda para o BD
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            session["username"] = nome
            session["email"] = email
            return redirect(url_for("home")) # Redireciona para pagina Home
        except Exception as e:
            return f"ERROR: {e}"


# Rota Home, depois de entrar ou registrar com sucesso
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/feedback')
def feedback():
    return render_template("feedback.html")

@app.route('/perfil')
def perfil():
    return render_template("perfil.html")

@app.route('/sair')
def sair():
    session.clear()
    return redirect(url_for("login"))

@app.route('/excluir_perfil', methods=["POST"])
def excluir_perfil():
    email = session['email']
    usuario = Usuarios.query.filter_by(email_usuario=email).first()

    if usuario:
        try:
            db.session.delete(usuario)
            db.session.commit()
            session.clear()
            flash("Seu perfil foi excluido com sucesso.", "sucesso")
            return redirect(url_for("login"))
        except Exception as e:
            return f"ERROR: {e}"

@app.route('/enviar_feedback', methods=["POST"])
def enviar_feedback():
    if request.method == "POST":
        nome_feedback = request.form["nome_feedback"]
        email_feedback = request.form["email_feedback"]
        tipo_feedback = request.form["tipo_feedback"]
        texto_feedback = request.form["texto_feedback"]
        novo_feedback = Feedbacks(nome_feedback=nome_feedback, email_feedback=email_feedback, tipo_feedback=tipo_feedback, texto_feedback=texto_feedback)
        try:
            db.session.add(novo_feedback)
            db.session.commit()
            return "Duvida/Reclamação enviada com sucesso!"
        except Exception as e:
            return f"Error: {e}"


@app.route('/database_feedbacks')
def database_feedbacks():
    feedbacks = Feedbacks.query.order_by(Feedbacks.id_feedback).all()
    return render_template("database_feedbacks.html", feedbacks=feedbacks)

@app.route('/database_feedbacks/excluir_feedback/<int:id>')
def excluir_feedback(id:int):
    excluir_feedback = Feedbacks.query.get_or_404(id)
    try:
        db.session.delete(excluir_feedback)
        db.session.commit()
        return redirect(url_for("database_feedbacks"))
    except Exception as e:
        return f"Error: {e}"

# Rota para ver o conteudo da tabela Usuarios
@app.route('/database')
def database():
    usuarios = Usuarios.query.order_by(Usuarios.id_usuario).all()
    return render_template('database.html', usuarios=usuarios)

# Rota para excluir valores do BD
@app.route('/database/excluir_usuario/<int:id>')
def excluir_usuario(id:int):
    excluir_usuario = Usuarios.query.get_or_404(id) # Usuario para excluir
    try:
        db.session.delete(excluir_usuario)
        db.session.commit()
        return redirect(url_for("database"))
    except Exception as e:
        return f"ERROR: {e}"



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)