from datetime import datetime
from ..extensions import db

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.now)
    data_retirada = db.Column(db.DateTime, nullable=True)
    total = db.Column(db.Float, nullable=False)
    rm_aluno = db.Column(db.String(20), nullable=False)

    status = db.Column(db.String(20), default='pendente')  
    # opções: 'pendente', 'retirado', 'cancelado'

    itens = db.relationship('ItemPedido', backref='pedido', cascade="all, delete-orphan")