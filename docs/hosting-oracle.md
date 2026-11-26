# Deploy em VM Oracle Cloud (Always Free) com alarmes

Guia de hospedagem do bot em uma VM sempre-free da Oracle com:
- **auto-recuperação** (postar de novo sozinho após queda/reboot),
- **healthcheck** interno (Docker),
- **alarme externo** quando o bot parar de responder.

## 1. Criar a VM

Console Oracle Cloud → **Compute → Instances → Create Instance**.

| Opção | Valor recomendado |
|---|---|
| Shape | **A1.Flex (ARM)** — Always Free até 4 OCPU / 24 GB. Alternativa: VM.Standard.E2.1.Micro (AMD, 1 OCPU / 1 GB) |
| OS | **Canonical Ubuntu 24.04** (ou 22.04) |
| SSH key | Sua chave pública |

O bot só faz **chamadas de saída** (Discord + Postgres local + heartbeat) — ele não precisa de portas de entrada. Antes de alterar a **Security List**, confira todas as VMs associadas: a lista padrão pode ser compartilhada por outros projetos. Neste ambiente, duas VMs usam a lista padrão e a regra **443/TCP** é necessária para o outro projeto; não a remova para atender apenas ao Laro. Mantenha SSH (22/TCP) conforme o acesso administrativo.

ARM nota: a base do Dockerfile (`python:*-alpine`) é multi-arch (builda em aarch64),
mas os wheels de `asyncpg`/`aiohttp` para Python 3.15 aarch64 ainda não foram
provados nesta VM. Se o `docker compose build` falhar por falta de wheel, voltar
o Dockerfile para `python:3.14-alpine` e reabrir o PR de bump mais tarde.

## 2. Preparar o servidor

```bash
ssh ubuntu@IP_DA_VM

sudo apt update && sudo apt upgrade -y
# Docker (get.docker.com) — também ativa e habilita o serviço no boot
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu   # deslogar e logar de novo
sudo systemctl enable --now docker
```

## 3. Subir o bot

```bash
git clone https://github.com/EduardoSFragoso/laro_mvp_tracker.git
cd laro_mvp_tracker
cp .env.example .env
nano .env   # BOT_USER_TOKEN=... e POSTGRES_PASSWORD=<senha da VM>
            # (DATABASE_URL padrão do compose já serve)
docker compose up -d --build
docker compose logs -f --no-color bot   # Ctrl+C sai sem parar o bot
```

O `docker-compose.yml` já cobre a resiliência local:

- `restart: unless-stopped` no `db` e no `bot` — queda do processo volta sozinha;
- o Docker reinicia na inicialização da VM (reboot/migração/maintenance do Oracle);
- `healthcheck` do `bot` consulta `GET /health` (interno, porta 8080 não publicada):
  200 quando o tracker está pronto, 503 enquanto sobe.

Importante: o `db` **não publica porta alguma** — o Postgres fica apenas na
rede interna do compose; no host, acesse com
`docker compose exec db psql -U postgres -d laro`.

## 4. Alarme quando o bot parar (monitor externo)

O healthcheck do Docker não consegue avisar se a **VM inteira** cair — para isso
existe o heartbeat de saída:

1. Crie uma conta (gratuita) num monitor: **UptimeRobot** (Heartbeat monitor) ou **Better Stack** (Heartbeat).
2. Periodicidade sugerida: **5 minutos** — o monitor acusa queda quando não recebe ping dentro da janela.
3. Configure o canal do alarme: e-mail e/ou integração **Discord webhook** nas opções do monitor.
4. Pegue a URL do heartbeat (formato `https://heartbeat.../<id>`) e coloque no `.env` da VM:

```bash
HEARTBEAT_URL=https://heartbeat.uptimerobot.com/...
HEARTBEAT_SECS=60
docker compose up -d
```

O bot faz um `GET` na URL a cada `HEARTBEAT_SECS`. Se os pings param (VM morta,
rede fora, docker travado, bot crashado), o monitor dispara o alarme.

## 5. Camada extra (opcional)

- **Container travado sem crashar** (processo vivo, bot morto): o healthcheck marca
  o container `unhealthy` (visível em `docker ps`). Para reiniciar automaticamente
  nesse caso, adicione o container [`willfarrell/autoheal`](https://github.com/willfarrell/docker-autoheal)
  no compose.
- **Alarme no nível Oracle**: no console, **Observability → Alarm Definitions**
  dá para criar alarme de `CpuUtilization` (ex.: CPU = 0% por 15 min) como
  plano B independente do heartbeat.

## 6. Manutenção

```bash
cd laro_mvp_tracker
git pull
docker compose pull autoheal
docker compose up -d --build bot autoheal
docker compose logs --no-color --since 10m bot   # procurar Traceback
```

Backup do dado do bot (rastreios/roles/settings):

```bash
docker compose exec -T db pg_dump -U postgres laro > backup-$(date +%F).sql
# restaurar: cat backup.sql | docker compose exec -T db psql -U postgres -d laro
```
