import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "raid_data.json"

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

def save_raid_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 1. نافذة بدء الرايد (Raid Start Modal)
class RaidStartModal(discord.ui.Modal, title="⚔️ | إعداد ونشر إعلان الرايد"):
    server_link = discord.ui.TextInput(
        label="رابط سيرفر العدو (Invite Link)",
        placeholder="https://discord.gg/...",
        style=discord.TextStyle.short,
        required=True
    )
    difficulty = discord.ui.TextInput(
        label="مستوى الصعوبة (Difficulty)",
        placeholder="مثال: Hard / Extreme",
        style=discord.TextStyle.short,
        required=True
    )
    targets = discord.ui.TextInput(
        label="الأهداف / منو وياكم ومن عدوكم",
        placeholder="مثال: VLX vs ENEMY",
        style=discord.TextStyle.short,
        required=True
    )
    region = discord.ui.TextInput(
        label="السيرفر / الرجيون (Region)",
        placeholder="EU / ME",
        style=discord.TextStyle.short,
        required=True,
        default="EU"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 | جاري إرسال إعلانات الرايد...", ephemeral=True)

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)

        embed = discord.Embed(
            title="⚔️ **VLX Clan Raid Notification** ⚔️",
            color=0x000000 # أسود فخم
        )
        embed.add_field(name="⚔️ Difficulty", value=f"`{self.difficulty.value}`", inline=False)
        embed.add_field(name="🎯 Targets", value=f"`{self.targets.value}`", inline=False)
        embed.add_field(name="📡 Region", value=f"🌍 `{self.region.value}`", inline=False)
        
        instructions = (
            "→ Click **Join** below to enter the server\n"
            "→ Follow callouts from raid leadership\n"
            "→ Stay until the raid is concluded"
        )
        embed.add_field(name="📜 Instructions", value=instructions, inline=False)
        
        # وضع بنر VLX في البداية
        embed.set_image(url="رابط_صورة_البنر_هنا") # ارفع الصورة المرفقة وضع رابطها المباشر هنا
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        # إرسال للخاص وللقناة الحالية
        for member in interaction.guild.members:
            if not member.bot:
                try:
                    await member.send(embed=embed, view=view)
                except:
                    pass
        
        await interaction.channel.send(embed=embed, view=view)

# 2. نافذة إنهاء الرايد (Raid End Modal)
class RaidEndModal(discord.ui.Modal, title="🏁 | إنهاء الرايد وتسجيل النتائج"):
    duration = discord.ui.TextInput(
        label="مدة الرايد (Duration)",
        placeholder="مثال: 1:11:40",
        style=discord.TextStyle.short,
        required=True
    )
    result_status = discord.ui.TextInput(
        label="نتيجة الرايد (Result)",
        placeholder="VICTORY",
        style=discord.TextStyle.short,
        required=True,
        default="VICTORY"
    )
    win_reason = discord.ui.TextInput(
        label="سبب الفوز (Reason / Operation Status)",
        placeholder="مثال: Operation successful.",
        style=discord.TextStyle.short,
        required=True,
        default="Operation successful."
    )
    participants_ids = discord.ui.TextInput(
        label="منشن أو آيديات المشاركين (افصل بينهم بمسافة)",
        placeholder="@User1 @User2 أو اتركها فارغة إذا لم تحدد",
        style=discord.TextStyle.paragraph,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_raid_data()
        
        participants = []
        if self.participants_ids.value.strip():
            words = self.participants_ids.value.split()
            for w in words:
                cleaned = w.replace("<@", "").replace(">", "").replace("!", "")
                if cleaned.isdigit():
                    member = interaction.guild.get_member(int(cleaned))
                    if member:
                        participants.append(member)

        if not participants:
            await interaction.followup.send("❌ | لم تقم بتحديد أعضاء مشاركين صحيحيين!", ephemeral=True)
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

        embed = discord.Embed(
            title="〈★〉🏁 **RAID CONCLUDED**",
            description=f"`{self.win_reason.value}`",
            color=0x000000
        )
        embed.add_field(name="🏁 Result", value=f"`✅ {self.result_status.value}`", inline=False)
        embed.add_field(name="⏱️ Duration", value=f"`{self.duration.value}`", inline=False)
        embed.add_field(name="👥 Raiders", value=f"`{len(participants)}`", inline=False)
        embed.add_field(name="✅ Raider List", value=raider_list_text, inline=False)
        embed.add_field(name="🔥 Win Streak", value=f"`{current_streak} in a row`", inline=False)
        
        # وضع نفس بنر VLX في النهاية أيضاً
        embed.set_image(url="رابط_صورة_البنر_هنا") # ارفع الصورة المرفقة وضع رابطها المباشر هنا
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        mentions_str = " ".join([m.mention for m in participants])
        await interaction.channel.send(content=f"🔔 تجميعة المشاركين بالرايد: {mentions_str}", embed=embed)
        await interaction.followup.send("✅ | تم إنهاء الرايد بنجاح!", ephemeral=True)

class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ خاص بالإدارة ] بدء رايد جديد ونشره بالخاص والقناة")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="raid-end", description="[ خاص بالإدارة ] إنهاء الرايد وتسجيل النتائج ونشر النتيجة")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndModal())

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
