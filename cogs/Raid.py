import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

DATA_FILE = "raid_data.json"
# حط رابط الصورة (البنر) هنا بين القوسين
BANNER_URL = "رابط_البنر_هنا"

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

def save_raid_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# نافذة بدء الرايد (Raid Start Modal)
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
        if BANNER_URL != "رابط_البنر_هنا":
            embed.set_image(url=BANNER_URL)
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)

        # 1. الإعلان بالشات العام مع @here
        await interaction.channel.send(content="@here 🔔 **تنبيه رايد جديد:**", embed=embed, view=view)

        # 2. التوجيه للخاص لكل عضو
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

# نافذة إنهاء الرايد (مرتبة بدون رسائل فرعية مزعجة وبها البنر وعدد المشاركين)
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
    participants_input = discord.ui.TextInput(
        label="آيديات المشاركين أو منشناتهم (انسخها هنا)",
        placeholder="ضع الآيديات أو المنشنات هنا مهما كان عددها...",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_raid_data()
        
        participants = []
        words = self.participants_input.value.split()
        for w in words:
            cleaned = w.replace("<@", "").replace(">", "").replace("!", "")
            if cleaned.isdigit():
                member = interaction.guild.get_member(int(cleaned))
                if member and member not in participants:
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

        # تقسيم اللستة إذا كانت طويلة جداً لتجنب خطأ ديسكورد
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
            description=f"`{self.win_reason.value}`",
            color=0x000000
        )
        embed.add_field(name="🏁 Result", value=f"`✅ {self.result_status.value}`", inline=False)
        embed.add_field(name="⏱️ Duration", value=f"`{self.duration.value}`", inline=False)
        embed.add_field(name="👥 Total Raiders", value=f"`{len(participants)}`", inline=False)
        
        for idx, chunk in enumerate(chunks):
            field_name = f"✅ Raider List ({idx+1})" if len(chunks) > 1 else "✅ Raider List"
            embed.add_field(name=field_name, value=chunk, inline=False)

        embed.add_field(name="🔥 Win Streak", value=f"`{current_streak} in a row`", inline=False)
        
        # وضع البنر بشكل تلقائي هنا
        if BANNER_URL != "رابط_البنر_هنا":
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        # إرسال النتيجة بـ Embed واحد مرتب وبدون رسائل فوضوية متفرقة
        await interaction.channel.send(content="🏁 **تقرير ونتايج الرايد النهائية:**", embed=embed)
        await interaction.followup.send("✅ | تم تسجيل النتائج ونشر التقرير بالبنر في الشات العام بنجاح!", ephemeral=True)

class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ خاص بالإدارة ] بدء رايد ونشره بـ here وتوجيهه للخاص")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="raid-end", description="[ خاص بالإدارة ] إنهاء الرايد وتسجيل النتائج بالبنر التلقائي")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndModal())

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
