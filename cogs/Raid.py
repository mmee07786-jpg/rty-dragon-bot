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
        # رد سريع للمشرف حتى لا تگول الكونسول إن التفاعل انتهى
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

        # 1. أولاً: إرسال الإعلان في الروم الحالية
        await interaction.channel.send(content="@here 🔔 **New Raid Notification:**", embed=embed, view=view)

        # 2. ثانياً: تصنيف الأعضاء (متصلين وغير متصلين) وتجنب البوتات
        online_members = []
        offline_members = []

        for member in interaction.guild.members:
            if member.bot:
                continue
            # فحص الحالة (متصل، مشهور كمتصل online/idle/dnd يعتبرون نشطين أو حسب الحالة المتاحة)
            if member.status != discord.Status.offline:
                online_members.append(member)
            else:
                offline_members.append(member)

        # دالة مساعدة لإرسال الرسائل بدفعات وبشكل آمن
        async def send_in_batches(member_list, batch_size, delay):
            for i in range(0, len(member_list), batch_size):
                batch = member_list[i:i + batch_size]
                tasks = []
                for member in batch:
                    async def send_dm(m):
                        try:
                            await m.send(content="📩 **Raid Notification Direct Message:**", embed=embed, view=view)
                        except Exception:
                            pass # في حال كان غالق الخاص
                    tasks.append(send_dm(member))
                
                # تنفيذ الدفعة الحالية بالتوازي
                await asyncio.gather(*tasks)
                # انتظار بسيط بين كل دفعة ودفعة لتجنب سبام ديسكورد
                await asyncio.sleep(delay)

        # تشغيل إرسال الدفعات في الخلفية حتى لا يعلق البوت
        asyncio.create_task(send_in_batches(online_members, batch_size=30, delay=1.5))
        asyncio.create_task(send_in_batches(offline_members, batch_size=20, delay=2.0))

class RaidEndModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    duration = discord.ui.TextInput(
        label="Raid Duration",
        placeholder="e.g., 1:11:40",
        style=discord.TextStyle.short,
        required=True
    )
    result_status = discord.ui.TextInput(
        label="Raid Result",
        placeholder="VICTORY",
        style=discord.TextStyle.short,
        required=True,
        default="VICTORY"
    )
    win_reason = discord.ui.TextInput(
        label="Reason / Operation Status",
        placeholder="e.g., Operation successful.",
        style=discord.TextStyle.short,
        required=True,
        default="Operation successful."
    )

    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        non_bots = [m for m in interaction.guild.members if not m.bot][:25]
        
        if not non_bots:
            await interaction.response.send_message("❌ | No members found in server!", ephemeral=True)
            return

        view = RaidSelectView(self.duration.value, self.result_status.value, self.win_reason.value, non_bots, interaction.user)
        await interaction.response.send_message("👇 **اختر المشاركين في الريد من القائمة أدناه:**", view=view, ephemeral=True)

class RaidSelectView(discord.ui.View):
    def __init__(self, duration, result_status, win_reason, members, author):
        super().__init__(timeout=180)
        self.duration = duration
        self.result_status = result_status
        self.win_reason = win_reason
        self.author = author
        
        options = [
            discord.SelectOption(label=m.display_name[:50], value=str(m.id), description=f"User: {m.name}")
            for m in members
        ]
        
        self.select_menu = discord.ui.Select(
            placeholder="⭐ اختر المشاركين من القائمة...",
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

        await interaction.response.defer(ephemeral=True)
        data = load_raid_data()
        
        participants = []
        for uid_str in self.select_menu.values:
            member = interaction.guild.get_member(int(uid_str))
            if member and member not in participants:
                participants.append(member)

        if not participants:
            await interaction.followup.send("❌ | لم تقم بتحديد أي مشارك!", ephemeral=True)
            return

        if "raider_stats" not in data:
            data["raider_stats"] = {}

        raider_list_text = ""
        for member in participants:
            m_id = str(member.id)
            if m_id not in data["raider_stats"]:
                data["raider_stats"][m_id] = 0
            data["raider_stats"][m_id] += 1
            total_rp = data["raider_stats"][m_id]
            raider_list_text += f"★ <@{m_id}> — {total_rp} RP\n"

        data["win_streak"] = data.get("win_streak", 0) + 1
        current_streak = data["win_streak"]
        save_raid_data(data)

        chunks = []
        current_chunk = ""
        for line in raider_list_text.split("\n"):
            if len(current_chunk) + len(line) + 1 > 1024:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        embed = discord.Embed(
            title="〈★〉🏁 **RAID CONCLUDED**",
            description=f"`{self.win_reason}`",
            color=EMBED_COLOR
        )
        embed.add_field(name="🏁 Result", value=f"`✅ {self.result_status}`", inline=False)
        embed.add_field(name="⏱️ Duration", value=f"`{self.duration}`", inline=False)
        embed.add_field(name="👥 Total Raiders", value=f"`{len(participants)}`", inline=False)
        
        for idx, chunk in enumerate(chunks):
            field_name = f"✅ Raider List ({idx+1})" if len(chunks) > 1 else "✅ Raider List"
            embed.add_field(name=field_name, value=chunk, inline=False)

        embed.add_field(name="🔥 Win Streak", value=f"`{current_streak} in a row`", inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="🏁 **Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("✅ | Results recorded and report published successfully!", ephemeral=True)

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
        await interaction.response.send_modal(RaidEndModal(interaction.channel))

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
