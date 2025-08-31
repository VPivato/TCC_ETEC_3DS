from app import create_app
from app.extensions import db
from app.models import Usuarios
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = Usuarios(
        codigo_etec_usuario='000',
        rm_usuario='admin',
        hash_senha_usuario=generate_password_hash('1234'),
        nivel_conta=1
    )
    
    db.session.add(admin)
    db.session.commit()
    print('Admin adicionado com sucesso')