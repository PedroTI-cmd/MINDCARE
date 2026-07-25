"""Helper de data/hora para evitar o `datetime.utcnow()` obsoleto.

Mantemos os valores como *naive* (sem tzinfo) porque é o que as colunas
`db.DateTime` do SQLAlchemy/SQLite armazenam neste projeto. Se no futuro
o banco for migrado para armazenar datas com timezone, ajuste aqui e nas
colunas dos modelos (`db.DateTime(timezone=True)`).
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
