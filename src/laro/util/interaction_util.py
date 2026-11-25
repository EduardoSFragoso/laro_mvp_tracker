from __future__ import annotations

import discord


async def is_confirmation_owner_admin(interaction: discord.Interaction, requester_id: int) -> bool:
    """Allow only the requesting administrator to use confirmation controls."""
    member = interaction.user
    permissions = getattr(member, 'guild_permissions', None)
    if member.id == requester_id and permissions is not None and permissions.manage_guild:
        return True

    await interaction.response.send_message(
        'Apenas quem iniciou a ação e ainda tem a permissão Gerenciar Servidor pode usar estes botões.',
        ephemeral=True,
    )
    return False
