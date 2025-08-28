import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename

from ...models.produto import Produtos, categoriasProduto
from ...extensions import db

from utils.decorators import admin_required

produto_bp = Blueprint("produto", __name__, url_prefix="/produto")

@produto_bp.route('/', methods=['POST', 'GET'])
@admin_required
def produto():
    colunas_produto = Produtos.__table__.columns.keys()
    registros_produto = Produtos.query.order_by(Produtos.id).all()
    return render_template('admin/produto/cadastro-produto.html', categorias=categoriasProduto, colunas=colunas_produto, registros=registros_produto)

@produto_bp.route('/cadastrar', methods=['POST'])
@admin_required
def cadastrar():
    try:
        file = request.files['imagem']

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = "default.png"

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



@produto_bp.route('/excluir/<int:id>', methods=['POST', 'GET'])
@admin_required
def excluir_produto(id):
    produto = Produtos.query.get_or_404(id)
    try:
        if produto.imagem_produto:  # Ex: 'uploads/imagem.jpg'
            caminho_imagem = os.path.join(current_app.static_folder, produto.imagem_produto)
            if os.path.exists(caminho_imagem): # Verifica se o arquivo existe e remove
                os.remove(caminho_imagem)
        db.session.delete(produto)
        db.session.commit()
        return redirect(url_for('produto.produto'))
    except Exception as e:
        db.session.rollback()
        return f"ERROR: {e}"



@produto_bp.route('/editar/<int:id>', methods=['POST', 'GET'])
@admin_required
def editar_produto(id):
    produto = Produtos.query.get_or_404(id)

    try:
        produto.descricao_produto = request.form.get('descricao')
        produto.categoria_produto = request.form.get('categoria').upper()
        produto.preco_produto = request.form.get('preco')
        produto.estoque_produto = request.form.get('estoque')

        imagem = request.files.get('imagem')

        if imagem and imagem.filename != '':
            filename = secure_filename(imagem.filename)
            # Cria pasta se não existir
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            # Caminho completo para salvar
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            imagem.save(filepath)
            produto.imagem_produto = f'uploads/{filename}'
        
        db.session.commit()
        return redirect(url_for('produto.produto'))
    except Exception as e:
        db.session.rollback()
        return f"ERROR: {e}"



@produto_bp.route('/cadastrar-multiplos', methods=['POST'])
def cadastrar_multiplos():
    if not request.is_json:
        return {"error": "Conteúdo deve ser JSON"}, 400

    produtos_data = request.get_json()

    try:
        novos_produtos = []
        for item in produtos_data:
            novo = Produtos(
                descricao_produto=item['descricao_produto'],
                categoria_produto=item['categoria_produto'].upper(),
                preco_produto=float(item['preco_produto']),
                estoque_produto=int(item['estoque_produto']),
                imagem_produto='uploads/' + item.get('imagem_produto', 'default.png')
            )
            novos_produtos.append(novo)

        db.session.add_all(novos_produtos)
        db.session.commit()

        return {"message": f"{len(novos_produtos)} produtos cadastrados com sucesso"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500