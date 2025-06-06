import os
from flask import Flask
from .extensions import db
from .models import *

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    from .auth.routes import auth_bp
    from .home.routes import home_bp
    from .feedback.routes import feedback_bp
    from .perfil.routes import perfil_bp
    from .notifications.routes import notificacao_bp
    from .admin.database.routes import database_bp
    from .admin.produtos.routes import produto_bp
    from .loja.routes import loja_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(notificacao_bp)
    app.register_blueprint(database_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(loja_bp)

    with app.app_context():
        db.create_all()
    
    return app