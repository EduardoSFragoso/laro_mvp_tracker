from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiohttp import web

from laro.domain.bot import Bot


log = logging.getLogger(__name__)


async def run_health_server(bot: Bot) -> None:
    """HTTP server for the deploy healthcheck (docs/hosting-oracle.md).

    GET /health answers 200 when the tracker is ready, 503 otherwise. Docker's
    healthcheck (or a local monitor) uses it to see the bot beyond "process is
    alive". Port 0 (HEALTH_PORT=0) disables it.
    """
    port = bot.settings.health_port
    if port == 0:
        return
    app = web.Application()
    app['bot'] = bot

    async def health(request: web.Request) -> web.Response:
        if bot.tracker_ready:
            return web.Response(text='ok')
        return web.Response(status=503, text='starting')

    app.router.add_get('/health', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    log.info(f'Health server listening on port {port}.')
    # Keeps the task alive; the site runs on the same loop.
    while True:
        await asyncio.sleep(3600)


async def run_heartbeat(bot: Bot) -> None:
    """Pings HEARTBEAT_URL periodically; the external monitor (UptimeRobot,
    Better Stack, ...) alerts when the pings stop. Outbound only, so the VM
    keeps having no open inbound ports. No URL = disabled."""
    url = bot.settings.heartbeat_url
    if url is None:
        return
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status >= 400:
                        log.warning(f'Heartbeat ping answered HTTP {response.status}.')
            except asyncio.CancelledError:
                raise
            except Exception:
                # Falha de rede não derruba o bot: o alarme do monitor externo
                # continua cobrindo (o ping perdido é o que dispara o alerta).
                log.warning('Heartbeat ping failed.', exc_info=True)
            await asyncio.sleep(bot.settings.heartbeat_secs)
