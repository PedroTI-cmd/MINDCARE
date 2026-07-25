"""
Configuração da aplicação baseada em variáveis de ambiente.

Nunca coloque segredos (SECRET_KEY, senhas de banco, etc.) diretamente
no código-fonte. Use um arquivo `.env` local (veja `.env.example`) ou
variáveis de ambiente reais no servidor de produção.
"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Configuração base, compartilhada por todos os ambientes."""

    # --- Segurança de sessão / cookies ---
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", default=True)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # --- Banco de dados ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'mindcare.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Autenticação / política de senha ---
    LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", 5))
    LOGIN_LOCKOUT_MINUTES = int(os.environ.get("LOGIN_LOCKOUT_MINUTES", 15))
    MIN_PASSWORD_LENGTH = int(os.environ.get("MIN_PASSWORD_LENGTH", 8))

    # --- Rate limiting (Flask-Limiter) ---
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    # --- Agendamento ---
    MAX_REQUESTS_PER_DAY = int(os.environ.get("MAX_REQUESTS_PER_DAY", 2))
    PATIENTS_PER_PAGE = int(os.environ.get("PATIENTS_PER_PAGE", 20))

    # --- Logging ---
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_DIR = os.environ.get("LOG_DIR", os.path.join(basedir, "logs"))

    WTF_CSRF_TIME_LIMIT = None  # tokens não expiram por tempo de sessão


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", default=False)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'mindcare-dev.db')}"
    )


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "testing-secret-key-not-for-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False

    @staticmethod
    def validate():
        """Chamado explicitamente por create_app() em produção.

        Falha rápido (fail-fast) se segredos essenciais não estiverem
        configurados, em vez de subir com valores inseguros padrão.
        """
        missing = []
        if not os.environ.get("SECRET_KEY"):
            missing.append("SECRET_KEY")
        if not os.environ.get("DATABASE_URL"):
            missing.append("DATABASE_URL")
        if missing:
            raise RuntimeError(
                "Variáveis de ambiente obrigatórias ausentes em produção: "
                + ", ".join(missing)
            )


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None):
    name = name or os.environ.get("FLASK_ENV", "default")
    return CONFIG_BY_NAME.get(name, DevelopmentConfig)
