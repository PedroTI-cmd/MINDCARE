from app.utils.time import utcnow

from app.extensions import db


class AuditLog(db.Model):
    """Registro de auditoria para ações sensíveis.

    Como o sistema lida com dados de saúde (informações de pacientes e
    consultas), manter um trilha de auditoria de quem fez o quê, quando e
    de onde é uma boa prática de segurança e conformidade (ex.: LGPD).
    """

    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    actor_role = db.Column(db.String(20), nullable=True)

    action = db.Column(db.String(80), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<AuditLog {self.action} actor={self.actor_id} target={self.target_type}:{self.target_id}>"


def log_action(action, actor=None, target_type=None, target_id=None, details=None, ip_address=None):
    """Cria e persiste uma entrada de auditoria.

    Não lança exceção em caso de falha de log para não quebrar o fluxo
    principal da requisição — apenas a operação de log é revertida.
    """
    entry = AuditLog(
        action=action,
        actor_id=getattr(actor, "id", None),
        actor_role=getattr(actor, "role", None),
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.session.add(entry)
