from datetime import timedelta
from app.utils.time import utcnow

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class Role:
    """Constantes de papéis de usuário (evita strings soltas pelo código)."""

    PACIENTE = "paciente"
    MEDICO = "medico"
    SECRETARIA = "secretaria"

    ALL = (PACIENTE, MEDICO, SECRETARIA)
    STAFF = (MEDICO, SECRETARIA)


class User(UserMixin, db.Model):
    """Modelo para todos os usuários do sistema (Médicos, Secretárias, Pacientes).

    Segurança:
    - `password_hash` nunca armazena senha em texto puro (werkzeug scrypt/pbkdf2).
    - `access_code_hash` (usado por médico/secretária) também é hasheado — o
      código em texto puro só existe no momento da criação, exibido uma única
      vez para quem cria a conta (ver `flask create-staff`).
    - Contadores de tentativas falhas + bloqueio temporário mitigam
      força bruta tanto no login por senha quanto por código de acesso.
    """

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False, index=True)
    access_code_hash = db.Column(db.String(255), nullable=True)

    phone = db.Column(db.String(30), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)

    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)

    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    locked_until = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    requests = db.relationship(
        "ConsultationRequest",
        backref="patient",
        lazy=True,
        foreign_keys="ConsultationRequest.patient_id",
    )

    __table_args__ = (
        db.CheckConstraint(
            "role IN ('paciente', 'medico', 'secretaria')", name="ck_user_role_valid"
        ),
    )

    # --- Flask-Login ---
    @property
    def is_active(self):  # sobrescreve UserMixin.is_active
        return self.is_active_account

    # --- Senha (pacientes) ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    # --- Código de acesso (médico/secretária) ---
    def set_access_code(self, raw_code: str) -> None:
        self.access_code_hash = generate_password_hash(raw_code)

    def check_access_code(self, raw_code: str) -> bool:
        if not self.access_code_hash:
            return False
        return check_password_hash(self.access_code_hash, raw_code)

    # --- Bloqueio de conta / força bruta ---
    def register_failed_login(self, max_attempts: int, lockout_minutes: int) -> None:
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = utcnow() + timedelta(minutes=lockout_minutes)

    def register_successful_login(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > utcnow())

    def __repr__(self):
        return f"<User {self.id} {self.role}>"
