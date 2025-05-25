from datetime import datetime
from ..extensions import db

class Notificacoes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensagem = db.Column(db.String(200), nullable=False)
    data = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"ID: {self.id} - MSG: {self.mensagem} - DATA: {self.data.strftime('%d-%m-%Y %H:%M')}"