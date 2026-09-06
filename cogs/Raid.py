import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

DATA_FILE = "raid_data.json"

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
        placeholder="",
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
        await interaction.response.send_message("🚀 | جاري إرسال الريد بالخاص للأعضاء على شكل دفعات...", ephemeral=True)

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
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)

        await interaction.channel.send(content="@here 🔔 **New Raid Notification:**", embed=embed, view=view)

        online_members = []
        offline_members = []

        for member in interaction.guild.members:
            if member.bot:
                continue
            if member.status != discord.Status.offline:
                online_members.append(member)
            else:
                offline_members.append(member)

        async def send_in_batches(member_list, batch_size, delay):
            for i in range(0, len(member_list), batch_size):
                batch = member_list[i:i + batch_size]
                tasks = []
                for member in batch:
                    async def send_dm(m):
                        try:
                            await m.send(content="📩 **Raid Notification Direct Message:**", embed=embed, view=view)
                        except Exception:
                            pass
                    tasks.append(send_dm(member))
                
                await asyncio.gather(*tasks)
                await asyncio.sleep(delay)

        asyncio.create_task(send_in_batches(online_members, batch_size=30, delay=1.5))
        asyncio.create_task(send_in_batches(offline_members, batch_size=20, delay=2.0))


class RaidEndModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    raid_number = discord.ui.TextInput(
        label="RAID Number",
        placeholder="",
        style=discord.TextStyle.short,
        required=True
    )
    enemy = discord.ui.TextInput(
        label="ENEMY",
        placeholder="",
        style=discord.TextStyle.short,
        required=True
    )
    ally = discord.ui.TextInput(
        label="ALLY",
        placeholder="",
        style=discord.TextStyle.short,
        required=True
    )
    duration = discord.ui.TextInput(
        label="DURATION",
        placeholder="",
        style=discord.TextStyle.short,
        required=True
    )
    status_reason = discord.ui.TextInput(
        label="STATUS",
        placeholder="",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        view = ParticipantsInputView(
            self.raid_number.value,
            self.enemy.value,
            self.ally.value,
            self.duration.value,
            self.status_reason.value,
            interaction.user
        )
        await interaction.response.send_message(
            "👇 **اضغط على الزر أدناه لإدخال أسماء/منشنات المشاركين:**",
            view=view,
            ephemeral=True
        )


class FinalReportModal(discord.ui.Modal, title="👥 | Enter MVPs / Participants"):
    participants_text = discord.ui.TextInput(
        label="MVPs (اكتب الأسماء أو المنشنات هنا)",
        placeholder="اكتب أسماء الـ 56 مشارك أو أكثر هنا...",
        style=discord.TextStyle.paragraph,
        required=True
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

        data["win_streak"] = data.get("win_streak", 0) + 1
        current_streak = data["win_streak"]
        save_raid_data(data)

        # التنسيق المطلوب تماماً بدون أمثلة وبنفس الشكل المطابق للصورة
        report_description = (
            f"**𝐑𝐀𝐈𝐃:** {self.raid_number}\n"
            f"╰➤\n\n"
            f"**𝐄𝐍𝐄𝐌𝐘:** {self.enemy}\n"
            f"╰➤\n\n"
            f"**𝐀𝐋𝐋𝐘:** {self.ally}\n"
            f"╰➤\n\n"
            f"**𝐃𝐔𝐑𝐀𝐓𝐈𝐎𝐍:** {self.duration}\n"
            f"╰➤\n\n"
            f"**𝐒𝐓𝐀𝐓𝐔𝐒:** {self.status_reason}\n"
            f"╰➤\n\n"
            f"**𝐌𝐕𝐏𝐒:** {self.participants_text}\n"
            f"╰➤\n\n"
            f"🔥 **Win Streak:** `{current_streak} in a row`"
        )

        embed = discord.Embed(
            title=f"〈★〉🏁 **RAID CONCLUDED**",
            description=report_description,
            color=EMBED_COLOR
        )

        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="🏁 **Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("✅ | تم نشر التقرير النهائي بنجاح للكلان!", ephemeral=True)


class ParticipantsInputView(discord.ui.View):
    def __init__(self, raid_number, enemy, ally, duration, status_reason, author):
        super().__init__(timeout=300)
        self.raid_number = raid_number
        self.enemy = enemy
        self.ally = ally
        self.duration = duration
        self.status_reason = status_reason
        self.author = author

    @discord.ui.button(label="✍️ أدخل أسماء المشاركين (MVPs)", style=discord.ButtonStyle.green)
    async def open_modal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ | هذه القائمة ليست لك!", ephemeral=True)
            return
        
        await interaction.response.send_modal(
            FinalReportModal(
                self.raid_number,
                self.enemy,
                self.ally,
                self.duration,
                self.status_reason
            )
        )


class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ Admin Only ] Start a raid with announcement and banner")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="raid-end", description="[ Admin Only ] Conclude the raid and record results")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndModal())

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
