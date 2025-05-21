from datetime import datetime
from ..extensions import db

class Feedbacks(db.Model):
    __tablename__ = "feedbacks"

    id_feedback = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_feedback = db.Column(db.String(40), nullable=False)
    email_feedback = db.Column(db.String(70), nullable=False)
    tipo_feedback = db.Column(db.String(15), nullable=False)
    texto_feedback = db.Column(db.String(700), nullable=False)
    data_feedback = db.Column(db.DateTime, default=datetime.now)