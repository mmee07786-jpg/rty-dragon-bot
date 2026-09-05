import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

DATA_FILE = "raid_data.json"

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

def save_raid_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# نافذة بدء الرايد (تبقى Modal لأنها عبارة عن نصوص عادية)
class RaidStartModal(discord.ui.Modal, title="⚔️ | بدء الرايد ونشر الإعلان مع @here والخاص"):
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
    counts = discord.ui.TextInput(
        label="كم عددهم و عددكم؟",
        placeholder="مثال: 5 V 8",
        style=discord.TextStyle.short,
        required=True,
        default="? V ?"
    )
    region = discord.ui.TextInput(
        label="السيرفر / الرجيون (Region)",
        placeholder="EU / ME",
        style=discord.TextStyle.short,
        required=True,
        default="EU"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 | جاري نشر الإعلان العام بـ @here وتوجيهه للخاص للأعضاء...", ephemeral=True)

        embed = discord.Embed(
            title="⚔️ **VLX Clan Raid Notification** ⚔️",
            color=0x000000
        )
        embed.add_field(name="⚔️ Difficulty", value=f"`{self.difficulty.value}`", inline=False)
        embed.add_field(name="🎯 Targets", value=f"`{self.targets.value}`", inline=False)
        embed.add_field(name="🔢 Counts (عددهم وعددكم)", value=f"`{self.counts.value}`", inline=False)
        embed.add_field(name="📡 Region", value=f"🌍 `{self.region.value}`", inline=False)
        
        instructions = (
            "→ Click **Join** below to enter the server\n"
            "→ Follow callouts from raid leadership\n"
            "→ Stay until the raid is concluded"
        )
        embed.add_field(name="📜 Instructions", value=instructions, inline=False)
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)

        # إرسال الإعلان بالشات العام مع @here
        await interaction.channel.send(content="@here 🔔 **تنبيه رايد جديد:**", embed=embed, view=view)

        # توجيه للخاص لكل عضو
        try:
            members = [m for m in interaction.guild.members if not m.bot]
            for member in members:
                try:
                    await member.send(content="📩 **توجيه إعلان رايد جديد من سيرفرنا:**", embed=embed, view=view)
                    await asyncio.sleep(0.8)
                except Exception:
                    continue
        except Exception as e:
            print(f"خطأ في إرسال الرسائل الخاصة: {e}")

class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ خاص بالإدارة ] بدء رايد ونشره بـ here وتوجيهه للخاص")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="raid-end", description="[ خاص بالإدارة ] إنهاء الرايد وتسجيل النتائج بطريقة سهلة للموبايل")
    @app_commands.describe(
        duration="مدة الرايد (مثال: 1:11:40)",
        result_status="نتيجة الرايد (مثال: VICTORY)",
        win_reason="سبب الفوز أو حالة العملية",
        member1="المشارك الأول (اختر من القائمة التلقائية)",
        member2="المشارك الثاني (اختياري)",
        member3="المشارك الثالث (اختياري)",
        member4="المشارك الرابع (اختياري)",
        member5="المشارك الخامس (اختياري)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(
        self, 
        interaction: discord.Interaction, 
        duration: str, 
        result_status: str = "VICTORY", 
        win_reason: str = "Operation successful.",
        member1: discord.Member = None,
        member2: discord.Member = None,
        member3: discord.Member = None,
        member4: discord.Member = None,
        member5: discord.Member = None
    ):
        await interaction.response.defer(ephemeral=True)
        
        # جمع الأعضاء الذين تم اختيارهم من القوائم
        participants = [m for m in [member1, member2, member3, member4, member5] if m is not None]

        if not participants:
            await interaction.followup.send("❌ | يجب عليك اختيار مشارك واحد على الأقل!", ephemeral=True)
            return

        data = load_raid_data()
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
            description=f"`{win_reason}`",
            color=0x000000
        )
        embed.add_field(name="🏁 Result", value=f"`✅ {result_status}`", inline=False)
        embed.add_field(name="⏱️ Duration", value=f"`{duration}`", inline=False)
        embed.add_field(name="👥 Raiders", value=f"`{len(participants)}`", inline=False)
        embed.add_field(name="✅ Raider List", value=raider_list_text, inline=False)
        embed.add_field(name="🔥 Win Streak", value=f"`{current_streak} in a row`", inline=False)
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        mentions_str = " ".join([m.mention for m in participants])
        await interaction.channel.send(content=f"🔔 تجميعة المشاركين بالرايد: {mentions_str}", embed=embed)
        await interaction.followup.send("✅ | تم نشر نتائج الرايد في الشات العام بنجاح!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
