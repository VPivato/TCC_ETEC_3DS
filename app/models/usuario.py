from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from ..extensions import db

class Usuarios(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('alunos.id'), nullable=False)
    hash_senha_usuario = db.Column(db.String(100), nullable=False)
    data_criacao_usuario = db.Column(db.DateTime, default=datetime.now)
    imagem_usuario = db.Column(db.String(255), nullable=True, default='uploads/pfp/default.jpg')
    nivel_conta = db.Column(db.Integer, default=0, nullable=False)
    conta_ativa = db.Column(db.String(3), nullable=True, default='sim')

    aluno = db.relationship("Alunos", backref="usuario", uselist=False)

    notificacoes_ativas = db.Column(db.Boolean, default=True)
    ultima_notificacao_vista = db.Column(db.Boolean, default=False)

    def set_senha(self, senha):
        self.hash_senha_usuario = generate_password_hash(senha)
    
    def check_senha(self, senha):
        return check_password_hash(self.hash_senha_usuario, senha)
    
    def __repr__(self):
        return f"ID: {self.id_usuario}, Nome: {self.nome_usuario}"