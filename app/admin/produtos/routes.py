import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from ...models.produto import Produtos, categoriasProduto
from ...extensions import db

produto_bp = Blueprint("produto", __name__, url_prefix="/produto")

@produto_bp.route('/')
def produto():
    return render_template('admin/produto/cadastro-produto.html', categorias=categoriasProduto)

@produto_bp.route('/cadastrar', methods=['POST'])
def cadastrar():
    try:
        file = request.files['imagem']
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        novo_produto = Produtos(
            descricao_produto=request.form['descricao'],
            categoria_produto=request.form['categoria'].upper(),
            preco_produto=float(request.form['preco']),
            estoque_produto=int(request.form['estoque']),
            imagem_produto='uploads/' + filename
        )
        db.session.add(novo_produto)
        db.session.commit()

        return redirect('/produto')
    except Exception as e:
        return f"ERROR: {e}"