from app import create_app
from app.extensions import db
from app.models.aluno import Alunos

app = create_app()
with app.app_context():
    alunos = [
        Alunos(
            nome_aluno="Vinicius Pivato de Aragão",
            email_aluno="vinicius.aragao@etec.sp.gov.br",
            codigo_etec_aluno="055",
            descricao_etec="ETEC Prof. Eudécio Luiz Vicente",
            rm_aluno="07282"
        ),
        Alunos(
            nome_aluno="Yasmim da Silva Nascimento",
            email_aluno="yasmim.nascimento@etec.sp.gov.br",
            codigo_etec_aluno="055",
            descricao_etec="ETEC Prof. Eudécio Luiz Vicente",
            rm_aluno="01234"
        )
    ]

    db.session.add_all(alunos)
    db.session.commit()
    print("Alunos inseridos com sucesso!")