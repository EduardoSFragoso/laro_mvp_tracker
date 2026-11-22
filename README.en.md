# Yellow Tracker (Ragnarok Online LATAM)

Português | [English](README.en.md)

Yellow Tracker is a Discord bot to track MVPs, adapted for the **Ragnarok Online LATAM** server (the official Gravity/GNJOY LATAM server).

Based on the [original yellowtracker](https://github.com/victorgawk/yellowtracker), refactored (dataclasses, env-based settings, module-level services) and with the MVP list, respawn times and events updated for LATAM.

## Run locally

Prerequisites:

- Python 3.13+
- A Discord bot token
- A PostgreSQL database

1. In the PostgreSQL database, use the content from `sql/yellowtracker.sql` to create the initial database structure (tables + the LATAM MVP list).
2. Use the root [`.env.example`](.env.example) as a template and create a `.env` file with the following variables:
```properties
# REQUIRED (the bot fails to start without them)

BOT_USER_TOKEN=your Discord bot token
DATABASE_URL=your PostgreSQL URL in the format postgres://user:password@host:port/database

# OPTIONAL (the bot uses the default value if not set)

DEL_MSG_AFTER_SECS=time to delete a message in the track channel after its last update (default = 10 seconds)
TABLE_ENTRY_EXPIRATION_MINS=time to remove an entry from the table after the max respawn window is reached (default = 20 minutes)
TIMER_DELAY_SECS=bot timer delay in seconds (default = 5 seconds)
TIMEZONE=timezone used for HH:MM datetimes (default = America/Sao_Paulo)
COMMAND_PREFIX=chat command prefix (default = !)
```
3. In a terminal, go to the `src` folder.
4. Run `pip install -r requirements.txt` to install the dependencies.
5. Run `python app.py` to start the bot.

## Run with Docker Compose

The repo root has a `docker-compose.yml` that brings up **Postgres (with the schema + LATAM seed applied automatically) and the bot**:

1. Copy `.env.example` to `.env` in the root and fill in at least `BOT_USER_TOKEN` (the compose overrides `DATABASE_URL` to point at the `db` service).
2. `docker compose up --build`

The `laro_pgdata` volume persists the data; to start over, `docker compose down -v` (the SQL is applied again on the next start).
To run only Postgres and start the bot locally (from `src`, with `python app.py`): `docker compose up -d db` — in that case use `postgres://postgres:postgres@localhost:5432/laro` as the `DATABASE_URL`.

## Upgrading an existing database

If the database still holds the old MVP list, run `sql/seed_mvp_latam.sql` to rebuild the `mvp` table with the LATAM data:

```bash
psql "$DATABASE_URL" -f sql/seed_mvp_latam.sql
```

⚠️ The script is transactional and wipes the current MVPs and aliases (removing the tracks and guild rows tied to them). It also drops the legacy mining tables, since the mining tracking feature does not exist on the LATAM server.

## LATAM data

- **MVP list**: 64 entries with names and maps in Portuguese and respawn windows matching the LATAM community tracker (meurag.com/ferramentas/mvps). Details and sources in `docs/mvp-latam.md`.
- **Default timezone**: `America/Sao_Paulo` (Brasília time), same as the server time (UTC-3).
- **MVPs without an ID**: some of the new MVPs have a NULL `id_mob` in the database (it is only used for the preview thumbnail); the thumbnail is omitted in those cases.
- Full history of the refactor decisions (in Portuguese): [docs/decisoes.md](docs/decisoes.md).

## Usage

Define a channel in your Discord server to be used exclusively for MVP tracking (a brand-new channel is strongly recommended). Use the **!setmvpchannel** command. In this channel the bot keeps a help message and a table with the tracked MVPs and their remaining respawn times.

  - **WARNING**: after you use this command, **ALL** messages from the channel (if any) are erased irreversibly! Make sure you pick the right channel.

Inside an MVP channel, there are two ways to track a MVP:
- typing **!track MVP_NAME** or **!track MVP_NAME HHMM** (requires the **Message Content** intent; accepts the Portuguese name or the English alias — e.g. `!track amon ra 1234`, `!track atroce`, `!track brinaranea 1512`);
- pressing the **➕ TRACK MVP** button (opens a form).

Commands are **prefix-based messages** (default `!`, configurable in `COMMAND_PREFIX`) — instead of slash commands — so they do not mix with the slash commands of other bots on the `/` list. The table shows the **kRO map code** (navi, e.g. `gon_dun03`) instead of the Portuguese map name. Only messages starting with the prefix are processed; anything else is deleted automatically by the channel cleaning routine (requires the **Manage Messages** permission).

### Bot commands:

Command | Description
------- | ---------
**!track** `name` `time` | Report that MVP `name` died. The optional `time` argument sets the exact time of death, in the `HHMM` format, relative to the configured timezone or a custom timezone set with **!timezone**.
**!setmvpchannel** | Define the current channel as the MVP track channel.
**!unsetmvpchannel** | Undo the MVP track channel definition.
**!timezone** | Set a custom timezone for tracking when the time is given in `HHMM` syntax.
**!unsettimezone** | Remove the custom timezone.
**!settings** | Show the current bot settings.
**!clean** | Remove all tracked MVPs from the table (useful after a server reboot).
**!woe** | Show the War of Emperium (WoE) schedule: every Sunday, 8 PM to 10 PM server time (UTC-3).
**!** (or **!help**) | Show the command list.

> **Note:** the `/track` etc. commands no longer exist as **slash commands**; the original project's `custom`, `mobile`, `/gmc` and `/hh` features remain disabled/stripped on LATAM — custom and mobile have no use on this server, and GMC and Happy Hour do not exist on LATAM.

## MVP list (LATAM)

Names and maps as they appear on the server; respawn in minutes, as reported by the LATAM community tracker. "Aliases" are the English names also accepted when tracking (besides the Portuguese name).

Name | Aliases | Map | Respawn
---- | ------- | --- | -------
Abelha-Rainha | Mistress | Monte Mjolnir (4) | 120~130 min
Amon Ra | — | Subsolo da Pirâmide (2) | 60~70 min
Amon Ra do Pesadelo | Nightmare Amon Ra | Subsolo da Pirâmide (2) - Pesadelo | 60~70 min
Aranha Rainha | Brinaranea | Porão de Glastheim | 120~130 min
Árvore de Pitaya | Pitaya | Estufa de Pitayas | 360~370 min
Atroce | Atroce Ida | Planície de Ida | 180~190 min
Atroce | Atroce Audhumbla | Pradaria Audhumbla | 300~310 min
Atroce | Atroce Veins | Arredores de Veins (1) | 180~190 min
Atroce | Atroce Veins 2 | Arredores de Veins (2) | 360~370 min
Bafomé | Baphomet | Labirinto da Floresta (3) | 120~130 min
Bafomé Amaldiçoado | Cursed Baphomet | Castelo Amaldiçoado | 120~130 min
Belzebu | Beelzebub | Monastério (3) | 720~730 min
Besouro-Ladrão Dourado | GTB, Golden Thief Bug | Esgotos de Prontera (4) | 60~70 min
Bispo Decadente | FBH, Fallen Bishop | Monastério (2) | 120~130 min
Boitatá | Boitata | Profundezas das Cataratas | 120~130 min
Bruxa da Morte | Death Witch | Calabouço de Niflheim - Ópera em Ruínas | 180~190 min
Cavaleiro da Tempestade | SK, Stormy Knight | Fábrica de Brinquedos (2) | 67~77 min
Detale Esqueleto | Skeleton Detale | Caverna Subterrânea do Lago do Abismo (4) | 180~190 min
Detardeurus | Detale | Caverna Subterrânea do Lago do Abismo (3) | 180~190 min
Doppelganger | — | Calabouço de Geffen (2) | 120~130 min
Drácula | Dracula | Calabouço de Geffen (1) | 60~70 min
Drake | — | Navio Fantasma (2) | 120~130 min
Eddga | — | Floresta de Payon (10) | 120~130 min
Espadachim Egnigem | GEC, Egnigem Cenia | Biolaboratório (2) | 120~130 min
Faraó | Pharaoh | Esfinge (5) | 60~70 min
Flor do Luar | MF, Moonlight Flower | Caverna de Payon (4) | 60~70 min
Freeoni | Phreeoni | Deserto de Sograt (17) | 120~130 min
Gemaring | — | Ninho do Dragão (1) | 60~70 min
General Tartaruga | TG, Turtle General | Palácio Tartaruga | 60~70 min
Gorynych | — | Floresta Encantada (3) | 120~130 min
Hatii | Garm | Arredores de Lutie | 120~130 min
Ifrit | — | Vulcão de Thor (3) | 660~670 min
Imperatriz Scaraba | Empress Scaraba | Caverna Scaraba - Pesadelo | 120~130 min
Jungoliant | Jewel Ungoliant | Calabouço da Mina (3) | 120~130 min
Kiel-D-01 | Kiel | Fábrica de Robôs (2) | 120~180 min
Kraken | — | Túnel Submarino (5) | 140~150 min
Lady Branca | WL, White Lady, Bacsojin | Suei Long Gon | 116~126 min
Lady Tanee | LT, Tanee | Santuário Ancestral | 420~430 min
Leak | — | Vulcão Krakatau | 120~130 min
Lorde das Trevas | Dark Lord | Porão de Glastheim | 60~70 min
Maya | — | Formigueiro Infernal (2) | 120~130 min
Morroc Ferido | WM, Wounded Morroc | Deserto de Sograt (22) | 720~730 min
Muspellskoll | Skoll | Caverna de Magma (3) | 120~130 min
Orc Herói | OH, Orc Hero | Arredores de Geffen (3) | 60~70 min
Osíris | Osiris | Pirâmide (4) | 60~70 min
Pesar Noturno | Gloom Under Night | Santuário de Freya (5) | 300~310 min
Presas Flamejantes | Burning Fang | Labirinto de Oz (2) | 360~370 min
Quimera Única | Chimeratheone | Laboratório Abandonado de Amicitia | 180~190 min
Quimera Venenosa | Venomous Chimera | Laboratório Werner | 60~70 min
R001-Bestia | — | Rudus 4º Andar - Área de Descarte de Experimentos | 180~190 min
R48-85-Bestia | — | Rudus, depósito de rejeitos (2) | 60~70 min
Rainha Scaraba | QS, Queen Scaraba | Caverna Scaraba | 120~130 min
Rei Goblin | Goblin King | Câmara Desconhecida da Torre do Relógio | 1200~1210 min
RSX-0806 | — | Calabouço da Mina (2) | 125~135 min
Samurai Encarnado | Samurai Specter | Templo Subterrâneo | 91~101 min
Senhor das Trevas | Dark Lord | Cemitério de Glastheim | 60~70 min
Senhor das Trevas | Dark Lord | Cemitério Amaldiçoado | 60~70 min
Senhor dos Mortos | LOD, Lord of the Dead | Nifflheim | 133~143 min
Senhor dos Orcs | OL, Orc Lord | Arredores de Geffen (10) | 120~130 min
Serpente Suprema | ESL, Evil Snake Lord | Terra das Fadas | 94~104 min
Tao Gunka | Tao | Karu, a Caverna do Oeste | 300~310 min
Valquíria Randgris | VR, Valkyrie Randgris | Templo de Odin (3) | 480~490 min
Vesper | — | Centro de Juperos | 120~130 min
Vigia do Tempo | Time Holder | Torre Distorcida (3) | 120~130 min

## Tests and validation

```bash
pip install -r requirements.txt pytest
pytest
python scripts/validate_sql.py  # validates the SQL syntax and seed counts (requires sqlglot)
```

## Fly.io deploy

The project keeps the original `fly.toml` and `Dockerfile`. The current root `docker-compose.yml` brings up Postgres + the bot, configured by the root `.env` (template: `.env.example`).
