import asyncio
from typing import List

import disnake
from disnake.ext import commands

from .. import classes
from ..main import bot


def none_found(item: str):
    return disnake.Embed(
        title="We've been combing the desert for hours!",
        description=f"No {item}s have been found for this user",
    )


class Notes(disnake.ui.View):
    def __init__(self, notes: List[classes.Note], user: disnake.User):
        super().__init__(timeout=None)
        self.user = user

        self.notes = notes
        self.notes_count = 0

        self.first_page.disabled = True
        self.prev_page.disabled = True

        if len(notes) == 1:
            self.next_page.disabled = True
            self.last_page.disabled = True

    @disnake.ui.button(label="⏮", style=disnake.ButtonStyle.blurple)
    async def first_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.notes_count = 0
        embed = self.notes[self.notes_count].parse()
        embed.set_footer(text=f"Note {self.notes_count + 1} of {len(self.notes)}")

        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="◀", style=disnake.ButtonStyle.primary)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.notes_count -= 1
        embed = self.notes[self.notes_count].parse()
        embed.set_footer(text=f"Note {self.notes_count + 1} of {len(self.notes)}")

        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.notes_count == 0:
            self.first_page.disabled = True
            self.prev_page.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="▶", style=disnake.ButtonStyle.primary)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.notes_count += 1
        embed = self.notes[self.notes_count].parse()
        embed.set_footer(text=f"Note {self.notes_count + 1} of {len(self.notes)}")

        self.first_page.disabled = False
        self.prev_page.disabled = False
        if self.notes_count == len(self.notes) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="️⏭", style=disnake.ButtonStyle.primary)
    async def last_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.notes_count = len(self.notes) - 1
        embed = self.notes[self.notes_count].parse()
        embed.set_footer(text=f"Note {self.notes_count + 1} of {len(self.notes)}")

        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="✖", style=disnake.ButtonStyle.red)
    async def delete(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.edit_message(
            embed=disnake.Embed(
                title="Are you sure?",
                description="This will delete the note and cannot be undone",
                colour=disnake.Colour.blurple(),
            ),
            view=AreYouSure("delete note", self),
        )


class AreYouSure(disnake.ui.View):
    def __init__(self, action: str, view: Notes):
        super().__init__(timeout=None)
        self.action = action
        self.view = view

    @disnake.ui.button(label="✖", style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.edit_message(
            embed=disnake.Embed(
                title="Cancelled",
                description="The action has been cancelled, no changes have been made",
                colour=disnake.Colour.blurple(),
            ),
            view=None,
        )

    @disnake.ui.button(label="✓", style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if self.action == "delete note":
            server = classes.server(interaction.guild_id)
            del server.get_user(self.view.user.id).notes[self.view.notes_count]
            del self.view.notes[self.view.notes_count]
            server.save()

            if self.view.notes_count > 0:
                self.view.notes_count -= 1
                embed = self.view.notes[self.view.notes_count].parse()
                embed.set_footer(text=f"Note {self.view.notes_count + 1} of {len(self.view.notes)}")

                if len(self.view.notes) == 1:
                    self.view.first_page.disabled = True
                    self.view.prev_page.disabled = True
                    self.view.next_page.disabled = True
                    self.view.last_page.disabled = True

                await interaction.response.edit_message(embed=embed, view=self.view)
            else:
                if len(self.view.notes) == 1:
                    embed = self.view.notes[self.view.notes_count].parse()
                    embed.set_footer(text=f"Note {self.view.notes_count + 1} of {len(self.view.notes)}")

                    self.view.first_page.disabled = True
                    self.view.prev_page.disabled = True
                    self.view.next_page.disabled = True
                    self.view.last_page.disabled = True

                    await interaction.response.edit_message(embed=embed, view=self.view)
                else:
                    await interaction.response.edit_message(embed=none_found("note"), view=None)


class Reason(disnake.ui.Modal):
    def __init__(self, text) -> None:
        components = [
            disnake.ui.TextInput(
                label=text,
                placeholder="Poured milk before cereal",
                custom_id="reason",
                style=disnake.TextInputStyle.long,
                max_length=512,
                required=False,
            ),
        ]
        super().__init__(title="Provide a Reason", custom_id="reason_modal", components=components)

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.response.send_message(f"Something went wrong: {error}", ephemeral=True)


class Actions(disnake.ui.View):
    def __init__(self, ctx, user):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.user = user

    @disnake.ui.button(label="🗒️ Notes", style=disnake.ButtonStyle.primary)
    async def note(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        server = classes.server(self.ctx.guild.id)

        if server.get_user(self.user.id) is None:
            u = classes.User(self.user.id)
            server.add_user(u)

        user_ = server.get_user(self.user.id)
        notes = user_.notes

        if len(notes) == 0:
            await interaction.response.edit_message(embed=none_found("note"), view=None)
            return

        await interaction.response.edit_message(embed=notes[0].parse(), view=Notes(notes, self.user))

    @disnake.ui.button(label="⚠️ Warn", style=disnake.ButtonStyle.primary)
    async def warn(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        ctx = self.ctx
        user = self.user

        await interaction.response.send_modal(modal=Reason("Warn Reason:"))

        try:
            modal_inter: disnake.ModalInteraction = await bot.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "reason_modal" and i.author.id == ctx.author.id,
                timeout=300,
            )
        except asyncio.TimeoutError:
            return

        embed = disnake.Embed(
            title="User Warned",
            description=f"User {user.name}#{user.discriminator} has been warned!\n\n",
            colour=disnake.Colour.gold(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for custom_id, value in modal_inter.text_values.items():
            embed.add_field(name=custom_id.capitalize(), value=(value or "No reason provided"), inline=False)

        await modal_inter.response.send_message(embed=embed, ephemeral=True)

    @disnake.ui.button(label="👞 Kick", style=disnake.ButtonStyle.primary)
    async def kick(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        ctx = self.ctx
        user = self.user

        await interaction.response.send_modal(modal=Reason("Kick Reason:"))

        try:
            modal_inter: disnake.ModalInteraction = await bot.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "reason_modal" and i.author.id == ctx.author.id,
                timeout=300,
            )
        except asyncio.TimeoutError:
            return

        embed = disnake.Embed(
            title="User Kicked",
            description=f"User {user.name}#{user.discriminator} has been kicked!\n\n",
            colour=disnake.Colour.red(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for custom_id, value in modal_inter.text_values.items():
            embed.add_field(name=custom_id.capitalize(), value=(value or "No reason provided"), inline=False)

        await modal_inter.response.send_message(embed=embed, ephemeral=True)

    @disnake.ui.button(label="🔨 Ban", style=disnake.ButtonStyle.primary)
    async def ban(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        ctx = self.ctx
        user = self.user

        await interaction.response.send_modal(modal=Reason("Ban Reason:"))

        try:
            modal_inter: disnake.ModalInteraction = await bot.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "reason_modal" and i.author.id == ctx.author.id,
                timeout=300,
            )
        except asyncio.TimeoutError:
            return

        embed = disnake.Embed(
            title="User Banned",
            description=f"User {user.name}#{user.discriminator} has been banned!\n\n",
            colour=disnake.Colour.dark_red(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for custom_id, value in modal_inter.text_values.items():
            embed.add_field(name=custom_id.capitalize(), value=(value or "No reason provided"), inline=False)

        await modal_inter.response.send_message(embed=embed, ephemeral=True)


@commands.slash_command(
    name="note",
    description="Add a note to a user",
)
async def note(
        ctx,
        user: disnake.User,
        text: str
):
    note_ = classes.Note(
        content=text,
        author=ctx.author.id,
        user=user.id
    )

    server = classes.server(ctx.guild.id)

    if server.get_user(user.id) is None:
        user_ = classes.User(id_=user.id)
        server.add_user(user_)

    server.get_user(user.id).add_note(note_)
    server.save()

    embed = disnake.Embed(
        title="Note Added",
        description=f"Note added to {user.name}#{user.discriminator}",
        colour=disnake.Colour.blurple(),
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Note", value=text, inline=False)

    await ctx.send(embed=embed, ephemeral=True)


@commands.user_command(name="Info")
async def info_context(
        ctx,
        user: disnake.User
):
    await info(ctx, user)


@commands.slash_command(
    name="info",
    description="Get simple user info",
)
async def info(
        ctx,
        user: disnake.User
):
    embed = disnake.Embed(
        title=f"**{user.name}#{user.discriminator}**",
        colour=user.accent_colour
    )
    embed.set_footer(text="Bought to you with hopes and dreams")
    embed.set_thumbnail(url=user.display_avatar.url)

    roles = []
    for role in user.roles:
        if role.name != "@everyone":
            roles.append(role.mention)

    roles.reverse()

    embed.add_field(name="User ID", value=user.id, inline=False)
    embed.add_field(name="Created At", value=user.created_at, inline=False)
    embed.add_field(name="Roles", value=' '.join(roles), inline=False)

    if ctx.author.guild_permissions.kick_members and ctx.author.guild_permissions.ban_members:
        view = Actions(ctx, user)
    else:
        view = disnake.ui.View(timeout=None)

    await ctx.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )

    await view.wait()


def setup(_bot):
    print('Loading Moderation Ext.')

    _bot.add_user_command(info_context)
    _bot.add_slash_command(info)

    _bot.add_slash_command(note)

    print('Moderation Ext. Loaded')
