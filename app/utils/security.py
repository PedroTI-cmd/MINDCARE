"""Utilitários de segurança compartilhados."""
import secrets
import string

from flask import request


def generate_secure_code(length: int = 10) -> str:
    """Gera um código/senha temporária aleatoriamente forte (usa `secrets`,
    não `random`, que não é seguro para fins criptográficos)."""
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_client_ip() -> str:
    """Obtém o IP do cliente, considerando um único proxy reverso confiável
    (ex.: Nginx) configurado para enviar X-Forwarded-For.

    Nota: se a aplicação estiver atrás de mais de um proxy, ajuste
    `ProxyFix` em `app/__init__.py` de acordo com a topologia real, pois
    confiar cegamente em X-Forwarded-For sem isso permite spoofing de IP.
    """
    return request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
