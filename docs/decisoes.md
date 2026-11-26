# Decisões do projeto (histórico do refactor)

Registro das decisões tomadas ao refatorar o [Yellow Tracker](https://github.com/victorgawk/yellowtracker)
para o **Ragnarok Online LATAM** (servidor oficial da Gravity/GNJOY LATAM, lançado em 28/05/2025).
Este projeto foi movido para o repo público [laro_mvp_tracker](https://github.com/EduardoSFragoso/laro_mvp_tracker).

## Fontes de dados

- **Lista de MVPs e janelas de respawn**: [meurag.com/ferramentas/mvps](https://meurag.com/ferramentas/mvps) (nomes em pt-BR, t1/t2 exatamente como no meurag — sem "custom respawn"; `t1custom`/`t2custom` = NULL)
- **IDs dos mobs**: [ragnaplace.com/pt/rolatam-pt](https://ragnaplace.com/pt/rolatam-pt) (IDs kRO reais quando identificáveis; old-DB ids clássicos confirmados)
- Detalhes completos da pesquisa: [mvp-latam.md](mvp-latam.md)

Resultado: **64 MVPs** e 66 aliases no seed. `id_mob` é NULL para 7 MVPs sem ficha no ragnaplace
(Bruxa da Morte, Gorynych, Imperatriz Scaraba, Muspellskoll, Presas Flamejantes, Quimera Única, Rei Goblin) —
a thumbnail (ratemyserver) é simplesmente pulada nesses casos.

## Configurações regionais

- **Timezone padrão**: `America/Sao_Paulo` (UTC-3, horário do servidor)
- **WoE**: calendário oficial LATAM — **domingo, 20h–22h (UTC-3), WoE 1.0, 16 castelos**
  (fonte: [aviso oficial da GNJOY LATAM](https://ro.gnjoylatam.com/pt/news/notice/107))

## Recursos do projeto original x LATAM

| Recurso | Decisão | Motivo |
|---|---|---|
| `/woe` | Mantido, com o calendário oficial acima | Existe no LATAM |
| `/custom` e `/mobile` | Slash commands removidos; `!custom` desativado e `!mobile` ativo como comando por prefixo | Não há tempos custom no LATAM; o layout mobile continua útil |
| `/setminingchannel` e `/unsetminingchannel` | **Removidos por completo** | Mineração não existe no LATAM |
| `/gmc` e `/hh` | **Removidos por completo** (código, testes e emojis — decisão atualizada em 22/11/2026) | Não existem no LATAM; a abordagem antiga de responder "—" não valia a manutenção |
| Pacote `gmctokens` | **Removido por completo** (pacote Python e, em 22/11/2026, o schema legado `sql/gmctokens.sql` também) | Gerenciador de tokens do GMC de server privado antigo; referenciava tabelas que nunca existiram no schema novo |

No LATAM a lista de eventos (`WeeklyEvent.DATA`) só contém WoE e `EVENT_TIMER_TYPES=['woe']` em `event_timer.py`.
Se um dia a Gravity lançar GMC/HH, basta recriar os comandos (o histórico mostra que já responderam "—" via `event_service`) e acrescentar os agendamentos.
O comando por prefixo `!mobile` é despachado em `event/on_message.py`; `!custom` permanece fora do dispatcher.

## Remoção da mineração

Remoção total (código, schema e testes): comandos de canal, `MiningLocation`, `TrackType.MINING`,
tabelas `mining*` do SQL, coluna de canal na tabela `guild` e todas as referências em
serviços/utils/eventos/READMEs. O seed (`sql/seed_mvp_latam.sql`) inclui uma migração que faz
`DROP TABLE IF EXISTS` das tabelas legadas de mining para quem rodava o bot antigo.

## Padrões de desenvolvimento (AGENTS.md)

O documento de padrões `AGENTS.md` guiou o trabalho de manutenção. Na época do commit `93e9baa`, ele ainda não era versionado; hoje faz parte do repositório:

- **Ruff** como linter + formatter (`pyproject.toml`): line-length 120, alvo py313, regras `E/W/F/I/B/UP/C4/SIM`, aspas simples
- **Exceções específicas**: `domain/exceptions.py` (`BotConfigurationError`, `PoolNotInitializedError`) no lugar de `Exception` genérica; handlers estreitados (`discord.DiscordException`, `asyncpg.PostgresError`)
- **DRY**: `event_service` refatorado em `_evt_map` genérico + `build_evt_embed` compartilhado; `/gmc`, `/hh` e `/woe` viram chamadores finos
- **Bug corrigido no caminho** (F811): em `src/app.py`, os handlers `on_ready`/`on_message`/etc. eram sobrescritos pelos módulos importados de mesmo nome — agora importados com alias

## Documentação

- Dois READMEs: `README.md` (pt-BR, padrão) e `README.en.md` (inglês), com links cruzados

## Ambiente local (Docker)

- `docker-compose.yml` (raiz) refeito: serviço `db` (postgres:16, aplica `sql/laro.sql` + `sql/seed_mvp_latam.sql` na primeira subida; volume `laro_pgdata` persiste, `down -v` recomeça do zero) + serviço `bot` (build do `Dockerfile`, `depends_on` com healthcheck do Postgres)
- `.env.example` na raiz lista todas as variáveis carregadas por `src/laro/config.py`
- Removido o `postgres/docker-compose.yml` genérico antigo (substituído pelo serviço `db`); o `docker.env` original deu lugar ao `.env` da raiz

## Mapa exibido como código kRO (navi)

A tabela de rastreio (e o select de desambiguação) mostra o **código kRO do mapa** (navi, ex.: `gon_dun03`) em vez do nome em português — é o código que URLs de navegação (`/navi gon_dun03`) entendem. Decisões:

- Nova coluna `navi text` em `mvp` (schema completo em `sql/laro.sql` e migração `ADD COLUMN IF NOT EXISTS` no seed de upgrade), populada para os 64 MVPs do LATAM (pesquisa cruzada RMS renewal/kRO + rAthena + divine-pride/RagnaPlace; fontes por entrada em `docs/mvp-latam.md`)
- `Mvp.navi` + property `display_map` (navi com fallback para o nome pt): um único ponto de troca em `channel_service`/`entry_service`
- Nome em português continua no banco, no autocomplete e nas respostas do `/track`; só a exibição do mapa muda

## Comandos por prefixo de mensagem (sem slash commands)

Os comandos do bot deixaram de ser slash commands e passaram a ser **mensagens com prefixo** (padrão `!`, configurável em `COMMAND_PREFIX`), porque a lista `/` do Discord mistura os comandos de todos os bots do server e poluía a busca. Como o prefixo só tem um caractere, a resposta de "comando não existe" só é enviada dentro do canal de rastreio — fora dele, `!qualquer-coisa` de outros bots é ignorado sem ruído. Decisões:

- `LaroCommandTree`, todos os `@tree.command`, o autocomplete e os `tree.sync` foram removidos de `src/app.py`; `on_ready`/`on_guild_join` não sincronizam mais nada e `GUILD_ID` ficou sem efeito
- A interpretação acontece no `on_message` (`_dispatch_cmd`): `!track|woe|settings|clean|timezone|unsettimezone|setmvpchannel|unsetmvpchannel|mobile` + `!`/`!help`; desconhecidos respondem com dica; mensagens sem o prefixo são ignoradas (e apagadas pela rotina de limpeza)
- Os módulos em `command/` foram convertidos em funções `*_core(bot, message, ...)` reutilizáveis; `mobile` está ativo e exige permissão de administrador; `custom` continua desligado
- O botão **➕ TRACK MVP** e o modal continuam como interface alternativa (o modal não suporta autocomplete na API do Discord — feature request aberta, discussion #6212 do discord-api; select menu em modal limita a 25 opções < 64 MVPs)
- **Mensagem persistente de instruções**: canal de track tem, antes da tabela, um embed "📖 Como usar" (`ChannelState.id_help_message`), recriado/reordenado automaticamente pelo `init_channel` e protegido da rotina de limpeza; não é um pin do Discord
- Trade-off aceito: sair do slash remove o autocomplete do client; a ambiguidade de nomes continua resolvida pelo select (TrackView)

## Notificação de janela de respawn

Quando o `r1` (início da janela de respawn) de um MVP rastreado cruza 0, o timer do bot manda uma mensagem no canal de track com o horário aproximado de fechamento da janela (`r2`). Detalhes:

- Flag `TrackEntryState.notified` evita ping duplicado; o re-rastreio do mesmo MVP a reseta (`track_util.track_entry` e `UPDATE ... notified=FALSE` em `update_track_time`). A flag é **persistida** na coluna `mvp_guild.notified`: marcada `TRUE` no banco quando o aviso é enviado e restaurada no `load_db_entries`, então restart não re-pinga janelas já avisadas
- Dispara só na transição (`r1` em {0, -1}), então um MVP rastreado tarde não dispara ping atrasado nem na inicialização
- **Mensagem viva**: o aviso é um embed `ChannelState.notification_message` que permanece no canal enquanto houver janela aberta (`r1 <= 0 <= r2`) e é deletado quando a última fecha — ele nunca desaparece aos 10s (`DEL_MSG_AFTER_SECS`) como as outras mensagens (exceção em `is_msg_can_be_deleted`). No restart, o aviso existente é adotado (e duplicados, apagados) por `init_channel`
- **Ping opcional de role**: por padrão o aviso é silencioso (sem menção). `!setpingrole @role` grava `guild.id_notification_role` e passa a pingar só essa role quando uma janela nova abre; `!unsetpingrole` volta ao silencioso. Nunca se usa `@here`/`@everyone` — em canais populosos um ping geral seria invasivo (`AllowedMentions.none()` ou roles=[role])

## Permissões dos comandos

Comandos de configuração (`!timezone`, `!unsettimezone`, `!setmvpchannel`, `!unsetmvpchannel`, `!setpingrole`, `!unsetpingrole`, `!clean`, `!mobile`) exigem a permissão **Gerenciar Servidor** (checagem `guild_permissions.manage_guild` no `_dispatch_cmd`). Motivo: sem o gate, qualquer membro podia trocar a configuração do servidor. `!track`, `!woe` e `!settings` (leitura) continuam abertos. Comandos de dono do bot em DM (`!guilds` etc.) já eram restritos.

## Renome do pacote para `laro`

O bot era derivado do Yellow Tracker e herdou o pacote `src/yellowtracker`, o `sql/yellowtracker.sql` e os nomes de log. Para deixar o código com identidade própria: pacote renomeado para `src/laro`, SQL para `sql/laro.sql` e `fly.toml`/`pyproject.toml` para `laro` — apenas renome (nenhum comportamento muda). As referências históricas ao Yellow Tracker de origem ficam nos READMEs/decisões.

## Monitoramento para o deploy (VM Oracle)

Camadas, do mais interno ao mais externo (ver `docs/hosting-oracle.md`):

- **Auto-recuperação local**: `restart: unless-stopped` no compose + Docker habilitado no boot da VM. O Postgres não publica porta (rede interna do compose apenas).
- **Healthcheck do Docker**: o bot expõe `GET /health` (aiohttp, porta `HEALTH_PORT`, padrão 8080, não publicada e desligável com `HEALTH_PORT=0`); responde 200 só depois de `tracker_ready`. O healthcheck do compose marca o container `unhealthy` se o bot travar sem crashar.
- **Alarme externo**: o bot faz ping (`GET`) em `HEARTBEAT_URL` a cada `HEARTBEAT_SECS` (default 60s); um monitor externo (UptimeRobot/Better Stack) alerta quando os pings param — cobre queda da VM inteira, que o healthcheck local não vê. Ping falho não derruba o bot; `monitoring_service.py`.

## Pendências (não bloqueiam o repo)

1. ~~`.env` real (token do bot + `DATABASE_URL`) para smoke test com Discord + Postgres~~ **Feito**: bot conectou via Docker (`docker compose up -d`), sincronizou slash commands e subiu o pool do Postgres (22/11/2026).
2. ~~Validação do SQL num Postgres de verdade~~ **Feito**: o Postgres do Docker aplicou `sql/laro.sql` + `sql/seed_mvp_latam.sql` na primeira subida; `SELECT count(*) FROM mvp` = 64 (22/11/2026). A validação estática continua disponível via `scripts/validate_sql.py`.

## CI, Dependabot e proteção de branch (22/11/2026)

- **CI** (`.github/workflows/ci.yml`): ruff check + ruff format + pytest em Python 3.13, 3.14 e 3.15 (o 3.15 entrou por PR em 23/11/2026, quando a imagem Docker subiu para `python:3.15.2-alpine`; validado com build + smoke test locais), mais job de `pip-audit` contra o lockfile. Instalação pelo `src/requirements.lock` (closure de runtime pinado) em vez do `requirements.txt` (só diretas). Permissões do workflow reduzidas a `contents: read`.
- **Dependabot** (`.github/dependabot.yml`): PRs semanais para pip (`/src`), github-actions e docker.
- **Creds do Postgres**: saíram do compose para o `.env` da raiz (`POSTGRES_*`, interpoladas com defaults só de dev local); na VM a senha deve ser trocada antes do primeiro `compose up` (ver `docs/hosting-oracle.md`).
- **Branch protection da `main`**: ruleset `protege-main` ativo (22/11/2026) — *Require a pull request before merging*, *Require status checks to pass* com **checks (3.13)**, **checks (3.14)**, **checks (3.15)** e **audit** exigidos (a "lição" da CI vermelha mergida: o check obrigatório é a rede de segurança contra merge de código quebrado — não desmarcar; cada coluna da matriz gera um check com nome próprio e precisa de entrada própria no ruleset), *Require branches to be up to date*, *Block force pushes*, *Require conversation resolution* e *Require linear history* (sem merge commits). Fora do ruleset, único método de merge permitido é **Rebase and merge** — `main` linha reta, cada commit do PR entra com mensagem e hash próprios. Push direto na `main` recusado (GH013); tudo passa por branch + PR. Exceção emergencial: desativar o ruleset temporariamente (edit → toggle Enforcement) e reativar.
