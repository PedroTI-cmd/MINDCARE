from flask import Blueprint, jsonify
from flask_login import login_required

from app.decorators import roles_required
from app.models import ConsultationRequest, ConsultationStatus, Role

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/consultas")
@login_required
@roles_required(Role.MEDICO, Role.SECRETARIA)
def api_consultas():
    """Retorna as consultas agendadas em formato JSON para o FullCalendar."""
    consultas_agendadas = ConsultationRequest.query.filter_by(
        status=ConsultationStatus.SCHEDULED
    ).all()

    eventos = [
        {
            "title": f"Consulta com {consulta.patient.name}",
            "start": consulta.scheduled_datetime.isoformat(),
            "id": consulta.id,
            "extendedProps": {
                "patientName": consulta.patient.name,
                "formattedDateTime": consulta.scheduled_datetime.strftime("%d/%m/%Y às %H:%M"),
            },
        }
        for consulta in consultas_agendadas
    ]
    return jsonify(eventos)
