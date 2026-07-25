from app.models import User, Role


class TestSecurityHeaders:
    def test_x_content_type_nosniff(self, client):
        response = client.get("/login")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_deny(self, client):
        response = client.get("/login")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_csp_present(self, client):
        response = client.get("/login")
        assert "Content-Security-Policy" in response.headers


class TestUserModel:
    def test_password_hashed(self, app):
        with app.app_context():
            u = User(name="Teste", role=Role.PACIENTE, email="hash@test.com")
            u.set_password("MinhaSenha1")
            assert u.password_hash != "MinhaSenha1"
            assert u.check_password("MinhaSenha1")
            assert not u.check_password("errada")

    def test_access_code_hashed(self, app):
        with app.app_context():
            u = User(name="Staff", role=Role.MEDICO)
            u.set_access_code("CODIGO-SECRETO")
            assert u.access_code_hash != "CODIGO-SECRETO"
            assert u.check_access_code("CODIGO-SECRETO")
            assert not u.check_access_code("errado")

    def test_account_lockout(self, app):
        with app.app_context():
            u = User(name="Lock", role=Role.PACIENTE, email="lock@test.com")
            u.set_password("Senha123")
            assert not u.is_locked
            for _ in range(5):
                u.register_failed_login(max_attempts=5, lockout_minutes=15)
            assert u.is_locked
            u.register_successful_login()
            assert not u.is_locked
            assert u.failed_login_attempts == 0
