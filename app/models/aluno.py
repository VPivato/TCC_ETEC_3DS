from ..extensions import db

class Alunos(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_aluno = db.Column(db.String(70), nullable=False, unique=True)
    email_aluno = db.Column(db.String(70), nullable=False, unique=True)
    codigo_etec_aluno = db.Column(db.String(5), nullable=False)
    descricao_etec = db.Column(db.String(70), nullable=False)
    rm_aluno = db.Column(db.String(10), nullable=False)