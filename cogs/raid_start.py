import discord
from discord.ext import commands
from discord import app_commands
import json
import os

BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&"
DATA_FILE = "raid_data.json"

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

# خيارات الألوان الجاهزة أو إدخال كود لون مخصص
class RaidStartModal(discord.ui.Modal, title="⚔️ | Raid Start & Announcement"):
    clan_name = discord.ui.TextInput(
        label="Clan Name (اتركه فارغاً لـ VLX تلقائياً)", 
        placeholder="مثال: RL أو VLX...", 
        style=discord.TextStyle.short, 
        required=False
    )
    color_input = discord.ui.TextInput(
        label="Color (كود HEX مثل #FF0000 أو اسم لون)", 
        placeholder="مثال: #8B0000 أو red, blue, green...", 
        style=discord.TextStyle.short, 
        required=False,
        default="8B0000"
    )
    server_link = discord.ui.TextInput(
        label="Server Link", 
        placeholder="رابط السيرفر...", 
        style=discord.TextStyle.short, 
        required=True
    )
    difficulty = discord.ui.TextInput(
        label="Difficulty", 
        placeholder="صعوبة الرايد...", 
        style=discord.TextStyle.short, 
        required=True
    )
    region = discord.ui.TextInput(
        label="Region", 
        placeholder="المنطقة...", 
        style=discord.TextStyle.short, 
        required=True, 
        default=""
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 | جاري إرسال إشعار الرايد...", ephemeral=True)

        # تحديد اسم الكلان (إذا ترك فارغاً يصير VLX)
        clan = self.clan_name.value.strip() if self.clan_name.value else "VLX"

        # معالجة اللون (تحويل كود الـ HEX أو الألوان الجاهزة إلى رقم صحيح لـ Discord Embed)
        color_val = self.color_input.value.strip()
        embed_color = 0x8B0000 # اللون الافتراضي (أحمر غامق)
        
        if color_val:
            if color_val.startswith("#"):
                color_val = color_val[1:]
            
            # محاولة تحويل كود الـ HEX
            try:
                embed_color = int(color_val, 16)
            except ValueError:
                # ألوان جاهزة سريعة
                preset_colors = {
                    "red": 0xFF0000,
                    "blue": 0x0000FF,
                    "green": 0x00FF00,
                    "gold": 0xFFD700,
                    "purple": 0x800080,
                    "black": 0x000000,
                    "white": 0xFFFFFF
                }
                embed_color = preset_colors.get(color_val.lower(), 0x8B0000)

        # بناء الإيمبد مع اسم الكلان واللون الجديد
        embed = discord.Embed(title=f"⚔️ **{clan} Clan Raid Notification** ⚔️", color=embed_color)
        embed.add_field(name="⚔️ Difficulty", value=f"`{self.difficulty.value}`", inline=False)
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

class RaidStartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ Admin Only ] Start a raid with custom clan name & color")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

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

            lb_embed = discord.Embed(title="🏆 | Clan Top Raiders (Leaderboard)", description=description, color=0x8B0000)
            lb_embed.set_footer(text="Clan Statistics")
            await interaction.response.send_message(embed=lb_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidStartCog(bot))
