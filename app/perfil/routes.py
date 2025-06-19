import os
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from ..models.usuario import Usuarios
from ..models.notificacao import Notificacoes
from ..extensions import db

perfil_bp = Blueprint("perfil", __name__, url_prefix="/perfil")

@perfil_bp.route('/')
def perfil():
    notificacoes = Notificacoes.query.order_by(Notificacoes.data_notificacao.desc()).all()
    return render_template("perfil/perfil.html", notificacoes=notificacoes, header_mode='perfil')



@perfil_bp.route('/upload_pfp', methods=['POST'])
def upload_pfp():
    try:
        file = request.files['foto_perfil']

        if file and file.filename != '':
            usuario = Usuarios.query.get(session['user_id'])
            if not usuario:
                return redirect(url_for('perfil.perfil'))

            # Monta o nome do arquivo no padrão: id_codigoetec_rm.jpg
            ext = file.filename.rsplit('.', 1)[1].lower()  # Extrai extensão (jpg, png, etc.)
            filename = f"{usuario.id}_{usuario.codigo_etec_usuario}_{usuario.nome_usuario}_{datetime.now().strftime('%M-%S')}.{ext}"
            filename = secure_filename(filename)  # Garante nome seguro

            # Caminho para salvar
            upload_folder = current_app.config['UPLOAD_FOLDER_PFP']
            os.makedirs(upload_folder, exist_ok=True)

            caminho_salvar = os.path.join(upload_folder, filename)

            file.save(caminho_salvar)

            # Redimensiona para evitar imagens grandes
            try:
                from PIL import Image

                with Image.open(caminho_salvar) as img:
                    img = img.convert("RGB")
                    img.thumbnail((300, 300))  # Limita para 500x500
                    img.save(caminho_salvar, format='JPEG', quality=85)
            except Exception as e:
                os.remove(caminho_salvar)  # Remove imagem inválida
                return redirect(url_for('perfil.perfil'))

            usuario = Usuarios.query.get(session['user_id'])
            if usuario:
                caminho_antigo = os.path.join(
                    current_app.root_path, 'static', usuario.imagem_usuario
                )

                # Se não for a imagem padrão e se o arquivo existir, remove
                if (
                    usuario.imagem_usuario != 'uploads/pfp/default.jpg'
                    and os.path.exists(caminho_antigo)
                ):
                    os.remove(caminho_antigo)

                # Atualiza o caminho da nova imagem
                usuario.imagem_usuario = f'uploads/pfp/{filename}'

                db.session.commit()

                return redirect(url_for('perfil.perfil'))

        else:
            return redirect(url_for('perfil.perfil'))

    except Exception as e:
        return redirect(url_for('perfil.perfil'))



@perfil_bp.route('/sair')
def sair():
    session.clear()
    return redirect(url_for("auth.login"))



@perfil_bp.route('/excluir_perfil', methods=["POST"])
def excluir_perfil():
    usuario = Usuarios.query.get(session['user_id'])
    if usuario:
        try:
            # Verifica se a foto não é a padrão antes de excluir
            if usuario.imagem_usuario != 'uploads/pfp/default.jpg':
                caminho_arquivo = os.path.join(
                    current_app.root_path, 'static', usuario.imagem_usuario
                )
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
            db.session.delete(usuario)
            db.session.commit()
            session.clear()
            return redirect(url_for("auth.login"))
        except Exception as e:
            return f"ERROR: {e}"