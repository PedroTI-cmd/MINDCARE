from datetime import datetime
from app.utils.time import utcnow

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.decorators import roles_required
from app.models import ConsultationRequest, ConsultationStatus, Role, log_action
from app.utils.security import get_client_ip

appointments_bp = Blueprint("appointments", __name__)


@appointments_bp.route("/solicitar_consulta", methods=["POST"])
@login_required
@roles_required(Role.PACIENTE)
def solicitar_consulta():
    patient_id = current_user.id
    today = utcnow().date()

    requests_today = ConsultationRequest.query.filter(
        ConsultationRequest.patient_id == patient_id,
        func.date(ConsultationRequest.requested_at) == today,
    ).count()

    max_per_day = current_app.config["MAX_REQUESTS_PER_DAY"]
    if requests_today >= max_per_day:
        flash(
            f"Você já atingiu o limite de {max_per_day} solicitações de agendamento por dia.",
            "warning",
        )
    else:
        new_request = ConsultationRequest(patient_id=patient_id)
        db.session.add(new_request)
        db.session.flush()
        log_action(
            "request_consultation",
            actor=current_user,
            target_type="consultation_request",
            target_id=new_request.id,
            ip_address=get_client_ip(),
        )
        db.session.commit()
        flash(
            "Sua solicitação de agendamento foi enviada com sucesso! "
            "A secretaria entrará em contato em breve.",
            "success",
        )
    return redirect(url_for("main.home"))


@appointments_bp.route("/agendar_consulta/<int:request_id>", methods=["POST"])
@login_required
@roles_required(Role.SECRETARIA)
def agendar_consulta(request_id):
    consulta_req = ConsultationRequest.query.get_or_404(request_id)

    data_str = (request.form.get("data") or "").strip()
    hora_str = (request.form.get("hora") or "").strip()

    if not data_str or not hora_str:
        flash("Informe data e hora da consulta.", "danger")
        return redirect(url_for("main.home"))

    try:
        scheduled_datetime = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        flash("Data ou hora inválida.", "danger")
        return redirect(url_for("main.home"))

    if scheduled_datetime < utcnow():
        flash("Não é possível agendar uma consulta em uma data/hora no passado.", "danger")
        return redirect(url_for("main.home"))

    conflict = ConsultationRequest.query.filter(
        ConsultationRequest.status == ConsultationStatus.SCHEDULED,
        ConsultationRequest.scheduled_datetime == scheduled_datetime,
        ConsultationRequest.id != consulta_req.id,
    ).first()
    if conflict:
        flash("Já existe uma consulta agendada para esta data e horário.", "warning")
        return redirect(url_for("main.home"))

    consulta_req.scheduled_datetime = scheduled_datetime
    consulta_req.status = ConsultationStatus.SCHEDULED
    log_action(
        "schedule_consultation",
        actor=current_user,
        target_type="consultation_request",
        target_id=consulta_req.id,
        ip_address=get_client_ip(),
        details=scheduled_datetime.isoformat(),
    )
    db.session.commit()
    flash(
        f"Consulta para {consulta_req.patient.name} agendada com sucesso para "
        f"{scheduled_datetime.strftime('%d/%m/%Y às %H:%M')}.",
        "success",
    )
    return redirect(url_for("main.home"))


@appointments_bp.route("/calendario")
@login_required
@roles_required(Role.MEDICO, Role.SECRETARIA)
def calendario():
    return render_template("calendario.html")


@appointments_bp.route("/cancelar_consulta/<int:request_id>", methods=["POST"])
@login_required
@roles_required(Role.SECRETARIA)
def cancelar_consulta(request_id):
    consulta = ConsultationRequest.query.get_or_404(request_id)
    consulta.status = ConsultationStatus.PENDING
    consulta.scheduled_datetime = None
    log_action(
        "cancel_consultation",
        actor=current_user,
        target_type="consultation_request",
        target_id=consulta.id,
        ip_address=get_client_ip(),
    )
    db.session.commit()
    flash(
        f"O agendamento de {consulta.patient.name} foi cancelado e retornou para pendências.",
        "warning",
    )
    return redirect(url_for("appointments.calendario"))


@appointments_bp.route("/confirmar_consulta/<int:request_id>", methods=["POST"])
@login_required
@roles_required(Role.MEDICO, Role.SECRETARIA)
def confirmar_consulta(request_id):
    consulta = ConsultationRequest.query.get_or_404(request_id)
    consulta.status = ConsultationStatus.DONE
    log_action(
        "confirm_consultation",
        actor=current_user,
        target_type="consultation_request",
        target_id=consulta.id,
        ip_address=get_client_ip(),
    )
    db.session.commit()
    flash(f"A consulta de {consulta.patient.name} foi marcada como concluída.", "success")
    return redirect(url_for("appointments.calendario"))


@appointments_bp.route("/historico_consultas")
@login_required
@roles_required(Role.PACIENTE)
def historico_consultas():
    consultas_concluidas = (
        ConsultationRequest.query.filter_by(
            patient_id=current_user.id, status=ConsultationStatus.DONE
        )
        .order_by(ConsultationRequest.scheduled_datetime.desc())
        .all()
    )
    return render_template("historico_consultas.html", consultas=consultas_concluidas)


@appointments_bp.route("/paciente_cancelar_consulta/<int:request_id>", methods=["POST"])
@login_required
@roles_required(Role.PACIENTE)
def paciente_cancelar_consulta(request_id):
    consulta = ConsultationRequest.query.get_or_404(request_id)

    # Verificação de autorização: garante que o paciente só pode cancelar
    # seus próprios agendamentos (evita IDOR — Insecure Direct Object Reference).
    if consulta.patient_id != current_user.id:
        flash("Você não tem permissão para cancelar este agendamento.", "danger")
        abort(403)

    consulta.status = ConsultationStatus.PENDING
    consulta.scheduled_datetime = None
    log_action(
        "patient_cancel_consultation",
        actor=current_user,
        target_type="consultation_request",
        target_id=consulta.id,
        ip_address=get_client_ip(),
    )
    db.session.commit()
    flash("Seu agendamento foi cancelado com sucesso. A vaga foi liberada.", "success")
    return redirect(url_for("main.home"))
