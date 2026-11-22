# Laro MVP Tracker (Ragnarok Online LATAM)

[English](README.en.md) | Português

Laro MVP Tracker é um bot do Discord para rastrear MVPs, adaptado para o servidor **Ragnarok Online LATAM** (servidor oficial da Gravity/GNJOY LATAM).

Baseado no [Yellow Tracker original](https://github.com/victorgawk/yellowtracker), refatorado (dataclasses, settings via env, services como módulos) e com a lista de MVPs, tempos de respawn e eventos atualizados para o LATAM.

## Rodar localmente

Pré-requisitos:

- Python 3.13+
- Um token de bot do Discord
- Um banco de dados PostgreSQL

1. No PostgreSQL, use o conteúdo do arquivo `sql/laro.sql` para criar a estrutura inicial do banco (tabelas + lista de MVPs do LATAM).
2. Use o [`.env.example`](.env.example) da raiz como modelo e crie um arquivo `.env` com as variáveis:
```properties
# OBRIGATÓRIAS (o bot falha ao iniciar sem elas)

BOT_USER_TOKEN=seu token de bot do Discord
DATABASE_URL=sua URL do PostgreSQL no formato postgres://usuario:senha@host:porta/banco

# OPCIONAIS (o bot usa os valores padrão se não forem definidas)

DEL_MSG_AFTER_SECS=tempo de exclusão de mensagem no canal de rastreio após a última atualização (padrão = 10 segundos)
TABLE_ENTRY_EXPIRATION_MINS=tempo para remover a entrada da tabela após alcance máximo de respawn (padrão = 20 minutos)
TIMER_DELAY_SECS=atraso do timer do bot em segundos (padrão = 5 segundos)
TIMEZONE=timezone usada para horários em formato HH:MM (padrão = America/Sao_Paulo)
COMMAND_PREFIX=prefixo dos comandos do bot no chat (padrão = !)
```
3. Em um terminal, vá até a pasta `src`.
4. Execute `pip install -r requirements.txt` para instalar as dependências.
5. Execute `python app.py` para iniciar o bot.

## Rodar com Docker Compose

A raiz tem um `docker-compose.yml` que sobe **Postgres (com schema + seed LATAM aplicados automaticamente) e o bot**:

1. Copie `.env.example` para `.env` na raiz e preencha ao menos `BOT_USER_TOKEN` (a `DATABASE_URL` é sobrescrita pelo compose para apontar ao serviço `db`).
2. `docker compose up --build`

> Para hospedar o bot 24/7 em uma VM Oracle Cloud (Always Free) com auto-recuperação e alarmes externos, veja [docs/hosting-oracle.md](docs/hosting-oracle.md).

O volume `laro_pgdata` persiste os dados; para recomeçar do zero, `docker compose down -v` (na próxima subida o SQL é aplicado de novo).
Para usar só o Postgres e rodar o bot localmente (a partir de `src`, com `python app.py`): descomente o `ports` do serviço `db` no compose (`docker compose up -d db`) — nesse caso use `postgres://postgres:postgres@localhost:5432/laro` na `DATABASE_URL`.

## Atualizando um banco já existente

Se o banco já tinha a lista antiga de MVPs, rode `sql/seed_mvp_latam.sql` para recriar a tabela `mvp` com os dados do LATAM:

```bash
psql "$DATABASE_URL" -f sql/seed_mvp_latam.sql
```

⚠️ O script é transacional e remove os MVPs e apelidos atuais (apagando também os rastreios e guildas ligados a eles).

## Dados do LATAM

- **Lista de MVPs**: 64 entradas com nomes e mapas em português e janelas de respawn conforme o rastreador da comunidade (meurag.com/ferramentas/mvps). Detalhes e fontes em `docs/mvp-latam.md`.
- **Timezone padrão**: `America/Sao_Paulo` (horário de Brasília), igual ao horário do servidor (UTC-3).
- **MVPs sem ID**: alguns MVPs novos não têm `id_mob` no banco (usado só para a miniatura da pré-visualização); o thumbnail é omitido nesses casos.
- Histórico completo das decisões do refactor: [docs/decisoes.md](docs/decisoes.md).

## Como usar

Defina um canal do seu servidor do Discord para ser usado exclusivamente no rastreamento de MVPs (recomendado um canal novo para isso). Use o comando **!setmvpchannel**. Nesse canal o bot mantém uma mensagem de instruções e uma tabela com os MVPs rastreados e os tempos restantes para o respawn.

  - **ATENÇÃO**: ao usar esse comando, **TODAS** as mensagens do canal (se houver) serão apagadas de forma irreversível! Escolha o canal certo.

Dentro de um canal de MVPs, há duas formas de rastrear:
- digitando **!track NOME_DE_MVP** (sem horário = morreu agora) ou **!track NOME_DE_MVP HHMM** (requer permissão **Message Content**; aceita nome em português ou apelido em inglês — ex.: `!track amon ra 1234`, `!track atroce`, `!track brinaranea 1512`);
- pressionando o botão **➕ TRACK MVP** (abre um formulário no Discord).

Quando a janela de respawn de um MVP abrir (início do tempo mínimo de respawn), o bot posta um aviso no canal de track e mostra até que horário a janela fica aberta — o aviso **fica no canal até a última janela fechar** (não é apagado pela limpeza automática). Por padrão o aviso **não pinga ninguém**; com `!setpingrole @role` o bot passa a pingar a role escolhida (nunca `@here`/`@everyone`) a cada janela nova que abrir.

Comandos de configuração (`!timezone`, `!setmvpchannel`/`!unsetmvpchannel`, `!setpingrole`/`!unsetpingrole`, `!clean`) exigem a permissão **Gerenciar Servidor**.

Os comandos são **mensagens com prefixo** (padrão `!`, configurável em `COMMAND_PREFIX`) — em vez de slash commands — para não aparecer misturados aos comandos de outros bots na lista `/`. A tabela exibe o **código kRO do mapa** (navi, ex.: `gon_dun03`) em vez do nome em português. Só mensagens que começam com o prefixo são processadas; as demais são apagadas automaticamente pela rotina de limpeza do canal (requer permissão **Manage Messages**).

Como não há mais lista de comandos na barra `/`, a descoberta funciona assim:
- Assim que um canal é definido, o bot fixa nele um embed **📖 Como usar** com a lista de comandos e exemplos — esse aviso fica permanentemente acima da tabela.
- O bot aparece na lista de membros com o status "`!` para ver os comandos do MVP Tracker".
- Dentro do canal, `!track` (sem argumentos) ou `!help` mostra a lista de comandos.

O horário da morte pode ser informado como `2035` ou `20:35` (HHMM, timezone do servidor ou a customizada com `!timezone`).

### Comandos do bot:

Comando | Descrição
------- | ---------
**!track** `nome` `hora` | Registra que o MVP `nome` morreu. O argumento `hora` determina o horário exato da morte, no formato `HHMM`, relativo à timezone configurada ou a uma timezone customizada definida com **!timezone**.
**!setmvpchannel** | Define o canal atual como canal de rastreio de MVPs.
**!unsetmvpchannel** | Cancela o canal de rastreio de MVPs.
**!timezone** | Define uma timezone customizada para o rastreio quando o horário é informado via `HHMM`.
**!unsettimezone** | Remove a timezone customizada.
**!settings** | Mostra as configurações atuais do bot.
**!clean** | Remove todos os MVPs rastreados da tabela (útil após reinícios do servidor).
**!woe** | Mostra o horário da Guerra do Emperium (WoE): todo domingo, das 20h às 22h (horário do servidor, UTC-3).
**!** (ou **!help**) | Mostra a lista de comandos.

> **Nota:** os comandos `/track` etc. deixaram de existir como **slash commands**; `custom`, `mobile`, `/gmc` e `/hh` do projeto original seguem desativados/sem código no LATAM — custom e mobile não têm uso no servidor, e GMC e Happy Hour não existem no LATAM.

## Lista de MVPs (LATAM)

Nomes e mapas conforme o servidor; respawn em minutos, conforme o rastreador da comunidade LATAM. "Apelidos" são os nomes reconhecidos em inglês no rastreio (além do nome em português).

Nome | Apelidos | Mapa | Respawn
---- | -------- | ---- | -------
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

## Testes e validação

```bash
pip install -r requirements.txt pytest
pytest
python scripts/validate_sql.py  # valida sintaxe e contagens do SQL (requer sqlglot)
```

## Deploy no Fly.io

O projeto mantém o `fly.toml` e o `Dockerfile` originais. O `docker-compose.yml` atual sobe Postgres + bot pela raiz, configurados pelo `.env` (modelo: `.env.example`).
