from datetime import datetime
from ..extensions import db

class Notificacoes(db.Model):
    __tablename__ = "notificacoes"

    id = db.Column(db.Integer, primary_key=True)
    titulo_notificacao = db.Column(db.String(50), nullable=False)
    mensagem_notificacao = db.Column(db.String(200), nullable=False)
    data_notificacao = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"ID: {self.id} - MSG: {self.mensagem} - DATA: {self.data.strftime('%d-%m-%Y %H:%M')}"