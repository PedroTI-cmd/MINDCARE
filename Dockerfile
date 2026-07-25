FROM python:3.12-slim

# Evita geração de arquivos .pyc e saída de buffer (melhor para logs em containers)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

WORKDIR /app

# Instala dependências antes de copiar o código (aproveita cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cria diretório de logs e pasta de instância com permissão restrita
RUN mkdir -p logs instance && chmod 750 logs instance

# Usuário não-root para executar a aplicação (princípio do menor privilégio)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Gunicorn: 4 workers síncronos. Ajuste --workers conforme os núcleos do servidor
# (regra: 2 × núcleos + 1). Use --worker-class gevent para alta concorrência.
CMD ["gunicorn", "wsgi:application", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "30", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
