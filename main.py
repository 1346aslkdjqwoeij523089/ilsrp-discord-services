import os
import nextcord
from nextcord.ext import commands
from nextcord.utils import utcnow
import asyncio
import chat_exporter

# ------------------------------
# Intents
# ------------------------------
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=";", intents=intents)

LOG_CHANNEL_ID = 1473167409505374220
BLUE = 0x4bbfff
MAX_TICKETS_PER_USER = 3

# ==============================
# TICKET CONFIG
# ==============================

CATEGORIES = {
    "general": 1471689868022120468,
    "appeal": 1471689978135183581,
    "report": 1473172223501144306,
    "management": 1471690051078455386
}

LOG_CHANNELS = {
    "general": 1471690459251478662,
    "appeal": 1471690532714450964,
    "report": 1471690532714450964,
    "management": 1471690561655279783
}

SUPPORT_ROLES = {
    "general": [1472072792081170682,1471641790112333867,1471641915215843559,1471642126663024640,1471642360503992411],
    "appeal": [1471641790112333867,1471641915215843559,1471642126663024640,1471642360503992411],
    "report": [1471641790112333867,1471641915215843559,1471642126663024640,1471642360503992411],
    "management": [1471641915215843559,1471642126663024640,1471642360503992411]
}

# ==============================
# UTILITIES
# ==============================

async def count_user_tickets(guild, user):
    count = 0
    for channel in guild.text_channels:
        if channel.topic and f"owner:{user.id}" in channel.topic:
            count += 1
    return count

def generate_ticket_name(user):
    return f"ticket-{user.name}".lower().replace(" ", "-")

# ==============================
# TICKET MODAL
# ==============================

class CloseReasonModal(nextcord.ui.Modal):
    def __init__(self, channel, ticket_type):
        super().__init__("Close Ticket With Reason")
        self.channel = channel
        self.ticket_type = ticket_type

        self.reason = nextcord.ui.TextInput(
            label="Reason for closing",
            style=nextcord.TextInputStyle.paragraph,
            required=True,
            max_length=500
        )
        self.add_item(self.reason)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()

        transcript = await chat_exporter.export(self.channel)
        if transcript:
            file = nextcord.File(
                fp=transcript.encode(),
                filename=f"{self.channel.name}.html"
            )
            log_channel = interaction.guild.get_channel(LOG_CHANNELS[self.ticket_type])
            await log_channel.send(
                content=f"🔒 Ticket closed with reason:\n{self.reason.value}",
                file=file
            )

        await self.channel.delete()

# ==============================
# TICKET BUTTON VIEW
# ==============================

class TicketView(nextcord.ui.View):
    def __init__(self, ticket_type):
        super().__init__(timeout=None)
        self.ticket_type = ticket_type

    @nextcord.ui.button(label="Claim", style=nextcord.ButtonStyle.primary)
    async def claim(self, button, interaction):
        await interaction.response.send_message(
            f"👤 {interaction.user.mention} has claimed this ticket.",
            allowed_mentions=nextcord.AllowedMentions.none()
        )

    @nextcord.ui.button(label="Transcript", style=nextcord.ButtonStyle.secondary)
    async def transcript(self, button, interaction):
        await interaction.response.defer(ephemeral=True)
        transcript = await chat_exporter.export(interaction.channel)
        if transcript:
            file = nextcord.File(
                fp=transcript.encode(),
                filename=f"{interaction.channel.name}.html"
            )
            await interaction.followup.send(file=file, ephemeral=True)

    @nextcord.ui.button(label="Close", style=nextcord.ButtonStyle.danger)
    async def close(self, button, interaction):
        await interaction.response.defer()

        transcript = await chat_exporter.export(interaction.channel)
        if transcript:
            file = nextcord.File(
                fp=transcript.encode(),
                filename=f"{interaction.channel.name}.html"
            )
            log_channel = interaction.guild.get_channel(LOG_CHANNELS[self.ticket_type])
            await log_channel.send(
                content="🔒 Ticket closed.",
                file=file
            )

        await interaction.channel.delete()

    @nextcord.ui.button(label="Close With Reason", style=nextcord.ButtonStyle.secondary)
    async def close_reason(self, button, interaction):
        await interaction.response.send_modal(
            CloseReasonModal(interaction.channel, self.ticket_type)
        )

# ==============================
# DROPDOWN
# ==============================

class TicketDropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(
                label="General Inquiry",
                value="general",
                emoji="<:GeneralInquiry:1471679744767426581>"
            ),
            nextcord.SelectOption(
                label="Appeal a Punishment",
                value="appeal",
                emoji="<:AppealandReports:1471679782818418852>"
            ),
            nextcord.SelectOption(
                label="Report a Member",
                value="report",
                emoji="<:AppealandReports:1471679782818418852>"
            ),
            nextcord.SelectOption(
                label="Management Request",
                value="management",
                emoji="<:ManagementRequests:1471679839667879956>"
            )
        ]

        super().__init__(
            placeholder="Select an Assistance Category",
            options=options,
            custom_id="persistent_ticket_dropdown"
        )

    async def callback(self, interaction: nextcord.Interaction):

        if await count_user_tickets(interaction.guild, interaction.user) >= MAX_TICKETS_PER_USER:
            await interaction.response.send_message(
                "❌ You already have 3 open tickets.",
                ephemeral=True
            )
            return

        ticket_type = self.values[0]
        category = interaction.guild.get_channel(CATEGORIES[ticket_type])

        overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            interaction.user: nextcord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for role_id in SUPPORT_ROLES[ticket_type]:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = nextcord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await interaction.guild.create_text_channel(
            name=generate_ticket_name(interaction.user),
            category=category,
            overwrites=overwrites,
            topic=f"owner:{interaction.user.id}"
        )

        embed = nextcord.Embed(
            title=f"You have created a {self.options[[o.value for o in self.options].index(ticket_type)].label}.",
            description="Please await staff assistance.\n\nRefrain from pinging staff members.",
            color=BLUE
        )

        await channel.send(
            content=interaction.user.mention,
            embed=embed,
            view=TicketView(ticket_type)
        )

        await interaction.response.send_message(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
        )

class TicketPanel(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ==============================
# MEMBER JOIN
# ==============================

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1471660664022896902)
    if channel:
        member_count = len([m for m in member.guild.members if not m.bot])

        def ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return str(n) + suffix

        welcome_message = (
            f"# <:ILSRP:1471990869166002291> Welcome to Illinois State Roleplay.\n\n"
            f"Hello, {member.mention}!\n\n"
            f"-# You are our {ordinal(member_count)} member."
        )

        await channel.send(welcome_message)

# ==============================
# LOGGING HELPER
# ==============================

async def log_command(user, command_name, ctx_type):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = nextcord.Embed(
            title="Command Executed",
            color=BLUE,
            timestamp=utcnow()
        )
        embed.set_author(name=f"{user}", icon_url=user.display_avatar.url)
        embed.add_field(name="Command", value=command_name)
        embed.add_field(name="Type", value=ctx_type)
        await log_channel.send(embed=embed)

# ==============================
# SAY COMMANDS
# ==============================

ALLOWED_ROLE_IDS = [1471642126663024640, 1471642360503992411]

@bot.command(name="say")
async def say_prefix(ctx, *, message: str):
    await log_command(ctx.author, "say", "Prefix")
    if any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        await ctx.message.delete()
        await ctx.send(message)
    else:
        await ctx.send("❌ No permission.")

@bot.slash_command(name="say", description="Repeat a message")
async def say_slash(interaction: nextcord.Interaction, *, message: str):
    await log_command(interaction.user, "say", "Slash")
    if any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message(message)
    else:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)

# ==============================
# READY EVENT
# ==============================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    bot.add_view(TicketPanel())

    await bot.sync_all_application_commands()

    keepalive_channel = bot.get_channel(1473152268411998410)

    async def keep_sending():
        await bot.wait_until_ready()
        while not bot.is_closed():
            if keepalive_channel:
                embed = nextcord.Embed(
                    title="__Activity Logistic__",
                    description=f"> Timestamp: <t:{int(utcnow().timestamp())}:F>",
                    color=BLUE
                )
                await keepalive_channel.send(embed=embed)
            await asyncio.sleep(60)

    bot.loop.create_task(keep_sending())

# ==============================
# RUN
# ==============================

bot.run(os.getenv("TOKEN"))
