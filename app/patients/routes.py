from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.decorators import roles_required
from app.models import User, Role, log_action
from app.patients.forms import CreatePatientForm
from app.utils.security import generate_secure_code, get_client_ip

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/pacientes")
@login_required
@roles_required(Role.MEDICO, Role.SECRETARIA)
def lista_pacientes():
    page = request.args.get("page", 1, type=int)
    search = (request.args.get("q") or "").strip()

    query = User.query.filter_by(role=Role.PACIENTE)
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(User.name.ilike(like), User.email.ilike(like)))

    pagination = query.order_by(User.name).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        "lista_pacientes.html", pacientes=pagination.items, pagination=pagination, search=search
    )


@patients_bp.route("/paciente/<int:patient_id>")
@login_required
@roles_required(Role.MEDICO, Role.SECRETARIA)
def ficha_paciente(patient_id):
    paciente = User.query.get_or_404(patient_id)
    if paciente.role != Role.PACIENTE:
        abort(404)

    log_action(
        "view_patient_record",
        actor=current_user,
        target_type="user",
        target_id=paciente.id,
        ip_address=get_client_ip(),
    )
    db.session.commit()

    return render_template("ficha_paciente.html", paciente=paciente)


@patients_bp.route("/pacientes/novo", methods=["POST"])
@login_required
@roles_required(Role.SECRETARIA)
def criar_paciente():
    form = CreatePatientForm()
    if not form.validate_on_submit():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")
        return redirect(url_for("main.home"))

    email = form.email.data.strip().lower()
    if User.query.filter_by(email=email).first():
        flash("Já existe um paciente cadastrado com este email.", "warning")
        return redirect(url_for("main.home"))

    temp_password = generate_secure_code(12)
    new_patient = User(
        name=form.name.data.strip(),
        email=email,
        phone=form.phone.data.strip() if form.phone.data else None,
        birth_date=form.birth_date.data,
        role=Role.PACIENTE,
        must_change_password=True,
    )
    new_patient.set_password(temp_password)
    db.session.add(new_patient)
    db.session.flush()

    log_action(
        "create_patient",
        actor=current_user,
        target_type="user",
        target_id=new_patient.id,
        ip_address=get_client_ip(),
    )
    db.session.commit()

    flash(
        f"Paciente {new_patient.name} cadastrado com sucesso. "
        f"Senha temporária (informe ao paciente, ela não será exibida novamente): {temp_password}",
        "success",
    )
    return redirect(url_for("main.home"))
