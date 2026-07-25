from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.models import User, Role, log_action
from app.utils.security import get_client_ip
from app.auth.forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        role = form.role.data
        user = None
        credential_ok = False

        if role == Role.PACIENTE:
            email = (form.email.data or "").strip().lower()
            user = User.query.filter_by(email=email, role=Role.PACIENTE).first()
            if user and not user.is_locked:
                credential_ok = user.check_password(form.password.data or "")
        else:
            access_code = form.access_code.data or ""
            # Não há como buscar por hash, então iteramos apenas entre os
            # usuários do papel solicitado (staff é um conjunto pequeno).
            candidates = User.query.filter_by(role=role).all()
            for candidate in candidates:
                if candidate.check_access_code(access_code):
                    user = candidate
                    break
            if user and not user.is_locked:
                credential_ok = True

        ip = get_client_ip()

        if user and user.is_locked:
            flash(
                "Esta conta está temporariamente bloqueada devido a múltiplas "
                "tentativas de login inválidas. Tente novamente mais tarde.",
                "danger",
            )
            log_action("login_blocked_locked", actor=user, ip_address=ip)
            db.session.commit()
        elif user and credential_ok and user.is_active_account:
            user.register_successful_login()
            log_action("login_success", actor=user, ip_address=ip)
            db.session.commit()
            login_user(user)
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("main.home"))
        else:
            if user:
                user.register_failed_login(
                    max_attempts=current_app.config["LOGIN_MAX_ATTEMPTS"],
                    lockout_minutes=current_app.config["LOGIN_LOCKOUT_MINUTES"],
                )
                log_action("login_failed", actor=user, ip_address=ip)
                db.session.commit()
            else:
                # Não revela se o usuário existe ou não — evita
                # enumeração de contas via mensagens de erro distintas.
                log_action(
                    "login_failed_unknown_user", ip_address=ip,
                    details=f"role={role}",
                )
                db.session.commit()

            if role == Role.PACIENTE:
                flash("Email ou senha inválidos.", "danger")
            else:
                flash("Código de acesso inválido.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Este email já está cadastrado. Por favor, faça login.", "warning")
            return redirect(url_for("auth.login"))

        new_user = User(name=form.name.data.strip(), email=email, role=Role.PACIENTE)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.flush()
        log_action("register", actor=new_user, ip_address=get_client_ip())
        db.session.commit()

        flash("Registro realizado com sucesso! Por favor, faça o login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_action("logout", actor=current_user, ip_address=get_client_ip())
    db.session.commit()
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("main.landing"))
