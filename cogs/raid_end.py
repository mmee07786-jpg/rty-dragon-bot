import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

DATA_FILE = "raid_data.json"
EMBED_COLOR = 0x8B0000

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

def save_raid_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# مودال معلومات الرايد الأساسية
class RaidEndInfoModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    raid_number = discord.ui.TextInput(label="RAID Number", placeholder="", style=discord.TextStyle.short, required=True)
    enemy = discord.ui.TextInput(label="ENEMY", placeholder="", style=discord.TextStyle.short, required=True)
    ally = discord.ui.TextInput(label="ALLY", placeholder="", style=discord.TextStyle.short, required=True)
    duration = discord.ui.TextInput(label="DURATION", placeholder="", style=discord.TextStyle.short, required=True)
    status_reason = discord.ui.TextInput(label="STATUS", placeholder="", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        view = RaidFinalMediaView(
            self.raid_number.value,
            self.enemy.value,
            self.ally.value,
            self.duration.value,
            self.status_reason.value,
            interaction.user
        )
        await interaction.response.send_message(
            "👇 **اضغط على الزر أدناه لإدخال الـ MVPs والروابط ونشر التقرير:**",
            view=view,
            ephemeral=True
        )


class RaidFinalMediaView(discord.ui.View):
    def __init__(self, raid_number, enemy, ally, duration, status_reason, author):
        super().__init__(timeout=180)
        self.raid_number = raid_number
        self.enemy = enemy
        self.ally = ally
        self.duration = duration
        self.status_reason = status_reason
        self.author = author

    @discord.ui.button(label="📝 إدخال المشاركين والروابط", style=discord.ButtonStyle.green, emoji="⭐")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ | هذه القائمة ليست لك!", ephemeral=True)
            return
        await interaction.response.send_modal(
            RaidSubmitModal(self.raid_number, self.enemy, self.ally, self.duration, self.status_reason)
        )


class RaidSubmitModal(discord.ui.Modal, title="👥 | MVPs & Media Proofs"):
    mvps_input = discord.ui.TextInput(
        label="MVPs (قم بلصق المنشنات هنا)",
        placeholder="الصق المنشنات أو الأسماء هنا...",
        style=discord.TextStyle.paragraph,
        required=True
    )

    media_links = discord.ui.TextInput(
        label="Do you want to upload a video or photo?",
        placeholder="ضع أكثر من رابط (كل رابط بسطر) أو اكتب 'skip' للتخطي...",
        style=discord.TextStyle.paragraph,
        required=False
    )

    def __init__(self, raid_number, enemy, ally, duration, status_reason):
        super().__init__()
        self.raid_number = raid_number
        self.enemy = enemy
        self.ally = ally
        self.duration = duration
        self.status_reason = status_reason

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_raid_data()

        if "raider_stats" not in data:
            data["raider_stats"] = {}

        data["win_streak"] = data.get("win_streak", 0) + 1
        current_streak = data["win_streak"]

        user_ids = re.findall(r'<@!?(\d+)>', self.mvps_input.value)
        for uid in user_ids:
            if uid not in data["raider_stats"]:
                data["raider_stats"][uid] = 0
            data["raider_stats"][uid] += 1

        save_raid_data(data)

        report_content = (
            f"╭─〔 𝐒𝐂𝐎𝐑𝐄 〕─╮\n\n"
            f"**𝐑𝐀𝐈𝐃:**\n"
            f"╰➤{self.raid_number}\n\n"
            f"**𝐄𝐍𝐄𝐌𝐘:**\n"
            f"╰➤{self.enemy}\n\n"
            f"**𝐀𝐋𝐋𝐘:**\n"
            f"╰➤{self.ally}\n\n"
            f"**𝐃𝐔𝐑𝐀𝐓𝐈𝐎𝐍:**\n"
            f"╰➤{self.duration}\n\n"
            f"**𝐒𝐓𝐀𝐓𝐔𝐒:**\n"
            f"╰➤{self.status_reason}\n\n"
            f"**𝐌𝐕𝐏𝐒:**\n"
            f"╰➤ {self.mvps_input.value}\n\n"
        )

        media_val = self.media_links.value.strip() if self.media_links.value else ""
        if media_val and media_val.lower() != "skip":
            report_content += f"**𝐏𝐑𝐎𝐎𝐅𝐒 / 𝐌𝐄𝐃𝐈𝐀:**\n╰➤ {media_val}\n\n"

        report_content += (
            f"🔥 **Win Streak:** `{current_streak} in a row`\n\n"
            f"╰────────────────╯"
        )

        embed = discord.Embed(color=EMBED_COLOR, description=report_content)
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="🏁 **Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("✅ | تم نشر التقرير وتحديث إحصائيات المشاركين بنجاح!", ephemeral=True)


class RaidSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="end-raid", description="[ Admin Only ] Conclude the raid and record results")
    @app_commands.checks.has_permissions(administrator=True)
    async def end_raid(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndInfoModal())

    @app_commands.command(name="raid-list", description="Auto-generate and send the top 30 raiders list in English")
    async def raid_list(self, interaction: discord.Interaction):
        data = load_raid_data()
        stats = data.get("raider_stats", {})

        if not stats:
            await interaction.response.send_message("❌ | No raid statistics recorded yet!", ephemeral=True)
            return

        sorted_raiders = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:30]

        description = ""
        for index, (uid, count) in enumerate(sorted_raiders, start=1):
            user = interaction.guild.get_member(int(uid))
            name = user.mention if user else f"User ID: {uid}"
            medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
            description += f"{medal} {name} ──> **{count}** Raids Won\n"

        if not description:
            description = "No participants found."

        embed = discord.Embed(
            title="📋 | VLX Clan Active Raiders List (Top 30)",
            description=description,
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Requested by {interaction.user.name} | VLX Clan System")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-mentions", description="نشر منشنات المشاركين (يتحمل أكثر من 200 عضو دفعة وحدة)")
    @app_commands.describe(mentions_content="الصق منشنات الأعضاء هنا (تدعم أعداد ضخمة فوق الـ 200 عضو)")
    async def raid_mentions(self, interaction: discord.Interaction, mentions_content: str):
        embed = discord.Embed(title="👥 | Raid Members Mentions (200+ Supported)", description=mentions_content, color=EMBED_COLOR)
        embed.set_footer(text=f"Mentions by {interaction.user.name} | VLX Clan")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-rank", description="معرفة عدد الرايدات التي شارك بها العضو")
    @app_commands.describe(member="اختر العضو (اختياري)")
    async def raid_rank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        data = load_raid_data()
        stats = data.get("raider_stats", {})
        
        count = stats.get(str(target.id), 0)
        
        embed = discord.Embed(title="📊 | Raider Rank Statistics", color=EMBED_COLOR)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="User", value=target.mention, inline=False)
        embed.add_field(name="Total Raids Participated", value=f"🛡️ `{count} Raids`", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-top", description="عرض قائمة أكثر الأشخاص مشاركة في الرايدات (Leaderboard)")
    async def raid_top(self, interaction: discord.Interaction):
        data = load_raid_data()
        stats = data.get("raider_stats", {})
        
        if not stats:
            await interaction.response.send_message("❌ | لا توجد أي إحصائيات مسجلة لرايدات حتى الآن!")
            return

        sorted_raiders = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        description = ""
        for index, (uid, count) in enumerate(sorted_raiders, start=1):
            user = interaction.guild.get_member(int(uid))
            name = user.mention if user else f"User ID: {uid}"
            medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
            description += f"{medal} {name} ──> **{count}** Raids\n"

        embed = discord.Embed(title="🏆 | VLX Clan Raid Leaderboard (Top 10)", description=description, color=EMBED_COLOR)
        embed.set_footer(text="VLX Clan Statistics")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RaidSystemCog(bot))
