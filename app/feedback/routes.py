from flask import Blueprint, render_template, request, redirect, url_for
from ..models.feedback import Feedbacks
from ..extensions import db

feedback_bp = Blueprint("feedback", __name__, url_prefix="/feedback")

@feedback_bp.route('/feedback')
def feedback():
    return render_template("feedback/feedback.html")

@feedback_bp.route('/enviar_feedback', methods=["POST"])
def enviar_feedback():
    if request.method == "POST":
        nome_feedback = request.form["nome_feedback"]
        email_feedback = request.form["email_feedback"]
        tipo_feedback = request.form["tipo_feedback"]
        texto_feedback = request.form["texto_feedback"]
        novo_feedback = Feedbacks(nome_feedback=nome_feedback, email_feedback=email_feedback, tipo_feedback=tipo_feedback, texto_feedback=texto_feedback)
        try:
            db.session.add(novo_feedback)
            db.session.commit()
            return "Duvida/Reclamação enviada com sucesso!"
        except Exception as e:
            return f"Error: {e}"


@feedback_bp.route('/database_feedbacks')
def database_feedbacks():
    feedbacks = Feedbacks.query.order_by(Feedbacks.id_feedback).all()
    return render_template("feedback/database_feedbacks.html", feedbacks=feedbacks)

@feedback_bp.route('/database_feedbacks/excluir_feedback/<int:id>')
def excluir_feedback(id:int):
    excluir_feedback = Feedbacks.query.get_or_404(id)
    try:
        db.session.delete(excluir_feedback)
        db.session.commit()
        return redirect(url_for("feedback.database_feedbacks"))
    except Exception as e:
        return f"Error: {e}"