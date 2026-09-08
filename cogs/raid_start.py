import discord
from discord.ext import commands
from discord import app_commands
import json
import os

BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&"
CONFIG_FILE = "clan_config.json"
DATA_FILE = "raid_data.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"clan_name": "VLX", "embed_color": 0x8B0000}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

class RaidStartModal(discord.ui.Modal, title="⚔️ | Raid Start & Announcement"):
    server_link = discord.ui.TextInput(label="Server Link", placeholder="", style=discord.TextStyle.short, required=True)
    difficulty = discord.ui.TextInput(label="Difficulty", placeholder="", style=discord.TextStyle.short, required=True)
    targets = discord.ui.TextInput(label="Targets / Matchup", placeholder="", style=discord.TextStyle.short, required=True, default="")
    counts = discord.ui.TextInput(label="Our Count & Their Count", placeholder="", style=discord.TextStyle.short, required=True, default="")
    region = discord.ui.TextInput(label="Region", placeholder="", style=discord.TextStyle.short, required=True, default="")

    async def on_submit(self, interaction: discord.Interaction):
        # الرد على المودال مباشرة لإرسال إعلان الرايد بالشات العامة بدون رسائل خاصة
        await interaction.response.defer(ephemeral=True)

        config = load_config()
        clan = config.get("clan_name", "VLX")
        embed_color = config.get("embed_color", 0x8B0000)

        embed = discord.Embed(title=f"⚔️ **{clan} Clan Raid Notification** ⚔️", color=embed_color)
        embed.add_field(name="⚔️ Difficulty", value=f"`{self.difficulty.value}`", inline=False)
        embed.add_field(name="🎯 Targets", value=f"`{self.targets.value}`", inline=False)
        embed.add_field(name="🔢 Our Count & Their Count", value=f"`{self.counts.value}`", inline=False)
        embed.add_field(name="📡 Region", value=f"🌍 `{self.region.value}`", inline=False)
        
        instructions = (
            "→ Click **Join** below to enter the server\n"
            "→ Click **Leaderboard** to check top active raiders\n"
            "→ Follow callouts from raid leadership\n"
            "→ Stay until the raid is concluded"
        )
        embed.add_field(name="📜 Instructions", value=instructions, inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | {clan} Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))
                self.add_item(discord.ui.Button(label="Leaderboard", style=discord.ButtonStyle.secondary, custom_id="show_leaderboard", emoji="🏆"))

        view = RaidView(self.server_link.value)
        await interaction.channel.send(content="@here 🔔 **New Raid Notification:**", embed=embed, view=view)
        await interaction.delete_original_response()

class RaidStartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ Admin Only ] Start a raid with announcement")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="name_clan", description="[ Admin Only ] تعيين اسم الكلان الظهور بإعلانات الرايد")
    @app_commands.describe(name="اكتب اسم الكلان الجديد (اتركه فارغاً ليعود VLX)")
    @app_commands.checks.has_permissions(administrator=True)
    async def name_clan(self, interaction: discord.Interaction, name: str = "VLX"):
        config = load_config()
        config["clan_name"] = name
        save_config(config)
        await interaction.response.send_message(f"✅ | تم تحديث اسم الكلان بنجاح إلى: **{name}**", ephemeral=True)

    @app_commands.command(name="color_emed", description="[ Admin Only ] تغيير لون شريط إعلان الرايد")
    @app_commands.describe(hex_code="اكتب كود اللون (مثل #FF0000 أو 8B0000)")
    @app_commands.checks.has_permissions(administrator=True)
    async def color_emed(self, interaction: discord.Interaction, hex_code: str):
        cleaned_code = hex_code.strip()
        if cleaned_code.startswith("#"):
            cleaned_code = cleaned_code[1:]
        
        try:
            color_int = int(cleaned_code, 16)
        except ValueError:
            await interaction.response.send_message("❌ | كود اللون غير صحيح! استخدم صيغة صحيحة مثل `#FF0000`.", ephemeral=True)
            return

        config = load_config()
        config["embed_color"] = color_int
        save_config(config)
        await interaction.response.send_message(f"✅ | تم تحديث لون إعلان الرايد بنجاح إلى `#{cleaned_code}`", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component and interaction.data.get("custom_id") == "show_leaderboard":
            data = load_raid_data()
            stats = data.get("raider_stats", {})
            
            if not stats:
                await interaction.response.send_message("❌ | No raid statistics recorded yet!", ephemeral=True)
                return

            sorted_raiders = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
            
            description = ""
            for index, (uid, count) in enumerate(sorted_raiders, start=1):
                user = interaction.guild.get_member(int(uid))
                name = user.mention if user else f"User ID: {uid}"
                medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
                description += f"{medal} {name} ──> **{count}** Raids\n"

            config = load_config()
            lb_embed = discord.Embed(title="🏆 | Clan Top Raiders (Leaderboard)", description=description, color=config.get("embed_color", 0x8B0000))
            lb_embed.set_footer(text="Clan Statistics")
            await interaction.response.send_message(embed=lb_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidStartCog(bot))
