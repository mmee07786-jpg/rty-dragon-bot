import discord
from discord.ext import commands
from discord import app_commands
import json
import os

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


class RaidEndInfoModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    raid_number = discord.ui.TextInput(label="RAID Number", placeholder="", style=discord.TextStyle.short, required=True)
    enemy = discord.ui.TextInput(label="ENEMY", placeholder="", style=discord.TextStyle.short, required=True)
    ally = discord.ui.TextInput(label="ALLY", placeholder="", style=discord.TextStyle.short, required=True)
    duration = discord.ui.TextInput(label="DURATION", placeholder="", style=discord.TextStyle.short, required=True)
    status_reason = discord.ui.TextInput(label="STATUS", placeholder="", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        view = RaidMembersSelectView(
            self.raid_number.value,
            self.enemy.value,
            self.ally.value,
            self.duration.value,
            self.status_reason.value,
            interaction.user
        )
        await interaction.response.send_message(
            "👇 **اضغط على الزر أدناه لكتابة وبحث وإضافة أسماء/منشنات المشاركين (بدون قيود):**",
            view=view,
            ephemeral=True
        )


class RaidMembersSelectView(discord.ui.View):
    def __init__(self, raid_number, enemy, ally, duration, status_reason, author):
        super().__init__(timeout=180)
        self.raid_number = raid_number
        self.enemy = enemy
        self.ally = ally
        self.duration = duration
        self.status_reason = status_reason
        self.author = author

    @discord.ui.button(label="⭐ بحث وإدخال المشاركين (MVPs)", style=discord.ButtonStyle.green, emoji="🔍")
    async def open_selector(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ | هذه القائمة ليست لك!", ephemeral=True)
            return

        # يفتح المودال بشكل فوري وسريع جداً بدون أي عمليات جلب ثقيلة
        await interaction.response.send_modal(
            RaidFinalMediaModal(
                self.raid_number,
                self.enemy,
                self.ally,
                self.duration,
                self.status_reason
            )
        )


class RaidFinalMediaModal(discord.ui.Modal, title="👥 | MVPs & Media Proofs"):
    mvps_input = discord.ui.TextInput(
        label="MVPs (ابحث واكتب أسماء أو منشنات الأعضاء هنا)",
        placeholder="مثال: @user1 @user2 أو اكتب أسمائهم...",
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
        await interaction.followup.send("✅ | تم نشر التقرير النهائي بنجاح!", ephemeral=True)


class RaidEndCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-end", description="[ Admin Only ] Conclude the raid and record results")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndInfoModal())

async def setup(bot):
    await bot.add_cog(RaidEndCog(bot))

