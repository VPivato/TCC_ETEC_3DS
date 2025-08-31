import random
import sys
from datetime import datetime, timedelta
from app.models import Usuarios, Produtos, ItemPedido, Pedido
from app import create_app
from app.extensions import db

def gerar_pedidos_fake(db, quantidade=10):
    usuarios = Usuarios.query.all()
    produtos = Produtos.query.all()

    if not usuarios or not produtos:
        print("Não há usuários ou produtos cadastrados.")
        return

    for _ in range(quantidade):
        usuario = random.choice(usuarios)

        # ----- Distribuição das datas -----
        # Normal em torno de 30 dias atrás, com desvio padrão de 15
        dias_atras = max(0, int(random.gauss(30, 15)))  
        data_pedido = datetime.now() - timedelta(days=dias_atras)

        # ----- Probabilidade de status -----
        status = random.choices(
            ['retirado', 'pendente', 'cancelado'],
            weights=[70, 20, 10],
            k=1
        )[0]

        pedido = Pedido(
            usuario=usuario,
            data_hora=data_pedido,
            status=status,
            total=0
        )

        db.session.add(pedido)
        db.session.flush()

        # ----- Itens do pedido -----
        # Distribuição enviesada para escolher 1 ou 2 produtos com mais frequência
        num_itens = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
        itens_pedido = random.sample(produtos, min(num_itens, len(produtos)))

        total = 0
        for produto in itens_pedido:
            # Quantidade com viés para 1 unidade
            qtd = random.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0]
            item = ItemPedido(
                pedido_id=pedido.id,
                produto=produto,
                quantidade=qtd,
                preco_unitario=float(produto.preco_produto)
            )
            db.session.add(item)
            total += qtd * float(produto.preco_produto)

        pedido.total = total

    db.session.commit()
    print(f"{quantidade} pedidos gerados com sucesso!")


app = create_app()
with app.app_context():
    # pega argumento da linha de comando, senão usa 10 como padrão
    quantidade = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    gerar_pedidos_fake(db, quantidade)