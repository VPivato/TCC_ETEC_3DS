from datetime import datetime
from ..extensions import db

class Pedido(db.Model):
    __tablename__ = "pedido"

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    data_hora = db.Column(db.DateTime, default=datetime.now)
    data_retirada = db.Column(db.DateTime, nullable=True)
    data_cancelamento = db.Column(db.DateTime, nullable=True)
    total = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(20), default='pendente')  
    # opções: 'pendente', 'retirado', 'cancelado'

    itens = db.relationship(
        'ItemPedido',
        backref='pedido',
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    usuario = db.relationship('Usuarios', backref='pedidos')