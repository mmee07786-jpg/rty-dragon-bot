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

# دالة إرسال الإعلانات عبر الويب هوكس المرقمة (للـ raid-start فقط)
async def send_via_webhooks(interaction, embed, view, server_link):
    channel = interaction.channel
    webhooks = []
    try:
        existing_hooks = await channel.webhooks()
        for h in existing_hooks:
            if h.name.startswith("VLX_Raid_"):
                webhooks.append(h)
        
        while len(webhooks) < 3:
            hook = await channel.create_webhook(name=f"VLX_Raid_{len(webhooks)+1}")
            webhooks.append(hook)
    except Exception as e:
        await channel.send(f"⚠️ تنبيه: البوت يحتاج صلاحية Manage Webhooks بالروم. الخطأ: {e}")
        return

    try:
        members = [m async for m in interaction.guild.fetch_members(limit=None)]
    except:
        members = interaction.guild.members

    online_members = [m for m in members if not m.bot and hasattr(m, "status") and m.status != discord.Status.offline]
    offline_members = [m for m in members if not m.bot and (not hasattr(m, "status") or m.status == discord.Status.offline)]
    
    all_sorted = online_members + offline_members
    batch_size = 10
    total_members = len(all_sorted)
    
    for idx, i in enumerate(range(0, total_members, batch_size)):
        batch = all_sorted[i:i + batch_size]
        hook_index = (idx % len(webhooks)) + 1
        active_webhook = webhooks[idx % len(webhooks)]
        
        mentions_text = " ".join([m.mention for m in batch])
        content_msg = f"📌 **Webhook {hook_index}** | الدفعة ({i+1} إلى {min(i+batch_size, total_members)})\n{mentions_text}"
        
        try:
            await active_webhook.send(
                content=content_msg,
                embed=embed,
                username=f"VLX Raid Bot #{hook_index}",
                avatar_url=interaction.client.user.display_avatar.url
            )
            await asyncio.sleep(2)
        except Exception as e:
            print(f"خطأ في إرسال الويب هوك: {e}")

# 1. نافذة بدء الرايد (Raid Start Modal)
class RaidStartModal(discord.ui.Modal, title="⚔️ | إعداد ونشر إعلان الرايد بالويب هوكس"):
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
        await interaction.response.send_message("🚀 | جاري إنشاء وبث الويب هوكس المرقمة للأعضاء...", ephemeral=True)

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)

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
        embed.set_image(url="رابط_صورة_البنر_هنا")
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        asyncio.create_task(send_via_webhooks(interaction, embed, view, self.server_link.value))

# 2. نافذة إنهاء الرايد (Raid End Modal) - تنشر بالشات العام فقط بدون أي رسائل خاص للأعضاء
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
        label="آيديات المشاركين أو منشناتهم (افصل بينهم بمسافة)",
        placeholder="اكتب الآيديات أو المنشنات هنا...",
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
                if member:
                    participants.append(member)

        if not participants:
            await interaction.followup.send("❌ | لم تقم بتحديد أعضاء مشاركين صحيحيين أو أن الآيديات غير صحيحة!", ephemeral=True)
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
        
        embed.set_image(url="رابط_صورة_البنر_هنا")
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        mentions_str = " ".join([m.mention for m in participants])
        
        # النشر في الشات العام (الروم الحالي) حصرياً وبدون أي إرسال خاص
        await interaction.channel.send(content=f"🔔 تجميعة المشاركين بالرايد: {mentions_str}", embed=embed)
        await interaction.followup.send("✅ | تم إنهاء الرايد ونشر النتائج في الشات العام بنجاح!", ephemeral=True)

class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ خاص بالإدارة ] بدء رايد جديد عبر الويب هوكس")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="raid-end", description="[ خاص بالإدارة ] إنهاء الرايد ونشر النتائج بالشات العام")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndModal())

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
