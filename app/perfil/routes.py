import os
from flask import Blueprint, render_template, session, redirect, url_for, request, current_app, send_file, abort, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from ..models.usuario import Usuarios
from ..models.notificacao import Notificacoes
from ..models.pedido import Pedido
from ..extensions import db

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import io

perfil_bp = Blueprint("perfil", __name__, url_prefix="/perfil")

@perfil_bp.route('/')
def perfil():
    usuario_id = session.get('user_id')
    if not usuario_id:
        return redirect(url_for('auth.login'))

    pedidos = Pedido.query.filter_by(id_usuario=usuario_id).order_by(Pedido.data_hora.desc()).all()
    notificacoes = Notificacoes.query.order_by(Notificacoes.data_notificacao.desc()).all()
    return render_template("perfil/perfil.html", notificacoes=notificacoes, pedidos=pedidos, header_mode='perfil')



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
            filename = f"{usuario.id}_{usuario.codigo_etec_usuario}_{usuario.rm_usuario}_{datetime.now().strftime('%M-%S')}.{ext}"
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



@perfil_bp.route('/comprovante/<int:pedido_id>')
def baixar_comprovante(pedido_id):
    usuario_id = session.get('user_id')
    if not usuario_id:
        return redirect(url_for('auth.login'))

    pedido = Pedido.query.filter_by(id=pedido_id, id_usuario=usuario_id).first()
    if not pedido:
        abort(404, description="Pedido não encontrado")

    usuario = Usuarios.query.get(usuario_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle('custom', fontSize=11, leading=14)
    elementos = []

    # Logotipo
    try:
        logo = Image('app/static/images/shared/favicon.png', width=2*cm, height=2*cm)
        elementos.append(logo)
    except:
        pass

    # Nome da cantina
    elementos.append(Paragraph("<strong>FoodPay - Comprovante de Pedido</strong>", styles['Title']))
    elementos.append(Spacer(1, 12))

    # Dados do pedido
    elementos.append(Paragraph(f"Pedido nº: <strong>{pedido.id}</strong>", custom_style))
    elementos.append(Paragraph(f"Data do pedido: <strong>{pedido.data_hora.strftime('%d/%m/%Y %H:%M')}</strong>", custom_style))
    elementos.append(Paragraph(f"Status: <strong>{pedido.status.title()}</strong>", custom_style))
    elementos.append(Spacer(1, 12))

    # Tabela de itens
    dados_tabela = [['Qtd', 'Produto', 'Preço unitário', 'Subtotal']]

    for item in pedido.itens:
        produto = item.produto
        subtotal = item.quantidade * item.preco_unitario
        dados_tabela.append([
            str(item.quantidade),
            produto.descricao_produto,
            f"R$ {item.preco_unitario:.2f}",
            f"R$ {subtotal:.2f}"
        ])

    tabela = Table(dados_tabela, hAlign='LEFT', colWidths=[2*cm, 8*cm, 4*cm, 4*cm])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 12))

    # Total
    elementos.append(Paragraph(f"<strong>Total geral:</strong> R$ {pedido.total:.2f}", styles['Heading2']))
    elementos.append(Spacer(1, 24))

    # Rodapé
    elementos.append(Paragraph(f"Etec: {usuario.codigo_etec_usuario}", custom_style))
    elementos.append(Paragraph(f"RM: {usuario.rm_usuario}", custom_style))
    if usuario.nivel_conta == 0:
        elementos.append(Paragraph(f"Nome: {usuario.aluno.nome_aluno}", custom_style))
        elementos.append(Paragraph(f"E-mail: {usuario.aluno.email_aluno}", custom_style))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("Obrigado por comprar com FoodPay! Esperamos vê-lo novamente em breve.", custom_style))

    doc.build(elementos)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"comprovante_pedido_{pedido.id}.pdf",
        mimetype='application/pdf'
    )


@perfil_bp.route("/estatisticas-usuario", methods=["POST"])
def estatisticas_usuario():
    dados = request.get_json()
    user_id = session.get('user_id')  # id do usuário logado
    periodo = dados.get('periodo', 'este_mes')

    if not user_id:
        return jsonify({"erro": "Usuário não autenticado."}), 401

    # --- Ajuste do período ---
    now = datetime.now()
    if periodo == 'esta_semana':
        data_inicio = now - timedelta(days=now.weekday())  # segunda-feira
    elif periodo == 'este_mes':
        data_inicio = datetime(now.year, now.month, 1)
    elif periodo == 'comeco_ano':
        data_inicio = datetime(now.year, 1, 1)
    else:
        data_inicio = datetime(now.year, 1, 1)  # fallback
    data_inicio = data_inicio.replace(hour=0, minute=0, second=0)
    data_fim = now.replace(hour=23, minute=59, second=59)

    # --- Pedidos do usuário no período ---
    pedidos = Pedido.query.filter(
        Pedido.id_usuario == user_id,
        Pedido.status == 'retirado',
        Pedido.data_hora >= data_inicio,
        Pedido.data_hora <= data_fim
    ).all()

    total_pedidos = len(pedidos)
    total_gasto = sum(p.total for p in pedidos)
    media_pedido = total_gasto / total_pedidos if total_pedidos > 0 else 0

    # --- Top 3 produtos mais comprados ---
    produtos_count = {}
    for p in pedidos:
        for item in p.itens:
            if item.produto.descricao_produto in produtos_count:
                produtos_count[item.produto.descricao_produto] += item.quantidade
            else:
                produtos_count[item.produto.descricao_produto] = item.quantidade
    top_produtos_list = sorted(produtos_count.items(), key=lambda x: x[1], reverse=True)[:3]
    top_produtos = [{"nome": nome, "quantidade": quantidade} for nome, quantidade in top_produtos_list]

    # --- Gasto por categoria ---
    gasto_categoria = {}
    for p in pedidos:
        for item in p.itens:
            cat = item.produto.categoria_produto
            gasto_categoria[cat] = gasto_categoria.get(cat, 0) + (item.quantidade * item.preco_unitario)
    gasto_por_categoria = {
        "labels": list(gasto_categoria.keys()),
        "valores": list(gasto_categoria.values())
    }

    return jsonify({
        "total_pedidos": total_pedidos,
        "total_gasto": total_gasto,
        "media_pedido": media_pedido,
        "top_produtos": top_produtos,
        "gasto_por_categoria": gasto_por_categoria
    })


@perfil_bp.route('/sair')
def sair():
    session.clear()
    return redirect(url_for("home.home"))



@perfil_bp.route('/excluir_perfil', methods=["POST"])
def excluir_perfil():
    usuario = Usuarios.query.get(session['user_id'])
    if usuario:
        try:
            # Verifica se a foto não é a padrão antes de excluir
            if os.path.normpath(usuario.imagem_usuario) != os.path.normpath('uploads/pfp/default.jpg'):
                caminho_arquivo = os.path.join(
                    current_app.root_path, 'static', usuario.imagem_usuario
                )
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)

            # Marca a conta como inativa
            usuario.conta_ativa = "nao"
            db.session.commit()
            session.clear()
            return redirect(url_for("home.home"))
        except Exception as e:
            return f"ERROR: {e}"