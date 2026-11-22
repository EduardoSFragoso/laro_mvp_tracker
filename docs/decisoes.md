# Decisões do projeto (histórico do refactor)

Registro das decisões tomadas ao refatorar o [yellowtracker](https://github.com/victorgawk/yellowtracker)
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
| `/custom` e `/mobile` | **Comentados em `app.py`** (código dos módulos mantido, comando fora da sincronização) | Não têm uso no LATAM (sem tempos custom cadastrados; layout mobile herdado do server original) |
| `/setminingchannel` e `/unsetminingchannel` | **Removidos por completo** | Mineração não existe no LATAM |
| `/gmc` e `/hh` | **Removidos por completo** (código, testes e emojis — decisão atualizada em 22/11/2026) | Não existem no LATAM; a abordagem antiga de responder "—" não valia a manutenção |
| Pacote `gmctokens` | **Removido por completo** | Gerenciador de tokens do GMC de server privado antigo; referenciava tabelas que nunca existiram no schema novo |

No LATAM a lista de eventos (`WeeklyEvent.DATA`) só contém WoE e `EVENT_TIMER_TYPES=['woe']` em `event_timer.py`.
Se um dia a Gravity lançar GMC/HH, basta recriar os comandos (o histórico mostra que já responderam "—" via `event_service`) e acrescentar os agendamentos.
Para reativar `/custom` e `/mobile`, basta descomentar os blocos em `app.py` e o import correspondente (os módulos `command/custom.py` e `command/mobile.py` continuam no projeto).

## Remoção da mineração

Remoção total (código, schema e testes): comandos de canal, `MiningLocation`, `TrackType.MINING`,
tabelas `mining*` do SQL, coluna de canal na tabela `guild` e todas as referências em
serviços/utils/eventos/READMEs. O seed (`sql/seed_mvp_latam.sql`) inclui uma migração que faz
`DROP TABLE IF EXISTS` das tabelas legadas de mining para quem rodava o bot antigo.

## Padrões de desenvolvimento (AGENTS.md)

Um documento de padrões (`AGENTS.md`, não versionado no repo) guiou o último commit (`93e9baa`):

- **Ruff** como linter + formatter (`pyproject.toml`): line-length 120, alvo py313, regras `E/W/F/I/B/UP/C4/SIM`, aspas simples
- **Exceções específicas**: `domain/exceptions.py` (`BotConfigurationError`, `PoolNotInitializedError`) no lugar de `Exception` genérica; handlers estreitados (`discord.DiscordException`, `asyncpg.PostgresError`)
- **DRY**: `event_service` refatorado em `_evt_map` genérico + `build_evt_embed` compartilhado; `/gmc`, `/hh` e `/woe` viram chamadores finos
- **Bug corrigido no caminho** (F811): em `src/app.py`, os handlers `on_ready`/`on_message`/etc. eram sobrescritos pelos módulos importados de mesmo nome — agora importados com alias

## Documentação

- Dois READMEs: `README.md` (pt-BR, padrão) e `README.en.md` (inglês), com links cruzados

## Ambiente local (Docker)

- `docker-compose.yml` (raiz) refeito: serviço `db` (postgres:16, aplica `sql/yellowtracker.sql` + `sql/seed_mvp_latam.sql` na primeira subida; volume `laro_pgdata` persiste, `down -v` recomeça do zero) + serviço `bot` (build do `Dockerfile`, `depends_on` com healthcheck do Postgres)
- `.env.example` na raiz lista todas as variáveis carregadas por `src/yellowtracker/config.py`
- Removido o `postgres/docker-compose.yml` genérico antigo (substituído pelo serviço `db`); o `docker.env` original deu lugar ao `.env` da raiz

## Mapa exibido como código kRO (navi)

A tabela de rastreio (e o select de desambiguação) mostra o **código kRO do mapa** (navi, ex.: `gon_dun03`) em vez do nome em português — é o código que URLs de navegação (`/navi gon_dun03`) entendem. Decisões:

- Nova coluna `navi text` em `mvp` (schema completo em `sql/yellowtracker.sql` e migração `ADD COLUMN IF NOT EXISTS` no seed de upgrade), populada para os 64 MVPs do LATAM (pesquisa cruzada RMS renewal/kRO + rAthena + divine-pride/RagnaPlace; fontes por entrada em `docs/mvp-latam.md`)
- `Mvp.navi` + property `display_map` (navi com fallback para o nome pt): um único ponto de troca em `channel_service`/`entry_service`
- Nome em português continua no banco, no autocomplete e nas respostas do `/track`; só a exibição do mapa muda

## Comandos por prefixo de mensagem (sem slash commands)

Os comandos do bot deixaram de ser slash commands e passaram a ser **mensagens com prefixo** (padrão `!`, configurável em `COMMAND_PREFIX`), porque a lista `/` do Discord mistura os comandos de todos os bots do server e poluía a busca. Como o prefixo só tem um caractere, a resposta de "comando não existe" só é enviada dentro do canal de rastreio — fora dele, `!qualquer-coisa` de outros bots é ignorado sem ruído. Decisões:

- `LaroCommandTree`, todos os `@tree.command`, o autocomplete e os `tree.sync` foram removidos de `src/app.py`; `on_ready`/`on_guild_join` não sincronizam mais nada e `GUILD_ID` ficou sem efeito
- A interpretação acontece no `on_message` (`_dispatch_cmd`): `!track|woe|settings|clean|timezone|unsettimezone|setmvpchannel|unsetmvpchannel|custom|mobile` + `!`/`!help`; desconhecidos respondem com dica; mensagens sem o prefixo são ignoradas (e apagadas pela rotina de limpeza)
- Os módulos em `command/` foram convertidos em funções `*_core(bot, message, ...)` reutilizáveis; `custom` e `mobile` continuam desligados (não despachados)
- O botão **➕ TRACK MVP** e o modal continuam como interface alternativa (o modal não suporta autocomplete na API do Discord — feature request aberta, discussion #6212 do discord-api; select menu em modal limita a 25 opções < 64 MVPs)
- **Mensagem fixa de instruções**: canal de track agora tem, antes da tabela, um embed "📖 Como usar" persistente (`ChannelState.id_help_message`), recriado/reordenado automaticamente pelo `init_channel` e protegido da rotina de limpeza
- Trade-off aceito: sair do slash remove o autocomplete do client; a ambiguidade de nomes continua resolvida pelo select (TrackView)

## Pendências (não bloqueiam o repo)

1. ~~`.env` real (token do bot + `DATABASE_URL`) para smoke test com Discord + Postgres~~ **Feito**: bot conectou via Docker (`docker compose up -d`), sincronizou slash commands e subiu o pool do Postgres (22/11/2026).
2. ~~Validação do SQL num Postgres de verdade~~ **Feito**: o Postgres do Docker aplicou `sql/yellowtracker.sql` + `sql/seed_mvp_latam.sql` na primeira subida; `SELECT count(*) FROM mvp` = 64 (22/11/2026). A validação estática continua disponível via `scripts/validate_sql.py`.
