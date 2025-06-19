class Config:
    SECRET_KEY = "my_secret_key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///banco_de_dados.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'app/static/uploads/'
    UPLOAD_FOLDER_PRODUTOS = 'app/static/uploads/produtos'
    UPLOAD_FOLDER_PFP = 'app/static/uploads/pfp'