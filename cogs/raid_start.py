import discord
from discord.ext import commands
from discord import app_commands

BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&"
EMBED_COLOR = 0x8B0000

class RaidStartModal(discord.ui.Modal, title="⚔️ | Raid Start & Announcement"):
    server_link = discord.ui.TextInput(label="Server Link", placeholder="", style=discord.TextStyle.short, required=True)
    difficulty = discord.ui.TextInput(label="Difficulty", placeholder="", style=discord.TextStyle.short, required=True)
    targets = discord.ui.TextInput(label="Targets / Matchup", placeholder="", style=discord.TextStyle.short, required=True, default="")
    counts = discord.ui.TextInput(label="Our Count & Their Count", placeholder="", style=discord.TextStyle.short, required=True, default="")
    region = discord.ui.TextInput(label="Region", placeholder="", style=discord.TextStyle.short, required=True, default="")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 | جاري إرسال إشعار الرايد...", ephemeral=True)

        embed = discord.Embed(title="⚔️ **VLX Clan Raid Notification** ⚔️", color=EMBED_COLOR)
        embed.add_field(name="⚔️ Difficulty", value=f"`{self.difficulty.value}`", inline=False)
        embed.add_field(name="🎯 Targets", value=f"`{self.targets.value}`", inline=False)
        embed.add_field(name="🔢 Our Count & Their Count", value=f"`{self.counts.value}`", inline=False)
        embed.add_field(name="📡 Region", value=f"🌍 `{self.region.value}`", inline=False)
        
        instructions = (
            "→ Click **Join** below to enter the server\n"
            "→ Follow callouts from raid leadership\n"
            "→ Stay until the raid is concluded"
        )
        embed.add_field(name="📜 Instructions", value=instructions, inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)
        await interaction.channel.send(content="@here 🔔 **New Raid Notification:**", embed=embed, view=view)

class RaidStartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ Admin Only ] Start a raid with announcement")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

async def setup(bot):
    await bot.add_cog(RaidStartCog(bot))

