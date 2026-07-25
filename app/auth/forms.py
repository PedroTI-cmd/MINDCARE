from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp

from app.models import Role


class LoginForm(FlaskForm):
    role = SelectField(
        "Eu sou",
        choices=[(Role.PACIENTE, "Paciente"), (Role.MEDICO, "Médico"), (Role.SECRETARIA, "Secretária(o)")],
        validators=[DataRequired()],
    )
    email = StringField("Email", validators=[Length(max=255)])
    password = PasswordField("Senha", validators=[Length(max=255)])
    access_code = PasswordField("Código de acesso", validators=[Length(max=255)])


class RegisterForm(FlaskForm):
    name = StringField("Nome completo", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(),
            Length(min=8, message="A senha deve ter pelo menos 8 caracteres."),
            Regexp(
                r"^(?=.*[A-Za-z])(?=.*\d).+$",
                message="A senha deve conter letras e números.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirme a senha",
        validators=[DataRequired(), EqualTo("password", message="As senhas não coincidem.")],
    )
