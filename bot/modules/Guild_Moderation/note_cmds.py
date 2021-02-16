from datetime import datetime as dt
import discord

from wards import guild_moderator

from .module import guild_moderation_module as module
from .tickets import Ticket, describes_ticket, TicketType


@module.cmd("note",
            desc="Create a moderation note on a member.")
@guild_moderator()
async def cmd_note(ctx):
    """
    Usage``:
        {prefix}note <user>
    Description:
        Prompts for a note to write on the given user.
        The note is visible in the `modlog`, if set, and in the user's tickets.
    Related:
        ticket, tickets, ticketset
    """
    if not ctx.args:
        return await ctx.error_reply("No arguments given, nothing to do.")

    user = await ctx.find_member(ctx.args, interactive=True)
    if user is None:
        return

    note = await ctx.input("Please enter the note.")
    ticket = NoteTicket.create(
        ctx.guild.id,
        ctx.author.id,
        ctx.client.user.id,
        [user.id],
        reason=note
    )
    await ticket.post()
    await ctx.reply("Note created!")


@describes_ticket(TicketType.NOTE)
class NoteTicket(Ticket):
    @property
    def embed(self):
        """
        The note embed to be posted in the modlog.
        Overrides the original `Ticket.embed`.
        """
        # Base embed
        embed = discord.Embed(
            title="Ticket #{}".format(self.ticketgid),
            timestamp=dt.fromtimestamp(self.created_at)
        )
        embed.set_author(name="Note")

        # Moderator information
        mod_user = self._client.get_user(self.modid)
        if mod_user is not None:
            embed.set_footer(text="Created by: {}".format(mod_user), icon_url=mod_user.avatar_url)
        else:
            embed.set_footer(text="Created by: {}".format(self.modid))

        # Target information
        targets = '\n'.join("<@{0}> ({0})".format(targetid) for targetid in self.memberids)
        if len(self.memberids) == 1:
            embed.description = "`Subject`: {}".format(targets)
        else:
            embed.add_field(name="Subjects", value=targets, inline=False)

        # Reason
        if self.reason:
            embed.add_field(name='Note', value=self.reason, inline=False)

        return embed
