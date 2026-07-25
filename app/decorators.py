"""Decorators de controle de acesso baseado em papel (RBAC).

Centralizar a checagem de papel em um decorator evita o padrão frágil de
repetir `if session['user']['role'] not in [...]` em cada rota — um erro de
copiar/colar nessas checagens é uma causa comum de falhas de autorização
(IDOR, escalonamento de privilégio).
"""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def roles_required(*roles):
    """Restringe uma rota a usuários autenticados com um dos papéis indicados.

    Requer que `@login_required` (Flask-Login) também esteja aplicado, ou
    aplica a checagem de autenticação internamente caso não esteja.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Por favor, faça login para acessar esta página.", "info")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
