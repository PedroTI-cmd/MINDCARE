# Política de Segurança

## Versões suportadas

| Versão | Suporte de segurança |
|--------|----------------------|
| última | ✅ Sim               |

## Relatando uma vulnerabilidade

**Não abra um issue público** para reportar vulnerabilidades de segurança.

Entre em contato diretamente pelo e-mail de segurança configurado para este projeto. Inclua:

1. Descrição da vulnerabilidade
2. Passos para reproduzir
3. Impacto potencial
4. Sugestão de correção (se houver)

Comprometemo-nos a responder em até 48 horas e a publicar um patch, com crédito ao pesquisador, em até 7 dias para vulnerabilidades críticas.

## Boas práticas para operadores

- Mantenha `SECRET_KEY` rotacionada periodicamente e nunca a versione
- Use PostgreSQL em produção (SQLite não é adequado para múltiplos workers)
- Configure Redis para o rate limiter em produção (`RATELIMIT_STORAGE_URI`)
- Mantenha o servidor por trás de Nginx/Caddy com TLS ativo
- Habilite `SESSION_COOKIE_SECURE=true` em ambientes com HTTPS
- Revise os logs de auditoria (`audit_log`) regularmente
- Aplique `flask db upgrade` antes de cada deploy
