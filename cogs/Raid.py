import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

DATA_FILE = "raid_data.json"
# رابط البانر الخاص ببداية الرايد (تستطيع تغييره متى شئت)
BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&"
EMBED_COLOR = 0x8B0000

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

def save_raid_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class RaidStartModal(discord.ui.Modal, title="⚔️ | Raid Start & Announcement"):
    server_link = discord.ui.TextInput(
        label="Server Link",
        placeholder="رابط السيرفر",
        style=discord.TextStyle.short,
        required=True
    )
    difficulty = discord.ui.TextInput(
        label="Difficulty",
        placeholder="e.g., Hard / Extreme",
        style=discord.TextStyle.short,
        required=True
    )
    targets = discord.ui.TextInput(
        label="Targets / Matchup",
        placeholder="",
        style=discord.TextStyle.short,
        required=True,
        default=""
    )
    counts = discord.ui.TextInput(
        label="Our Count & Their Count",
        placeholder="e.g., 4 vs 11",
        style=discord.TextStyle.short,
        required=True,
        default="? vs ?"
    )
    region = discord.ui.TextInput(
        label="Region",
        placeholder="EU / ME",
        style=discord.TextStyle.short,
        required=True,
        default="EU"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 | جاري إرسال إشعار الرايد...", ephemeral=True)

        embed = discord.Embed(
            title="⚔️ **VLX Clan Raid Notification** ⚔️",
            color=EMBED_COLOR
        )
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
        
        # وضع الصورة حصراً في بداية الرايد (Start)
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)
        await interaction.channel.send(content="@here 11🔔 **New Raid Notification:**", embed=embed, view=view)


class RaidEndModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    raid_number = discord.ui.TextInput(
        label="RAID Number",
        placeholder="129",
        style=discord.TextStyle.short,
        required=True
    )
    enemy = discord.ui.TextInput(
        label="ENEMY",
        placeholder="IVRAID",
        style=discord.TextStyle.short,
        required=True
    )
    ally = discord.ui.TextInput(
        label="ALLY",
        placeholder="VALTRYX",
        style=discord.TextStyle.short,
        required=True
    )
    duration = discord.ui.TextInput(
        label="DURATION",
        placeholder="30m",
        style=discord.TextStyle.short,
        required=True
    )
    status_reason = discord.ui.TextInput(
        label="STATUS",
        placeholder="auto win",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        non_bots = [m for m in interaction.guild.members if not m.bot][:25]
        
        if not non_bots:
            await interaction.response.send_message("❌ | لا توجد أعضاء في السيرفر!", ephemeral=True)
            return

        view = RaidSelectView(
            self.raid_number.value,
            self.enemy.value,
            self.ally.value,
            self.duration.value,
            self.status_reason.value,
            non_bots,
            interaction.user
        )
        await interaction.response.send_message("👇 **اختر المشاركين (MVPs) من القائمة أدناه:**", view=view, ephemeral=True)


class RaidSelectView(discord.ui.View):
    def __init__(self, raid_number, enemy, ally, duration, status_reason, members, author):
        super().__init__(timeout=180)
        self.raid_number = raid_number
        self.enemy = enemy
        self.ally = ally
        self.duration = duration
        self.status_reason = status_reason
        self.author = author
        
        options = [
            discord.SelectOption(label=m.display_name[:50], value=str(m.id), description=f"User: {m.name}")
            for m in members
        ]
        
        self.select_menu = discord.ui.Select(
            placeholder="⭐ اختر المشاركين...",
            min_values=1,
            max_values=len(options),
            options=options
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ | هذه القائمة ليست لك!", ephemeral=True)
            return

        participants = []
        for uid_str in self.select_menu.values:
            member = interaction.guild.get_member(int(uid_str))
            if member and member not in participants:
                participants.append(member)

        if not participants:
            await interaction.response.send_message("❌ | لم تقم بتحديد أي مشارك!", ephemeral=True)
            return

        await interaction.response.send_modal(
            MediaUploadModal(
                self.raid_number,
                self.enemy,
                self.ally,
                self.duration,
                self.status_reason,
                participants
            )
        )


class MediaUploadModal(discord.ui.Modal, title="📁 | إرفاق الوسائط الاختيارية"):
    media_links = discord.ui.TextInput(
        label="روابط الصور / الفيديوهات (اختياري)",
        placeholder="ضع الروابط هنا (بدون حد أقصى)...",
        style=discord.TextStyle.paragraph,
        required=False
    )

    def __init__(self, raid_number, enemy, ally, duration, status_reason, participants):
        super().__init__()
        self.raid_number = raid_number
        self.enemy = enemy
        self.ally = ally
        self.duration = duration
        self.status_reason = status_reason
        self.participants = participants

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_raid_data()

        if "raider_stats" not in data:
            data["raider_stats"] = {}

        mvps_text = ""
        for member in self.participants:
            m_id = str(member.id)
            if m_id not in data["raider_stats"]:
                data["raider_stats"][m_id] = 0
            data["raider_stats"][m_id] += 1
            mvps_text += f"<@{m_id}> "

        data["win_streak"] = data.get("win_streak", 0) + 1
        current_streak = data["win_streak"]
        save_raid_data(data)

        # تنسيق تقرير نهاية الرايد بدون صورة وبنفس الشكل والإطارات والأسهم المطلوبة
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
            f"╰➤ {mvps_text}\n\n"
        )

        if self.media_links and self.media_links.value.strip():
            report_content += f"**𝐏𝐑𝐎𝐎𝐅𝐒 / 𝐌𝐄𝐃𝐈𝐀:**\n╰➤ {self.media_links.value}\n\n"

        report_content += (
            f"🔥 **Win Streak:** `{current_streak} in a row`\n\n"
            f"╰────────────────╯"
        )

        embed = discord.Embed(color=EMBED_COLOR, description=report_content)
        # ملاحظة: تم حذف الصورة من نهاية الرايد تماماً بناءً على طلبك
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="🏁 **Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("✅ | تم نشر التقرير النهائي بدون صورة بنجاح!", ephemeral=True)


class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ Admin Only ] Start a raid with announcement")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="raid-end", description="[ Admin Only ] Conclude the raid and record results")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndModal())

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
