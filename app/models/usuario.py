from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from ..extensions import db

class Usuarios(db.Model):
    __tablename__ = "usuarios"

    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(40), nullable=False, unique=True)
    email_usuario = db.Column(db.String(70), nullable=False, unique=True)
    codigo_etec_usuario = db.Column(db.String(30), nullable=False)
    hash_senha_usuario = db.Column(db.String(100), nullable=False)
    data_criacao_usuario = db.Column(db.DateTime, default=datetime.now)

    notificacoes_ativas = db.Column(db.Boolean, default=True)
    ultima_notificacao_vista = db.Column(db.Boolean, default=False)

    def set_senha(self, senha):
        self.hash_senha_usuario = generate_password_hash(senha)
    
    def check_senha(self, senha):
        return check_password_hash(self.hash_senha_usuario, senha)
    
    def __repr__(self):
        return f"ID: {self.id_usuario}, Nome: {self.nome_usuario}"