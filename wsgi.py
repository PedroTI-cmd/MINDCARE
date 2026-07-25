"""Ponto de entrada WSGI para servidores de produção (ex.: Gunicorn).

Exemplo de uso:
    gunicorn "wsgi:application" --workers 4 --bind 0.0.0.0:8000
"""
import os
from app import create_app

application = create_app(os.environ.get("FLASK_ENV", "production"))

# Alias para compatibilidade com algumas plataformas (Railway, Heroku, etc.)
app = application
