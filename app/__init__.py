from flask import Flask
from .extensions import db
from .models import *

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    from .auth.routes import auth_bp
    from .home.routes import home_bp
    from .feedback.routes import feedback_bp
    from .perfil.routes import perfil_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(perfil_bp)

    with app.app_context():
        db.create_all()
    
    return app