# Auditoria de infraestrutura

Checklist do **laro_mvp_tracker**: bot Discord em Python (Docker) na VM Oracle `laro-vnic`, Postgres 16 em container no mesmo compose. Repo **público** no GitHub. É referenciado pelo `AGENTS.md`.

**Regra de ouro:** nunca cole segredos reais (senha do Postgres, token do bot, chaves SSH). Mascare valores e hosts em qualquer saída enviada a uma IA.

## Ordem das etapas

1. Auditoria **sem alterações** (este documento).
2. Segredos: rotacionar o que estiver exposto, antes de qualquer refatoração.
3. Rede de segurança: testes de caracterização, snapshot ou equivalente.
4. CI e proteção da branch principal.
5. Validação de entrada (comandos do bot).
6. Refatorações, uma etapa por vez, com a rede de segurança verde.
7. `handoff.md` para quem continuar.

## 1. Repositório e histórico

- O repo é **público**: todo o histórico é exposição. Nunca versionar `.env`, `.pem`, dumps.
- Procure arquivos sensíveis versionados:

```bash
git ls-files | grep -Ei '\.env$|\.env\.|\.pem|\.key|dump|\.sql\.gz|backup'
```

- Procure o mesmo no **histórico** (arquivos apagados continuam lá):

```bash
git log --all --diff-filter=A --name-only --format= | grep -Ei '\.env|\.pem|\.key|dump' | sort -u
```

- Use um detector de segredos no código e no histórico (`gitleaks` ou `trufflehog`), rodando localmente.
- `sql/laro.sql` e `sql/seed_mvp_latam.sql` são schema + seed de dados **do jogo** (MVPs, mapas) — sem credenciais por desenho. Se um dia um dump de dados reais for versionado, trata-se como vazamento potencial (tem IDs de Discord; avalia antes).
- `.env.example` é o único arquivo de ambiente versionado: só nomes de variáveis, nunca valores.

### Se achar um segredo

1. **Rotacione primeiro**: regenere o token do bot no Discord Developer Portal (isso troca a credencial viva), troque a senha do Postgres da VM.
2. Só depois decida se vale reescrever o histórico. A rotação é o que realmente protege; apagar do código não basta.

## 2. Banco (Postgres no compose, volume local)

- O Postgres **não publica porta**: só a rede interna do compose (`docker-compose.yml`, comentário no serviço `db`). Acesso do host via `docker compose exec db psql -U postgres -d laro`.
- `DATABASE_URL` só no `.env` da VM — nunca no repo, nunca no frontend (não existe frontend).
- O projeto é single-tenant e usa a role dona do banco (`POSTGRES_USER`). Aceito por simplicidade; revisitar se um dia expor API.
- **Backup** (cópia única fora do volume `laro_pgdata` na VM: `~/laro_mvp_tracker/backup_sim_teste.sql`, dump de 2026-11-23; arquivo pequeno porque os dados do MVP ainda não incluem históricos acumulados):

```bash
# dump de leitura (nome de arquivo com data, sem pessoal):
docker compose exec db pg_dump -U postgres laro > backup_$(date +%F).sql
```

- Restaurações do dump já validadas:
  - 2026-11-23, migração pra VM nova: `DROP SCHEMA public CASCADE; CREATE SCHEMA public` + `psql < dump` no banco de produção.
  - 2026-11-23, **simulação em container descartável** (procedimento abaixo): dump de produção (11K, 6 tabelas) restaurado num `postgres:16` paralelo (sem porta publicada, volume temporário) com `psql -v ON_ERROR_STOP=1` — zero erros e `count(*)` de todas as tabelas idênticos a produção.

```bash
# simulação de restore (não toca na produção; container morre depois):
cd ~/laro_mvp_tracker
docker compose exec db pg_dump -U postgres laro > backup_sim_teste.sql
docker run -d --name laro-db-teste -e POSTGRES_PASSWORD=teste -e POSTGRES_DB=laro postgres:16
# esperar: for i in $(seq 1 30); do docker exec laro-db-teste pg_isready -U postgres -d laro && break; sleep 1; done
docker cp backup_sim_teste.sql laro-db-teste:/tmp/
docker exec laro-db-teste psql -U postgres -d laro -v ON_ERROR_STOP=1 -f /tmp/backup_sim_teste.sql | tail -15
docker rm -f laro-db-teste
```

## 3. VM Oracle

Comandos de **leitura** para o dono executar na VM (mascare IPs antes de devolver a saída):

```bash
ss -tlnp
docker compose -f ~/laro_mvp_tracker/docker-compose.yml ps
sudo ufw status verbose
sudo sshd -T | grep -Ei 'passwordauthentication|permitrootlogin|pubkeyauthentication'
stat -c '%a %U:%G %n' ~/laro_mvp_tracker/.env
```

O último mostra só a permissão do `.env` (o esperado é `600`), sem ler o conteúdo.

No console da Oracle, confira a **Security List**: a única porta pública deve ser **22 (SSH)**. O bot não expõe porta alguma — o `/health` escuta apenas dentro do container (checado pelo docker healthcheck, `127.0.0.1` no container, não publicadão).

Boas práticas:

- acesso só por chave SSH (senha desativada no `sshd`);
- `.env` com permissão 600;
- atualizações automáticas do sistema (`unattended-upgrades`);
- usuário comum (não root), com grupo `docker`.

## 4. Bot e Docker

- **Token:** do Discord Developer Portal, só no `.env` da VM e no `.env` local de dev (fora do repo). Se vazar: resetar o token no portal **antes** de qualquer outra coisa.
- **Healthcheck:** `/health` deve responder **503** até pronto e **200** depois; `HEALTH_PORT=0` desliga o servidor (conta como saudável). O autoheal e o docker healthcheck dependem desse contrato.
- **Resiliência em camadas** (verificar as três):

| Camada | Proteção | Sintoma quando falta |
|---|---|---|
| Crash | `restart: unless-stopped` | container morre e não volta |
| Travado | `laro-autoheal` reinicia unhealthy | bot vivo mas sem responder |
| Tudo morto | healthchecks.io (ping a cada 60s, period/grace 10 min) → e-mail | ninguém sabe que caiu |
| VM em uso indevido | alarme Oracle `laro-cpu-alta` (CpuUtilization > 80% por 10 min, OCI Notifications → e-mail, repeat 15 min) | criptominerado na E2.1.Micro |

- **Dependências:** `pip-audit -r src/requirements.lock --strict` roda no job `audit` da CI; Dependabot (pip, actions, docker) abre PRs semanais.
- **Análise de código:** CodeQL pelo setup padrão do GitHub (Security → Code scanning; Python + Actions workflows, on push + semanal) — fora do `ci.yml`, gerenciado pelo GitHub. Alerts aparecem em Security → Code scanning; aliatar não é aceitar: triar antes.
- **Reports de vulnerabilidade:** `SECURITY.md` aponta para o private vulnerability reporting (ligado nas configurações do repo, canal privado na aba Security) — nenhum e-mail exposto.
- **Imagem base:** `python:3.15.2-alpine` — atualizações via Dependabot (ecosystem docker).

## 5. Segurança do bot

- **Entrada:** tudo que o bot processa vem do Discord. Comandos só com o prefixo `!`; partes soltas são strings — nada vira SQL direto (acesso ao banco por asyncpg **parametrizado**, `$1`).
- **Permissões:** comandos admin (ex.: `!setmvpchannel`, `!setpingrole`) exigem a permissão Discord *Gerenciar Servidor* (checada no dispatcher `ADMIN_COMMANDS` em `event/on_message.py`). Melhoras futuras: checagem também por role no banco.
- **Pings:** a role do aviso de respawn é pingada só no canal configurado; a lista de MVPs nunca menciona (allowed_mentions desativado no painel).
- **Interações:** botões/selects do painel marcam `interaction.user` e só o dono da ação confirma (deleção);
- **Logs:** sem conteúdo de mensagem de usuário; eventos nos logs são do ciclo de vida do bot (conexão, carga de settings, health).
- Comandos via DM são ignorados (`message.guild is None` → return).

## 6. CI e proteção da branch

- Workflow único (`.github/workflows/ci.yml`), `permissions: contents: read`, três jobs: `checks` (ruff + pytest em 3.13/3.14/3.15), `types` (pyright basic) e `audit` (pip-audit).
- pyright resolve imports via `.venv` (`pyrightconfig.json`, `venvPath`); o job `types` cria o `.venv` no runner e instala também `pytest` (não está no lockfile).
- Dependabot atualiza o próprio `ci.yml` (ecosystem github-actions); conferir `actions/checkout@vN`/`setup-python@vN` quando abrir os bumps.
- Proteção da `main`: ruleset `protege-main` (detalhes e como conferir: `docs/configuracao-repositorio.md`).
- Fluxo: PR → checks verdes → **Rebase and merge**. Nunca push direto.

## O que o agente não deve fazer sem confirmação

DROP, TRUNCATE, apagar volumes ou branches, mudar firewall ou Security List, reiniciar serviços na VM, aplicar migração na produção, reescrever o histórico do Git ou fazer push forçado. Na VM, o agente só **sugere comandos de leitura**; o dono executa e devolve a saída mascarada.
