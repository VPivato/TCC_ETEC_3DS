import random
import sys
from datetime import datetime, timedelta
from app.models import Usuarios, Produtos, ItemPedido, Pedido
from app import create_app
from app.extensions import db

import random
from datetime import datetime, timedelta
from app.models import Pedido, ItemPedido, Usuarios, Produtos

def gerar_pedidos_fake(db, quantidade=10, batch_size=5000):
    usuarios = Usuarios.query.all()
    produtos = Produtos.query.all()

    if not usuarios or not produtos:
        print("Não há usuários ou produtos cadastrados.")
        return

    pedidos = []
    itens = []

    now = datetime.now()

    for i in range(quantidade):
        usuario = random.choice(usuarios)

        # ----- Datas -----
        dias_atras = max(0, int(random.gauss(30, 15)))
        data_pedido = now - timedelta(days=dias_atras)

        # ----- Status -----
        status = random.choices(
            ['retirado', 'pendente', 'cancelado'],
            weights=[70, 20, 10],
            k=1
        )[0]

        pedido = Pedido(
            id_usuario=usuario.id,
            data_hora=data_pedido,
            status=status,
            total=0
        )

        total = 0
        num_itens = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
        itens_pedido = random.sample(produtos, min(num_itens, len(produtos)))

        for produto in itens_pedido:
            qtd = random.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0]
            item = ItemPedido(
                produto_id=produto.id,   # em vez de produto=produto
                quantidade=qtd,
                preco_unitario=float(produto.preco_produto)
            )
            itens.append((pedido, item))
            total += qtd * float(produto.preco_produto)

        pedido.total = total
        pedidos.append(pedido)

        # ---- Commit em lotes ----
        if (i + 1) % batch_size == 0:
            for pedido, item in itens:
                pedido.itens.append(item)
                db.session.add(pedido)
            db.session.commit()
            pedidos.clear()
            itens.clear()
            print(f"{i+1} pedidos gerados...")

    # Commit final para o restante
    if pedidos:
        for pedido, item in itens:
            pedido.itens.append(item)
            db.session.add(pedido)
        db.session.commit()

    print(f"{quantidade} pedidos gerados com sucesso!")


app = create_app()
with app.app_context():
    # pega argumento da linha de comando, senão usa 10 como padrão
    quantidade = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    gerar_pedidos_fake(db, quantidade)