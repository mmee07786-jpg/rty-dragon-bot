import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import re
import time
import aiohttp

DATA_FILE = "raid_data.json"
EMBED_COLOR = 0x8B0000

# 🔴 الآيدي الخاص بك (فهد)
OWNER_ID = 1107355943408259112

admin_cooldowns = {}

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # التأكد من وجود خانة صور التوبات
                for g_id in data:
                    if isinstance(data[g_id], dict):
                        data[g_id].setdefault("top_avatars", {})
                return data
            except json.JSONDecodeError:
                return {}
    return {}

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
        placeholder="ضع رابط الصورة أو الفيديو هنا...",
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
        guild_id = str(interaction.guild_id)
        data = load_raid_data()

        if guild_id not in data:
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "top_avatars": {}}

        data[guild_id]["win_streak"] = data[guild_id].get("win_streak", 0) + 1
        current_streak = data[guild_id]["win_streak"]

        if "raider_stats" not in data[guild_id]:
            data[guild_id]["raider_stats"] = {}

        user_ids = re.findall(r'<@!?(\d+)>', self.mvps_input.value)
        for uid in user_ids:
            if uid not in data[guild_id]["raider_stats"]:
                data[guild_id]["raider_stats"][uid] = 0
            data[guild_id]["raider_stats"][uid] += 1

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
        extracted_image_url = None

        if media_val and media_val.lower() != "skip":
            urls = re.findall(r'https?://[^\s]+', media_val)
            if urls:
                extracted_image_url = urls[0]
                report_content += f"**𝐏𝐑𝐎𝐎𝐅𝐒 / 𝐌𝐄𝐃𝐈𝐀:**\n╰➤ {media_val}\n\n"

        report_content += (
            f"🔥 **Win Streak:** `{current_streak} in a row`\n\n"
            f"╰────────────────╯"
        )

        embed = discord.Embed(color=EMBED_COLOR, description=report_content)
        if extracted_image_url:
            embed.set_image(url=extracted_image_url)

        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="🏁 **Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("✅ | تم نشر التقرير وتحديث نقاط الرايدات في هذا السيرفر بنجاح!", ephemeral=True)

# نافذة إدخال رقم التوب ورابط الصورة
class TopAvatarModal(discord.ui.Modal, title="🖼️ | تعيين صورة التوب"):
    top_rank = discord.ui.TextInput(
        label="أدخل رقم التوب (من 1 إلى 20)",
        placeholder="مثال: 1 أو 5 أو 20...",
        style=discord.TextStyle.short,
        required=True
    )
    image_url = discord.ui.TextInput(
        label="رابط الصورة",
        placeholder="ضع رابط الصورة هنا...",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # التحقق هل الرقم المدخل صالح أم لا
        try:
            rank = int(self.top_rank.value.strip())
        except ValueError:
            await interaction.followup.send("❌ | يرجى إدخال رقم صحيحي صحيح فقط!", ephemeral=True)
            return

        if rank < 1 or rank > 20:
            await interaction.followup.send("❌ | ماكو هيك توب! (أقصى حد هو توب 20)", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id not in data:
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "top_avatars": {}}
        
        if "top_avatars" not in data[guild_id]:
            data[guild_id]["top_avatars"] = {}

        # حفظ رابط الصورة للترتيب المحدد
        data[guild_id]["top_avatars"][str(rank)] = self.image_url.value.strip()
        save_raid_data(data)

        # تحديث الويب هوك فوراً إذا كان مفَعلاً
        cog = interaction.client.get_cog("RaidSystemCog")
        if cog:
            await cog.send_or_update_webhook_top(guild_id, interaction.guild)

        await interaction.followup.send(f"✅ | تم حفظ صورة التوب رقم **{rank}** وتحديث القائمة بنجاح!", ephemeral=True)

class RaidSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_webhook_loop.start()

    def cog_unload(self):
        self.weekly_webhook_loop.cancel()

    async def send_or_update_webhook_top(self, guild_id, guild):
        data = load_raid_data()
        if guild_id not in data:
            return
        
        g_data = data[guild_id]
        webhook_url = g_data.get("webhook_url")
        if not webhook_url:
            return

        stats = g_data.get("raider_stats", {})
        sorted_raiders = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:20]
        top_avatars = g_data.get("top_avatars", {})

        description = ""
        for index, (uid, count) in enumerate(sorted_raiders, start=1):
            member = guild.get_member(int(uid)) or self.bot.get_user(int(uid))
            name = member.mention if member else f"User ID: {uid}"
            
            # جلب رابط الصورة الخاصة بهذا التوب إن وجدت
            avatar_line = ""
            if str(index) in top_avatars:
                avatar_line = f"│ Image: {top_avatars[str(index)]}\n"

            # التصميم المطابق لطلبك تماماً مع منشن العضو وصورة التوب
            description += (
                f"┌─── 「 TOP {index} 」 ───┐\n"
                f"│ │\n"
                f"│ <<< • . >>>\n"
                f"│ {name}\n"
                f"{avatar_line}"
                f"│ Raids Joined: **{count}**\n"
                f"└─────────────────────┘\n\n"
            )

        if not description:
            description = "لا توجد أي نقاط رايدات مسجلة حتى الآن."

        embed = {
            "title": "🏆 | VLX Clan Weekly Top 20 Raiders",
            "description": description,
            "color": 9109504,
            "footer": {"text": "VLX Clan Automated Weekly Top System"}
        }

        payload = {"embeds": [embed]}

        async with aiohttp.ClientSession() as session:
            msg_id = g_data.get("webhook_message_id")
            if msg_id:
                edit_url = f"{webhook_url}/messages/{msg_id}"
                async with session.patch(edit_url, json=payload) as resp:
                    if resp.status == 200:
                        return
            
            async with session.post(f"{webhook_url}?wait=true", json=payload) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    g_data["webhook_message_id"] = res_json.get("id")
                    save_raid_data(data)

    @tasks.loop(hours=168)
    async def weekly_webhook_loop(self):
        data = load_raid_data()
        for guild_id, g_data in data.items():
            if g_data.get("webhook_url"):
                guild = self.bot.get_guild(int(guild_id))
                if guild:
                    await self.send_or_update_webhook_top(guild_id, guild)
                    # تصفير النقاط وسلسلة الانتصارات أسبوعياً تلقائياً
                    g_data["raider_stats"] = {}
                    g_data["win_streak"] = 0
                    g_data["top_avatars"] = {} # تصفير صور التوبات أسبوعياً أيضاً مع الجدول
                    save_raid_data(data)

    @weekly_webhook_loop.before_loop
    async def before_weekly_webhook(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="end-raid", description="[ Admin Only ] Conclude the raid and record results")
    @app_commands.checks.has_permissions(administrator=True)
    async def end_raid(self, interaction: discord.Interaction):
        if interaction.user.id == OWNER_ID:
            await interaction.response.send_modal(RaidEndInfoModal())
            return

        guild_id = str(interaction.guild_id)
        current_time = time.time()
        cooldown_duration = 3 * 3600

        if guild_id in admin_cooldowns:
            elapsed_time = current_time - admin_cooldowns[guild_id]
            if elapsed_time < cooldown_duration:
                remaining_seconds = int(cooldown_duration - elapsed_time)
                hours = remaining_seconds // 3600
                minutes = (remaining_seconds % 3600) // 60
                seconds = remaining_seconds % 60
                
                await interaction.response.send_message(
                    f"⏳ | عذراً، لا يمكنك استخدام أمر الـ End Raid حالياً.\n"
                    f"يجب الانتظار لمدة **3 ساعات** بين كل رايد وآخر للأدمنية.\n"
                    f"⏱️ **الوقت المتبقي بدقة:** `{hours} ساعة و {minutes} دقيقة و {seconds} ثانية`",
                    ephemeral=True
                )
                return

        admin_cooldowns[guild_id] = current_time
        await interaction.response.send_modal(RaidEndInfoModal())

    @app_commands.command(name="set-raider-avatar", description="إضافة أو تعديل صورة اللاعب في لوحة توب الرايدات أسبوعياً")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raider_avatar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TopAvatarModal())

    @app_commands.command(name="set-raid-webhook", description="[ خاص بالإدارة ] تعيين رابط الويب هوك لعرض أفضل 20 رايدر بالشكل المزخرف وتحديثه أسبوعياً")
    @app_commands.describe(webhook_url="الصق رابط الويب هوك هنا", channel="القناة التي سيتم إرسال التوب فيها")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raid_webhook(self, interaction: discord.Interaction, webhook_url: str, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id not in data:
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "top_avatars": {}}

        data[guild_id]["webhook_url"] = webhook_url
        data[guild_id]["webhook_channel_id"] = channel.id
        data[guild_id].pop("webhook_message_id", None)
        save_raid_data(data)

        await interaction.response.send_message("✅ | تم تفعيل ويب هوك توب الرايدات بنجاح! جاري إرسال القائمة المزخرفة الآن...", ephemeral=True)
        await self.send_or_update_webhook_top(guild_id, interaction.guild)

    @app_commands.command(name="disable-raid-webhook", description="[ خاص بالإدارة ] إلغاء وتعطيل خاصية ويب هوك توب الرايدات الأسبوعي")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_raid_webhook(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id in data and "webhook_url" in data[guild_id]:
            data[guild_id].pop("webhook_url", None)
            data[guild_id].pop("webhook_channel_id", None)
            data[guild_id].pop("webhook_message_id", None)
            save_raid_data(data)
            await interaction.response.send_message("✅ | تم إلغاء وتعطيل خاصية ويب هوك توب الرايدات في هذا السيرفر بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | لا يوجد ويب هوك مفعل أساساً في هذا السيرفر!", ephemeral=True)

    @app_commands.command(name="sync", description="[ Owner Only ] تحديث ومزامنة أوامر البوت")
    async def sync_commands(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | عذراً، هذا الأمر مخصص لـ **فهد** فقط!", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await self.bot.tree.sync()
            await interaction.followup.send(f"✅ | تم مزامنة وتحديث `{len(synced)}` أمر بنجاح!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء المزامنة: `{e}`", ephemeral=True)

    @app_commands.command(name="raid-mentions", description="نشر منشنات المشاركين")
    @app_commands.describe(mentions_content="الصق منشنات الأعضاء هنا")
    async def raid_mentions(self, interaction: discord.Interaction, mentions_content: str):
        embed = discord.Embed(title="👥 | Raid Members Mentions", description=mentions_content, color=EMBED_COLOR)
        embed.set_footer(text=f"Mentions by {interaction.user.name} | VLX Clan")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-add", description="[ Owner Only ] إضافة أو تعيين عدد الرايدات لعضو معين")
    @app_commands.describe(member="اختر العضو", amount="عدد الرايدات")
    async def raid_add(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | عذراً، هذا الأمر مخصص لـ **فهد** فقط!", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id not in data:
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "top_avatars": {}}
            
        data[guild_id]["raider_stats"][str(member.id)] = amount
        save_raid_data(data)

        embed = discord.Embed(
            title="✅ | Raid Statistics Updated",
            description=f"تم تحديث سجل الرايدات للعضو {member.mention}\nوأصبح رصيده: **{amount}** رايد.",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Updated by Developer (Fahd) | VLX Clan")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="raid-reset", description="[ Owner Only ] تصفير أو حذف نقاط ورايدات عضو معين أو كل السيرفر")
    @app_commands.describe(member="اختر العضو لتصفير نقاطه (اختياري)")
    async def raid_reset(self, interaction: discord.Interaction, member: discord.Member = None):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | عذراً، هذا الأمر مخصص لـ **فهد** فقط!", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        data = load_raid_data()

        if guild_id not in data:
            await interaction.response.send_message("❌ | لا توجد بيانات مسجلة في هذا السيرفر أساساً!", ephemeral=True)
            return

        if member:
            if str(member.id) in data[guild_id].get("raider_stats", {}):
                data[guild_id]["raider_stats"][str(member.id)] = 0
                save_raid_data(data)
                await interaction.response.send_message(f"✅ | تم تصفير نقاط الرايدات للعضو {member.mention} بنجاح!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ | هذا العضو ليس لديه أي نقاط مسجلة مسبقاً في هذا السيرفر.", ephemeral=True)
        else:
            data[guild_id]["raider_stats"] = {}
            data[guild_id]["win_streak"] = 0
            data[guild_id]["top_avatars"] = {}
            save_raid_data(data)
            await interaction.response.send_message("✅ | تم تصفير جميع إحصائيات وسلسلة انتصارات هذا السيرفر بالكامل بنجاح!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidSystemCog(bot))

