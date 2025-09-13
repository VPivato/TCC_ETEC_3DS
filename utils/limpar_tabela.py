import sys
from app import create_app, db
from app import models

def limpar_registros(db):
    if len(sys.argv) < 2:
        print("Uso: py -m utils.limpar_tabela <NomeDaTabela>")
        sys.exit(1)

    nome_tabela = sys.argv[1]
    Model = getattr(models, nome_tabela, None)

    if Model is None:
        print(f"Modelo '{nome_tabela}' não encontrado em app.models")
        sys.exit(1)

    try:
        if nome_tabela == 'Pedido':
            db.session.query(models.ItemPedido).delete(synchronize_session=False)
            num_registros = db.session.query(models.Pedido).delete(synchronize_session=False)
            print(f"{num_registros} registros da tabela '{nome_tabela}' foram excluídos.")
        else:
            num_registros = db.session.query(Model).delete(synchronize_session=False)
            print(f"{num_registros} registros da tabela '{nome_tabela}' foram excluídos.")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir registros: {e}")

app = create_app()
with app.app_context():
    limpar_registros(db)