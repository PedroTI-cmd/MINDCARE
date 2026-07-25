from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import User, ConsultationRequest, ConsultationStatus, Role

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    return render_template("landing.html")


@main_bp.route("/home")
@login_required
def home():
    if current_user.role == Role.MEDICO:
        doctor_patients = User.query.filter_by(role=Role.PACIENTE).order_by(User.name).all()
        return render_template("dashboard_medico.html", patients=doctor_patients)

    if current_user.role == Role.SECRETARIA:
        pending_requests = (
            ConsultationRequest.query.join(User)
            .filter(ConsultationRequest.status == ConsultationStatus.PENDING)
            .order_by(ConsultationRequest.requested_at.desc())
            .all()
        )
        return render_template("dashboard_secretaria.html", requests=pending_requests)

    # paciente
    upcoming_appointments = (
        ConsultationRequest.query.filter(
            ConsultationRequest.patient_id == current_user.id,
            ConsultationRequest.status == ConsultationStatus.SCHEDULED,
        )
        .order_by(ConsultationRequest.scheduled_datetime.asc())
        .all()
    )
    return render_template("dashboard_paciente.html", appointments=upcoming_appointments)
