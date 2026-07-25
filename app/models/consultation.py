from app.utils.time import utcnow

from app.extensions import db


class ConsultationStatus:
    PENDING = "pending"
    SCHEDULED = "scheduled"
    DONE = "done"

    ALL = (PENDING, SCHEDULED, DONE)


class ConsultationRequest(db.Model):
    """Solicitação/agendamento de consulta feita por um paciente."""

    __tablename__ = "consultation_request"

    id = db.Column(db.Integer, primary_key=True)
    requested_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    status = db.Column(
        db.String(20), nullable=False, default=ConsultationStatus.PENDING, index=True
    )
    patient_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )

    scheduled_datetime = db.Column(db.DateTime, nullable=True, index=True)
    notes = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'scheduled', 'done')",
            name="ck_consultation_status_valid",
        ),
    )

    def __repr__(self):
        return f"<ConsultationRequest {self.id} patient={self.patient_id} status={self.status}>"
