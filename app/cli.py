import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User, Role
from app.utils.security import generate_secure_code


def register_cli(app):
    @app.cli.command("seed-db")
    @with_appcontext
    def seed_db():
        """Cria as tabelas e, em ambiente de desenvolvimento/teste, popula
        com dados de exemplo. NUNCA cria credenciais fixas em produção."""
        db.create_all()

        if app.config.get("ENV") == "production" or not app.debug:
            click.echo(
                "Ambiente de produção detectado: apenas as tabelas foram "
                "criadas. Use 'flask create-staff' para criar contas."
            )
            return

        if User.query.filter_by(role=Role.MEDICO).first():
            click.echo("Dados de exemplo já existem, nada a fazer.")
            return

        medico = User(name="Dr. House", role=Role.MEDICO)
        medico.set_access_code("MED-123-DEV")

        sec1 = User(name="Maria", role=Role.SECRETARIA)
        sec1.set_access_code("SEC-001-DEV")

        paciente = User(
            name="João",
            email="paciente@example.com",
            role=Role.PACIENTE,
            phone="(11) 98765-4321",
        )
        paciente.set_password("SenhaForte123")

        db.session.add_all([medico, sec1, paciente])
        db.session.commit()
        click.echo(
            "Banco de dados de desenvolvimento populado.\n"
            "  Médico: código MED-123-DEV\n"
            "  Secretária: código SEC-001-DEV\n"
            "  Paciente: paciente@example.com / SenhaForte123"
        )

    @app.cli.command("create-staff")
    @click.option("--name", prompt="Nome completo", help="Nome do funcionário")
    @click.option(
        "--role",
        prompt="Papel (medico/secretaria)",
        type=click.Choice([Role.MEDICO, Role.SECRETARIA]),
    )
    @with_appcontext
    def create_staff(name, role):
        """Cria uma conta de médico ou secretária com um código de acesso
        gerado com segurança, exibido apenas uma vez neste terminal."""
        code = generate_secure_code(12)
        user = User(name=name, role=role)
        user.set_access_code(code)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Usuário '{name}' ({role}) criado. Código de acesso (anote agora): {code}")
