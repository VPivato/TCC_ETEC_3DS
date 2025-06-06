from ..extensions import db

categoriasProduto = ["Salgado", "Doce", "Bebida"]

class Produtos(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    descricao_produto = db.Column(db.String(40), nullable=False)
    categoria_produto = db.Column(db.String(15), nullable=False)
    preco_produto = db.Column(db.Numeric(5, 2), nullable=False)
    estoque_produto = db.Column(db.Integer, nullable=False)
    imagem_produto = db.Column(db.String(255), nullable=True)