import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import get_config, ProductionConfig
from app.extensions import db, migrate, csrf, login_manager, limiter
from app.errors import register_error_handlers
from app.cli import register_cli


def create_app(config_name: str | None = None) -> Flask:
    import os as _os
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=_os.path.join(_root, "templates"),
        static_folder=_os.path.join(_root, "static"),
    )
    os.makedirs(app.instance_path, exist_ok=True)

    config_class = get_config(config_name)
    app.config.from_object(config_class)
    if config_class is ProductionConfig:
        ProductionConfig.validate()

    # Confia em um único proxy reverso à frente da aplicação (ex.: Nginx)
    # para reconstruir corretamente scheme/host a partir de X-Forwarded-*.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    _init_extensions(app)
    _register_blueprints(app)
    _configure_security_headers(app)
    _configure_logging(app)
    _register_context_processors(app)
    register_error_handlers(app)
    register_cli(app)

    return app


def _register_context_processors(app: Flask) -> None:
    from app.utils.time import utcnow

    @app.context_processor
    def inject_globals():
        return {"now": utcnow()}


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.patients.routes import patients_bp
    from app.appointments.routes import appointments_bp
    from app.api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(api_bp)


def _configure_security_headers(app: Flask) -> None:
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        # CSP restrita às CDNs efetivamente usadas pelos templates
        # (Bootstrap, Google Fonts, FullCalendar). Ajuste esta lista se
        # novos recursos externos forem adicionados.
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        if not app.debug and not app.testing:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


def _configure_logging(app: Flask) -> None:
    if app.debug or app.testing:
        return

    os.makedirs(app.config["LOG_DIR"], exist_ok=True)
    log_file = os.path.join(app.config["LOG_DIR"], "mindcare.log")
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    handler.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))
