import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import re
import time

DATA_FILE = "raid_data.json"
EMBED_COLOR = 0x8B0000
GIF_BANNER_URL = "https://cdn.discordapp.com/attachments/1479214156560466045/1542918296322572338/Comp1-ezgif.com-crop-2.gif?ex=6aa41da3&is=6aa2cc23&hm=d6ba53f570b7920d6f2f3fe64ae84729c07eaf4503123b6d2bb7c9f3733db944&"

# 🔴 الآيدي الخاص بك (فهد)
OWNER_ID = 1107355943408259112

admin_cooldowns = {}

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # التأكد من وجود قائمة الحظر العامة أو لكل سيرفر
                for g_id in data:
                    if isinstance(data[g_id], dict) and "blacklist" not in data[g_id]:
                        data[g_id]["blacklist"] = []
                return data
            except json.JSONDecodeError:
                return {}
    return {}

def save_raid_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_global_stats(data):
    global_stats = {}
    for g_id, g_data in data.items():
        if isinstance(g_data, dict) and "raider_stats" in g_data:
            blacklist = g_data.get("blacklist", [])
            for uid, count in g_data["raider_stats"].items():
                if uid not in blacklist:
                    global_stats[uid] = global_stats.get(uid, 0) + count
    return global_stats

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
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "blacklist": []}

        if "blacklist" not in data[guild_id]:
            data[guild_id]["blacklist"] = []

        data[guild_id]["win_streak"] = data[guild_id].get("win_streak", 0) + 1
        current_streak = data[guild_id]["win_streak"]

        if "raider_stats" not in data[guild_id]:
            data[guild_id]["raider_stats"] = {}

        # استخراج الآيديات من المنشنات مع تجاهل المحظورين تماماً
        user_ids = re.findall(r'<@!?(\d+)>', self.mvps_input.value)
        blacklist = data[guild_id]["blacklist"]
        
        for uid in user_ids:
            if uid in blacklist:
                continue # تخطي العضو المحظور وعدم إضافة أي نقطة له
            if uid not in data[guild_id]["raider_stats"]:
                data[guild_id]["raider_stats"][uid] = 0
            data[guild_id]["raider_stats"][uid] += 1

        save_raid_data(data)

        # تحديث قائمة التوب تلقائياً في السيرفر بعد كل رايد جديد
        guild = interaction.guild
        cog = interaction.client.get_cog("RaidSystemCog")
        if cog:
            await cog.send_or_update_top_message(guild_id, guild)

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
        await interaction.followup.send("✅ | تم نشر التقرير وتحديث النقاط وقائمة التوب بنجاح!", ephemeral=True)

class RaidSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_message_loop.start()

    def cog_unload(self):
        self.weekly_message_loop.cancel()

    async def send_or_update_top_message(self, guild_id, guild):
        data = load_raid_data()
        if guild_id not in data:
            return
        
        g_data = data[guild_id]
        channel_id = g_data.get("top_channel_id")
        if not channel_id:
            return

        channel = guild.get_channel(int(channel_id))
        if not channel:
            return

        stats = g_data.get("raider_stats", {})
        blacklist = g_data.get("blacklist", [])
        
        # تصفية الأعضاء واستبعاد المحظورين نهائياً من القائمة
        filtered_stats = {uid: count for uid, count in stats.items() if uid not in blacklist}

        # ترتيب الأعضاء تنازلياً حسب عدد الرايدات
        sorted_raiders = sorted(filtered_stats.items(), key=lambda x: x[1], reverse=True)[:10]

        if not sorted_raiders:
            embed = discord.Embed(
                title="🏆 | VLX Clan Top Raiders",
                description="لا توجد أي نقاط رايدات مسجلة حتى الآن.",
                color=EMBED_COLOR
            )
            embed.set_image(url=GIF_BANNER_URL)
            msg_id = g_data.get("top_message_id")
            if msg_id:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    await msg.edit(embed=embed, embeds=[])
                    return
                except discord.NotFound:
                    pass
            new_msg = await channel.send(embed=embed)
            g_data["top_message_id"] = str(new_msg.id)
            save_raid_data(data)
            return

        embeds = []
        for index, (uid, count) in enumerate(sorted_raiders, start=1):
            member = guild.get_member(int(uid)) or self.bot.get_user(int(uid))
            name = member.mention if member else f"User ID: {uid}"
            
            box_content = (
                f"╔══『 TOP {index} 』══╗\n"
                f"│  |   |\n"
                f"│  <<< •  • >>>\n"
                f"│  {name}\n"
                f"│  Country:\n"
                f"│  —\n"
                f"│  Raids Joined: **{count}**"
            )

            emb = discord.Embed(description=box_content, color=EMBED_COLOR)
            emb.set_image(url=GIF_BANNER_URL)
            embeds.append(emb)

        msg_id = g_data.get("top_message_id")
        if msg_id:
            try:
                msg = await channel.fetch_message(int(msg_id))
                await msg.edit(embeds=embeds)
                return
            except discord.NotFound:
                pass

        new_msg = await channel.send(embeds=embeds)
        g_data["top_message_id"] = str(new_msg.id)
        save_raid_data(data)

    @tasks.loop(hours=168)
    async def weekly_message_loop(self):
        data = load_raid_data()
        for guild_id, g_data in data.items():
            if g_data.get("top_channel_id"):
                guild = self.bot.get_guild(int(guild_id))
                if guild:
                    await self.send_or_update_top_message(guild_id, guild)

    @weekly_message_loop.before_loop
    async def before_weekly_message(self):
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

    @app_commands.command(name="raid-ban", description="[ Owner Only ] حظر عضو من الظهور في التوبات أو حساب نقاطه للأبد")
    @app_commands.describe(member="اختر العضو المراد حظره")
    async def raid_ban(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | عذراً، هذا الأمر مخصص لـ **فهد** فقط!", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id not in data:
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "blacklist": []}

        if "blacklist" not in data[guild_id]:
            data[guild_id]["blacklist"] = []

        uid = str(member.id)
        if uid in data[guild_id]["blacklist"]:
            await interaction.response.send_message(f"⚠️ | العضو {member.mention} محظور مسبقاً من التوبات!", ephemeral=True)
            return

        data[guild_id]["blacklist"].append(uid)
        save_raid_data(data)

        # تحديث التوب فوراً لإزالته إن كان موجوداً
        await self.send_or_update_top_message(guild_id, interaction.guild)

        embed = discord.Embed(
            title="🚫 | Raid Leaderboard Ban",
            description=f"تم حظر العضو {member.mention} من التوبات والرايدات للأبد بنجاح!",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Banned by {interaction.user.name} | VLX Clan")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="raid-unban", description="[ Owner Only ] رفع الحظر عن عضو وإرجاعه للتوبات")
    @app_commands.describe(member="اختر العضو لرفع الحظر عنه")
    async def raid_unban(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | عذراً، هذا الأمر مخصص لـ **فهد** فقط!", ephemeral=True)
            return

        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id not in data or "blacklist" not in data[guild_id]:
            await interaction.response.send_message("❌ | لا توجد قائمة حظر مسجلة في هذا السيرفر!", ephemeral=True)
            return

        uid = str(member.id)
        if uid not in data[guild_id]["blacklist"]:
            await interaction.response.send_message(f"⚠️ | العضو {member.mention} ليس محظوراً أساساً!", ephemeral=True)
            return

        data[guild_id]["blacklist"].remove(uid)
        save_raid_data(data)

        # تحديث التوب لإظهاره إذا كان لديه نقاط سابقة
        await self.send_or_update_top_message(guild_id, interaction.guild)

        embed = discord.Embed(
            title="✅ | Raid Leaderboard Unban",
            description=f"تم رفع الحظر عن العضو {member.mention} وإرجاعه للتوبات بنجاح!",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Unbanned by {interaction.user.name} | VLX Clan")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set-raid-top", description="[ خاص بالإدارة ] تحديد قناة إرسال وتحديث توب الرايدات بالشكل المزخرف مع الشريط المتحرك")
    @app_commands.describe(channel="اختر القناة التي سيعمل فيها التوب")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raid_top(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id not in data:
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "blacklist": []}

        data[guild_id]["top_channel_id"] = str(channel.id)
        data[guild_id].pop("top_message_id", None)
        save_raid_data(data)

        await interaction.response.send_message(f"✅ | تم تفعيل توب الرايدات في القناة {channel.mention} بنجاح! جاري إرسال القوائم بالشكل المطلوب...", ephemeral=True)
        await self.send_or_update_top_message(guild_id, interaction.guild)

    @app_commands.command(name="disable-raid-top", description="[ خاص بالإدارة ] إلغاء وتعطيل خاصية توب الرايدات في هذا السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_raid_top(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        if guild_id in data and "top_channel_id" in data[guild_id]:
            data[guild_id].pop("top_channel_id", None)
            data[guild_id].pop("top_message_id", None)
            save_raid_data(data)
            await interaction.response.send_message("✅ | تم إلغاء وتعطيل خاصية توب الرايدات في هذا السيرفر بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | خاصية توب الرايدات غير مفعلة أساساً في هذا السيرفر!", ephemeral=True)

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

    @app_commands.command(name="raid-list", description="Auto-generate and send the top 30 raiders list for this server")
    async def raid_list(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        data = load_raid_data()
        guild_data = data.get(guild_id, {})
        stats = guild_data.get("raider_stats", {})
        blacklist = guild_data.get("blacklist", [])

        filtered_stats = {uid: count for uid, count in stats.items() if uid not in blacklist}

        if not filtered_stats:
            await interaction.response.send_message("❌ | No raid statistics recorded yet in this server!", ephemeral=True)
            return

        sorted_raiders = sorted(filtered_stats.items(), key=lambda x: x[1], reverse=True)[:30]
        description = ""
        for index, (uid, count) in enumerate(sorted_raiders, start=1):
            user = interaction.guild.get_member(int(uid)) or self.bot.get_user(int(uid))
            name = user.mention if user else f"User ID: {uid}"
            medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
            description += f"{medal} {name} ──> **{count}** Raids Won\n"

        embed = discord.Embed(title="📋 | VLX Clan Active Raiders List (Top 30 - This Server)", description=description, color=EMBED_COLOR)
        embed.set_footer(text=f"Requested by {interaction.user.name} | VLX Clan System")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-mentions", description="نشر منشنات المشاركين")
    @app_commands.describe(mentions_content="الصق منشنات الأعضاء هنا")
    async def raid_mentions(self, interaction: discord.Interaction, mentions_content: str):
        embed = discord.Embed(title="👥 | Raid Members Mentions", description=mentions_content, color=EMBED_COLOR)
        embed.set_footer(text=f"Mentions by {interaction.user.name} | VLX Clan")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-rank", description="معرفة عدد الرايدات العالمية للعضو")
    @app_commands.describe(member="اختر العضو (اختياري)")
    async def raid_rank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        data = load_raid_data()
        global_stats = get_global_stats(data)
        count = global_stats.get(str(target.id), 0)
        
        embed = discord.Embed(title="📊 | Global Raider Rank Statistics", color=EMBED_COLOR)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="User", value=target.mention, inline=False)
        embed.add_field(name="Total Global Raids Participated", value=f"🛡️ `{count} Raids`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid-top", description="عرض قائمة أفضل المشاركين عالمياً")
    async def raid_top(self, interaction: discord.Interaction):
        data = load_raid_data()
        global_stats = get_global_stats(data)
        
        if not global_stats:
            await interaction.response.send_message("❌ | لا توجد أي إحصائيات مسجلة عالمياً حتى الآن!", ephemeral=True)
            return

        sorted_raiders = sorted(global_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        description = ""
        for index, (uid, count) in enumerate(sorted_raiders, start=1):
            user = interaction.guild.get_member(int(uid)) or self.bot.get_user(int(uid))
            name = user.mention if user else f"User ID: {uid}"
            medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
            description += f"{medal} {name} ──> **{count}** Raids\n"

        embed = discord.Embed(title="🏆 | VLX Clan Global Raid Leaderboard (Top 10)", description=description, color=EMBED_COLOR)
        embed.set_footer(text="VLX Clan Global Statistics")
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
            data[guild_id] = {"raider_stats": {}, "win_streak": 0, "blacklist": []}
            
        data[guild_id]["raider_stats"][str(member.id)] = amount
        save_raid_data(data)

        guild = interaction.guild
        await self.send_or_update_top_message(guild_id, guild)

        embed = discord.Embed(
            title="✅ | Raid Statistics Updated",
            description=f"تم تحديث سجل الرايدات للعضو {member.mention}\nوأصبح إجمالي رايداته: **{amount}** رايد.",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Updated by {interaction.user.name} | VLX Clan")
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
                await self.send_or_update_top_message(guild_id, interaction.guild)
                await interaction.response.send_message(f"✅ | تم تصفير نقاط الرايدات للعضو {member.mention} بنجاح!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ | هذا العضو ليس لديه أي نقاط مسجلة مسبقاً في هذا السيرفر.", ephemeral=True)
        else:
            data[guild_id]["raider_stats"] = {}
            data[guild_id]["win_streak"] = 0
            save_raid_data(data)
            await self.send_or_update_top_message(guild_id, interaction.guild)
            await interaction.response.send_message("✅ | تم تصفير جميع إحصائيات وسلسلة انتصارات هذا السيرفر بالكامل بنجاح!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidSystemCog(bot))

