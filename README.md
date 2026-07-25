# MindCare — Sistema de Agendamento de Consultas

Plataforma web para gerenciamento de consultas em clínicas de saúde mental, com papéis distintos para **Paciente**, **Secretária** e **Médico**.

---

## Arquitetura

```
mindcare/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── config.py            # Configurações por ambiente (dev/test/produção)
│   ├── extensions.py        # Instâncias únicas das extensões Flask
│   ├── decorators.py        # @roles_required (RBAC centralizado)
│   ├── errors.py            # Handlers globais de erro (403/404/429/500)
│   ├── cli.py               # Comandos Flask CLI (seed-db, create-staff)
│   │
│   ├── models/
│   │   ├── user.py          # User com hash de senha/código, bloqueio de conta
│   │   ├── consultation.py  # ConsultationRequest com enum de status
│   │   └── audit_log.py     # AuditLog — trilha de auditoria de ações sensíveis
│   │
│   ├── auth/                # Blueprint: login, registro, logout
│   ├── main/                # Blueprint: landing page, roteador de dashboard
│   ├── patients/            # Blueprint: lista, ficha, criação de pacientes
│   ├── appointments/        # Blueprint: solicitar, agendar, cancelar, confirmar
│   ├── api/                 # Blueprint: endpoints JSON (FullCalendar)
│   └── utils/
│       └── security.py      # Geração de senhas seguras, extração de IP
│
├── templates/
│   ├── base.html            # Layout base com variáveis CSS, Bootstrap 5
│   ├── errors/              # Páginas de erro 403/404/429/500
│   └── ...                  # Dashboards, formulários, calendário
│
├── static/css/style.css
├── migrations/              # Flask-Migrate (Alembic)
├── tests/                   # pytest
├── wsgi.py                  # Ponto de entrada WSGI (Gunicorn)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── pytest.ini
```

---

## Quickstart (desenvolvimento local)

### Pré-requisitos
- Python 3.12+
- pip

### 1. Clone e configure

```bash
git clone <repo-url> mindcare
cd mindcare

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt

cp .env.example .env
# Edite .env e defina ao menos SECRET_KEY
```

### 2. Inicialize o banco de dados

```bash
flask db upgrade                   # aplica as migrations
flask seed-db                      # popula com dados de exemplo (só em dev)
```

Credenciais geradas pelo `seed-db`:
| Papel       | Login                  | Senha/Código   |
|-------------|------------------------|----------------|
| Paciente    | `paciente@example.com` | `SenhaForte123` |
| Médico      | —                      | `MED-123-DEV`  |
| Secretária  | —                      | `SEC-001-DEV`  |

### 3. Suba a aplicação

```bash
flask run --debug
```

Acesse: <http://localhost:5000>

---

## Docker (ambiente completo)

```bash
docker compose up --build
```

Isso sobe: Flask + Gunicorn, PostgreSQL 16 e Redis 7 (para rate limiting).

---

## Configuração de produção

Defina **obrigatoriamente** no ambiente:

| Variável       | Descrição                            |
|----------------|--------------------------------------|
| `SECRET_KEY`   | Chave de sessão (nunca versionar)    |
| `DATABASE_URL` | URL do PostgreSQL                    |
| `FLASK_ENV`    | `production`                         |

A aplicação falha ao iniciar (*fail-fast*) se essas variáveis não estiverem definidas.

Para gerar um `SECRET_KEY` seguro:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Criando contas de staff em produção

```bash
flask create-staff
```

O comando solicita nome e papel, gera um código de acesso aleatório de 12 caracteres e o exibe **uma única vez** no terminal. O hash é armazenado no banco — o código em texto puro nunca é persistido.

---

## Testes

```bash
pytest                    # roda toda a suite
pytest --cov=app          # com cobertura
pytest -v tests/test_auth.py   # arquivo específico
```

---

## Segurança

### O que foi implementado

| Vulnerabilidade original       | Correção                                                        |
|--------------------------------|-----------------------------------------------------------------|
| `SECRET_KEY` hardcoded         | Variável de ambiente; falha rápido sem ela em produção          |
| Senhas em texto puro           | Werkzeug `generate_password_hash` (scrypt/pbkdf2)              |
| Códigos de acesso em texto puro | Hasheados com `generate_password_hash`                         |
| CSRF inexistente               | Flask-WTF com token em todos os formulários                     |
| Sem rate limiting              | Flask-Limiter: 10 req/min no login, 5 req/min no registro       |
| Sem bloqueio por força bruta   | `failed_login_attempts` + `locked_until` no modelo `User`       |
| Checagens de papel repetidas   | Decorator `@roles_required` centralizado                        |
| IDOR no cancelamento           | Checagem explícita `consulta.patient_id != current_user.id`    |
| `debug=True` sempre            | Configuração por ambiente                                        |
| Sem cabeçalhos de segurança    | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, etc.       |
| Sem trilha de auditoria        | Modelo `AuditLog` para ações sensíveis (login, fichas, etc.)    |
| Sem tratamento de erros        | Handlers para 403/404/429/500 com rollback de DB no 500         |
| Formulário de cadastro sem ação | Rota `POST /pacientes/novo` + WTForms + senha temporária segura|
| ProxyFix ausente               | `werkzeug.middleware.proxy_fix.ProxyFix` configurado            |

### Relatando vulnerabilidades

Veja `SECURITY.md`.

---

## Variáveis de ambiente disponíveis

Veja `.env.example` para a lista completa com descrições.
