import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(123456789012345678)  # Replace with your channel ID

    # ---- EMBED 1: Banner ----
    banner_embed = nextcord.Embed(color=0x4bbfff)
    banner_embed.set_image(
        url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png?ex=69951c16&is=6993ca96&hm=f387c3f9b12fcdeb0623cefbe2da3c6f9d536d36a8049fc4b0c1cd70b4ca391a&"  # Replace with your banner image
    )
    
    # ---- EMBED 2: Welcome Message ----
    welcome_embed = nextcord.Embed(
        title="Welcome to the Server!",
        description=(
            f"Hey {member.mention} 👋\n\n"
            "We're glad to have you here.\n"
            "Make sure to read the rules and grab your roles!"
        ),
        color=0x4bbfff
    )

    welcome_embed.set_thumbnail(url=member.avatar.url)
    welcome_embed.set_footer(text=f"Member #{member.guild.member_count}")

    # 👇 TEXT BEFORE EMBEDS
    await channel.send(
        content=f"Greetings {member.mention} 🎉",
        embeds=[banner_embed, welcome_embed]
    )

bot.run(BOT_TOKEN)
