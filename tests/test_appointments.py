import pytest
from tests.conftest import login_paciente, login_secretaria


class TestSolicitarConsulta:
    def test_paciente_pode_solicitar(self, client):
        login_paciente(client)
        response = client.post("/solicitar_consulta", follow_redirects=False)
        # sucesso redireciona para /home
        assert response.status_code == 302

    def test_nao_autenticado_nao_pode_solicitar(self, client):
        response = client.post("/solicitar_consulta", follow_redirects=False)
        assert response.status_code == 302
        assert "login" in response.headers.get("Location", "").lower()

    def test_secretaria_nao_pode_solicitar(self, client):
        login_secretaria(client)
        response = client.post("/solicitar_consulta")
        assert response.status_code == 403


class TestIDOR:
    """Garante que um paciente não pode cancelar a consulta de outro."""

    def test_paciente_nao_cancela_consulta_alheia(self, client, app):
        from app.extensions import db
        from app.models import User, Role, ConsultationRequest, ConsultationStatus
        from datetime import datetime

        with app.app_context():
            outro = User(name="Outro IDOR2", email="outro_idor2@test.com", role=Role.PACIENTE)
            outro.set_password("Senha123")
            db.session.add(outro)
            db.session.flush()

            consulta = ConsultationRequest(
                patient_id=outro.id,
                status=ConsultationStatus.SCHEDULED,
                scheduled_datetime=datetime(2099, 2, 20, 14, 0),
            )
            db.session.add(consulta)
            db.session.commit()
            consulta_id = consulta.id

        login_paciente(client)
        response = client.post(
            f"/paciente_cancelar_consulta/{consulta_id}",
            follow_redirects=False,
        )
        assert response.status_code == 403
