from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError


class CreatePatientForm(FlaskForm):
    name = StringField("Nome completo", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Telefone", validators=[Optional(), Length(max=30)])
    birth_date = DateField("Data de nascimento", validators=[Optional()], format="%Y-%m-%d")

    def validate_birth_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("A data de nascimento não pode ser no futuro.")
