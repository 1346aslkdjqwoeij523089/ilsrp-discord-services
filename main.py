import os
import nextcord
from nextcord.ext import commands
from nextcord.utils import utcnow
import asyncio

# ------------------------------
# Intents
# ------------------------------
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

# ------------------------------
# Bot setup
# ------------------------------
bot = commands.Bot(command_prefix=";", intents=intents)

# ------------------------------
# Member join event
# ------------------------------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1471660664022896902)

    if channel:
        banner_embed = nextcord.Embed(color=0x4bbfff)
        banner_embed.set_image(
            url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png"
        )

        welcome_embed = nextcord.Embed(
            title="Welcome to the Server!",
            description=(
                f"Hey {member.mention} 👋\n\n"
                "We're glad to have you here.\n"
                "Make sure to read the rules and grab your roles!"
            ),
            color=0x4bbfff
        )

        welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        welcome_embed.set_footer(text=f"Member #{member.guild.member_count}")
        welcome_embed.timestamp = utcnow()

        await channel.send(
            content=f"Greetings {member.mention} 🎉",
            embeds=[banner_embed, welcome_embed]
        )

# ------------------------------
# SAY COMMAND (Prefix + Slash)
# ------------------------------
ALLOWED_ROLE_IDS = [1471642126663024640, 1471642360503992411]

@bot.hybrid_command(name="say", description="Repeat a message (Executive & Holding only)")
async def say(ctx, *, message: str):

    if any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):

        # Delete only if prefix command
        if ctx.interaction is None:
            try:
                await ctx.message.delete()
            except nextcord.Forbidden:
                pass

        await ctx.send(message)

    else:
        if ctx.interaction:
            await ctx.send(
                f"❌ {ctx.author.mention}, you don't have permission to use this command.",
                ephemeral=True
            )
        else:
            await ctx.send(f"❌ {ctx.author.mention}, you don't have permission to use this command.")

# ------------------------------
# REQUEST TRAINING (Prefix + Slash)
# ------------------------------
@bot.hybrid_command(
    name="requesttraining",
    description="Request a staff training session"
)
async def requesttraining(ctx):

    # Channel restriction
    if ctx.channel.id != 1473150653374271491:
        if ctx.interaction:
            await ctx.send(
                f"❌ {ctx.author.mention}, you can't use this command here.",
                ephemeral=True
            )
        else:
            await ctx.send(f"❌ {ctx.author.mention}, you can't use this command here.")
        return

    # Role restriction
    allowed_role_id = 1472037174630285538
    if allowed_role_id not in [role.id for role in ctx.author.roles]:
        if ctx.interaction:
            await ctx.send(
                f"❌ {ctx.author.mention}, you do not have permission to use this command.",
                ephemeral=True
            )
        else:
            await ctx.send(f"❌ {ctx.author.mention}, you do not have permission to use this command.")
        return

    target_channel = bot.get_channel(1473150653374271491)
    if not target_channel:
        await ctx.send("❌ Could not find the target channel.")
        return

    embed = nextcord.Embed(
        title="Greetings, Staff Trainers",
        description=(
            f"{ctx.author.mention} is requesting that a training session will be hosted at this time.\n\n"
            "You are requested to organize one and provide further instructions in <#1472056023358640282>."
        ),
        color=0x4bbfff
    )

    await target_channel.send(
        content="<@&1473151069264678932>",
        embed=embed
    )

    # Delete prefix command message
    if ctx.interaction is None:
        try:
            await ctx.message.delete()
        except nextcord.Forbidden:
            pass
        await ctx.send(
            f"✅ {ctx.author.mention}, your training request has been sent!",
            delete_after=5
        )
    else:
        await ctx.send(
            f"✅ {ctx.author.mention}, your training request has been sent!",
            ephemeral=True
        )

# ------------------------------
# Keep-alive task
# ------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

    # Sync slash commands
    try:
        await bot.sync_application_commands()
        print("Slash commands synced!")
    except Exception as e:
        print(f"Slash sync failed: {e}")

    keepalive_channel = bot.get_channel(1473152268411998410)

    async def keep_sending():
        await bot.wait_until_ready()
        while not bot.is_closed():
            if keepalive_channel:
                try:
                    await keepalive_channel.send("\u200b")
                except nextcord.Forbidden:
                    pass
            await asyncio.sleep(1800)  # 30 minutes

    bot.loop.create_task(keep_sending())

# ------------------------------
# Run bot
# ------------------------------
bot.run(os.getenv("TOKEN"))
