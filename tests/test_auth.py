import pytest
from tests.conftest import login_paciente, login_secretaria


class TestLoginPage:
    def test_get_login(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert "Login no MindCare" in response.data.decode("utf-8")

    def test_login_paciente_success(self, client):
        """Login correto deve redirecionar para /home."""
        response = login_paciente(client)
        assert response.status_code == 302
        assert "/home" in response.headers.get("Location", "")

    def test_login_paciente_wrong_password(self, client):
        response = client.post(
            "/login",
            data={"role": "paciente", "email": "paciente@test.com", "password": "senha-errada"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "inv" in response.data.decode("utf-8").lower()

    def test_login_secretaria_success(self, client):
        response = login_secretaria(client)
        assert response.status_code == 302
        assert "/home" in response.headers.get("Location", "")

    def test_login_secretaria_wrong_code(self, client):
        response = client.post(
            "/login",
            data={"role": "secretaria", "access_code": "CODIGO-COMPLETAMENTE-ERRADO"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "inv" in response.data.decode("utf-8").lower()

    def test_logout(self, client):
        login_paciente(client)
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302

    def test_unknown_email_same_message(self, client):
        """Não deve revelar se o email existe (evita enumeração de contas)."""
        r_unknown = client.post(
            "/login",
            data={"role": "paciente", "email": "naoexiste@test.com", "password": "qualquer"},
            follow_redirects=False,
        )
        r_wrong_pw = client.post(
            "/login",
            data={"role": "paciente", "email": "paciente@test.com", "password": "errada"},
            follow_redirects=False,
        )
        for r in (r_unknown, r_wrong_pw):
            assert "inv" in r.data.decode("utf-8").lower()


class TestRegister:
    def test_register_success(self, client):
        response = client.post(
            "/register",
            data={
                "name": "Novo Paciente",
                "email": "novo_register_ok@test.com",
                "password": "Senha123",
                "confirm_password": "Senha123",
            },
            follow_redirects=False,
        )
        # sucesso redireciona para login
        assert response.status_code == 302

    def test_register_duplicate_email(self, client):
        response = client.post(
            "/register",
            data={
                "name": "Dup",
                "email": "paciente@test.com",
                "password": "Senha123",
                "confirm_password": "Senha123",
            },
            follow_redirects=False,
        )
        # redireciona para login com aviso
        assert response.status_code == 302

    def test_register_weak_password(self, client):
        response = client.post(
            "/register",
            data={
                "name": "Fraco",
                "email": "fraco@test.com",
                "password": "abc",
                "confirm_password": "abc",
            },
            follow_redirects=False,
        )
        # falha de validação → re-renderiza o formulário (200)
        assert response.status_code == 200
        assert "8" in response.data.decode("utf-8")

    def test_register_password_mismatch(self, client):
        response = client.post(
            "/register",
            data={
                "name": "Mismatch",
                "email": "mismatch@test.com",
                "password": "Senha123",
                "confirm_password": "Senha999",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        body = response.data.decode("utf-8").lower()
        assert "coincidem" in body or "match" in body


class TestProtectedRoutes:
    def test_home_redirects_unauthenticated(self, client):
        response = client.get("/home", follow_redirects=False)
        assert response.status_code == 302

    def test_pacientes_denies_paciente_role(self, client):
        login_paciente(client)
        response = client.get("/pacientes")
        assert response.status_code == 403
