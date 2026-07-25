import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User, Role


@pytest.fixture(scope="session")
def app():
    """Cria a aplicação em modo de teste (banco SQLite em memória).

    IMPORTANTE: não mantemos um app_context() pressionado durante toda a
    sessão de testes. Se fizéssemos isso, o Flask reaproveitaria esse
    mesmo contexto (e o `flask.g`, onde o Flask-Login guarda o usuário
    autenticado) em vez de criar um novo por requisição — fazendo o
    login de um teste "vazar" para o próximo mesmo com um test_client novo.
    Por isso, o app_context só é usado pontualmente (setup/teardown do
    banco); cada requisição feita pelo test_client cria seu próprio
    contexto de aplicação/requisição, exatamente como em produção.
    """
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        _seed_test_data()

    yield application

    with application.app_context():
        _db.session.remove()
        _db.drop_all()


def _seed_test_data():
    medico = User(name="Dr. Teste", role=Role.MEDICO)
    medico.set_access_code("COD-MED-TEST")

    secretaria = User(name="Sec. Teste", role=Role.SECRETARIA)
    secretaria.set_access_code("COD-SEC-TEST")

    paciente = User(name="Pac. Teste", email="paciente@test.com", role=Role.PACIENTE)
    paciente.set_password("Senha123")

    _db.session.add_all([medico, secretaria, paciente])
    _db.session.commit()


@pytest.fixture()
def client(app):
    """Cliente de teste novo a cada teste (cookie jar isolado)."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def reset_test_user_lockout(app):
    """Reseta o estado de bloqueio do usuário paciente antes de cada teste."""
    with app.app_context():
        u = User.query.filter_by(email="paciente@test.com").first()
        if u:
            u.failed_login_attempts = 0
            u.locked_until = None
            _db.session.commit()
    yield


# ---------------------------------------------------------------------------
# Login helpers — não seguem redirect, evitando renderizar templates de
# dashboard durante os testes (o que é irrelevante para o que testamos aqui).
# ---------------------------------------------------------------------------

def login_paciente(client):
    return client.post(
        "/login",
        data={"role": "paciente", "email": "paciente@test.com", "password": "Senha123"},
        follow_redirects=False,
    )


def login_secretaria(client):
    return client.post(
        "/login",
        data={"role": "secretaria", "access_code": "COD-SEC-TEST"},
        follow_redirects=False,
    )


def login_medico(client):
    return client.post(
        "/login",
        data={"role": "medico", "access_code": "COD-MED-TEST"},
        follow_redirects=False,
    )
