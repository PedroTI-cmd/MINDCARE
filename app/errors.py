from flask import render_template, current_app
from app.extensions import db


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def rate_limited(_error):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(error):
        # Garante que uma transação de banco quebrada não vaze para a
        # próxima requisição no mesmo worker.
        db.session.rollback()
        current_app.logger.exception("Erro interno não tratado: %s", error)
        return render_template("errors/500.html"), 500
