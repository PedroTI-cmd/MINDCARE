# Política de Segurança

## Versões suportadas

| Versão | Suporte de segurança |
|--------|----------------------|
| última |  X Não               |


**abra um issue público** para reportar vulnerabilidades de segurança.

## Boas práticas para operadores

- Mantenha `SECRET_KEY` rotacionada periodicamente e nunca a versione
- Use PostgreSQL em produção (SQLite não é adequado para múltiplos workers)
- Configure Redis para o rate limiter em produção (`RATELIMIT_STORAGE_URI`)
- Mantenha o servidor por trás de Nginx/Caddy com TLS ativo
- Habilite `SESSION_COOKIE_SECURE=true` em ambientes com HTTPS
- Revise os logs de auditoria (`audit_log`) regularmente
- Aplique `flask db upgrade` antes de cada deploy
