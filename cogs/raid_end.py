import discord
from discord.ext import commands, tasks
from discord import app_commands
import json, os, re, time

DATA_FILE = "raid_data.json"
EMBED_COLOR = 0x8B0000
GIF_BANNER_URL = "https://cdn.discordapp.com/attachments/1479214156560466045/1542918296322572338/Comp1-ezgif.com-crop-2.gif?ex=6aa4c663&is=6aa374e3&hm=4b16c8a711658887aa9f018379775fff77ef8c176114498832a5a3dc10e5b8eb&"

OWNER_ID = 1107355943408259112
admin_cooldowns = {}

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                d = json.load(f)
                for g in d:
                    if isinstance(d[g], dict):
                        d[g].setdefault("roblox_users", {})
                        d[g].setdefault("member_countries", {})
                        d[g].setdefault("custom_avatars", {})
                        d[g].setdefault("blacklist", [])
                return d
            except: return {}
    return {}

def save_raid_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

class CustomAvatarModal(discord.ui.Modal, title="👤 | جلب وحفظ سكن روبلوكس للتوب"):
    roblox_username = discord.ui.TextInput(label="اكتب يوزر روبلوكس أو الايدي (أو رابط مباشر)", style=discord.TextStyle.short, required=True)
    def __init__(self, gid, top_num):
        super().__init__()
        self.gid = gid
        self.top_num = str(top_num)
    async def on_submit(self, interaction: discord.Interaction):
        val = self.roblox_username.value.strip()
        
        if val.startswith("http"):
            link = val
        else:
            if val.isdigit():
                link = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={val}&size=420x420&format=Png&isCircular=false"
            else:
                link = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={val}&size=420x420&format=Png&isCircular=false"

        data = load_raid_data()
        data.setdefault(self.gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "custom_avatars": {}, "blacklist": []})
        data[self.gid]["custom_avatars"][self.top_num] = link
        save_raid_data(data)
        
        await interaction.response.send_message(f"✅ | تم ربط سكن روبلوكس بنجاح للتوب رقم `{self.top_num}` وتحديث اللوحة!", ephemeral=True)
        g = interaction.client.get_guild(int(self.gid))
        cog = interaction.client.get_cog("RaidSystemCog")
        if g and cog:
            await cog.send_or_update_webhook_top(self.gid, g)

class CustomAvatarRankModal(discord.ui.Modal, title="🔢 | حدد رقم التوب المطلوب"):
    top_position = discord.ui.TextInput(label="يا توب تريد تحط السكن له؟ (من 1 إلى 20)", style=discord.TextStyle.short, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        val = self.top_position.value.strip()
        if not val.isdigit():
            await interaction.response.send_message("❌ | يرجى كتابة رقم صحيح بين 1 و 20!", ephemeral=True)
            return
        num = int(val)
        if num < 1 or num > 20:
            await interaction.response.send_message("❌ | التوبات محددة من 1 إلى 20 فقط!", ephemeral=True)
            return
        gid = str(interaction.guild_id)
        await interaction.response.send_modal(CustomAvatarModal(gid, num))

class RaidEndInfoModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    raid_number = discord.ui.TextInput(label="RAID Number", required=True)
    enemy = discord.ui.TextInput(label="ENEMY", required=True)
    ally = discord.ui.TextInput(label="ALLY", required=True)
    duration = discord.ui.TextInput(label="DURATION", required=True)
    status_reason = discord.ui.TextInput(label="STATUS", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        view = RaidFinalMediaView(self.raid_number.value, self.enemy.value, self.ally.value, self.duration.value, self.status_reason.value, interaction.user)
        await interaction.response.send_message("👇 اضغط أدناه لإدخال المشاركين والروابط:", view=view, ephemeral=True)

class RaidFinalMediaView(discord.ui.View):
    def __init__(self, rn, en, al, dur, st, author):
        super().__init__(timeout=180)
        self.rn, self.en, self.al, self.dur, self.st, self.author = rn, en, al, dur, st, author
    @discord.ui.button(label="📝 إدخال المشاركين والروابط", style=discord.ButtonStyle.green, emoji="⭐")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ | ليس لك!", ephemeral=True)
            return
        await interaction.response.send_modal(RaidSubmitModal(self.rn, self.en, self.al, self.dur, self.st))

class RaidSubmitModal(discord.ui.Modal, title="👥 | MVPs & Media"):
    mvps_input = discord.ui.TextInput(label="MVPs (منشنات)", style=discord.TextStyle.paragraph, required=True)
    media_links = discord.ui.TextInput(label="Media Link", style=discord.TextStyle.paragraph, required=False)
    def __init__(self, rn, en, al, dur, st):
        super().__init__()
        self.rn, self.en, self.al, self.dur, self.st = rn, en, al, dur, st
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "custom_avatars": {}, "blacklist": []})
        data[gid]["win_streak"] = data[gid].get("win_streak", 0) + 1
        streak = data[gid]["win_streak"]
        uids = re.findall(r'<@!?(\d+)>', self.mvps_input.value)
        blacklist = data[gid].get("blacklist", [])
        
        for uid in uids:
            if uid in blacklist: continue
            data[gid]["raider_stats"][uid] = data[gid]["raider_stats"].get(uid, 0) + 1

        save_raid_data(data)
        cog = interaction.client.get_cog("RaidSystemCog")
        if cog: await cog.send_or_update_webhook_top(gid, interaction.guild)
        
        content = f"╭─〔 𝐒𝐂𝐎𝐑𝐄 〕─╮\n\n**𝐑𝐀𝐈𝐃:**\n╰➤{self.rn}\n\n**𝐄𝐍𝐄𝐌𝐘:**\n╰➤{self.en}\n\n**𝐀𝐋𝐋𝐘:**\n╰➤{self.al}\n\n**𝐃𝐔𝐑𝐀𝐓𝐈𝐎𝐍:**\n╰➤{self.dur}\n\n**𝐒𝐓𝐀𝐓𝐔🇸:**\n╰➤{self.st}\n\n**𝐌𝐕𝐏🇸:**\n╰➤ {self.mvps_input.value}\n\n"
        mval = self.media_links.value.strip() if self.media_links.value else ""
        img_url = None
        if mval and mval.lower() != "skip":
            urls = re.findall(r'https?://[^\s]+', mval)
            if urls:
                img_url = urls[0]
                content += f"**𝐏𝐑𝐎𝐎🇸:**\n╰➤ {mval}\n\n"
        content += f"🔥 **Win Streak:** `{streak} in a row`\n\n╰────────────────╯"
        emb = discord.Embed(color=EMBED_COLOR, description=content)
        if img_url: emb.set_image(url=img_url)
        emb.set_footer(text=f"Ended by {interaction.user.name} | VLX")
        await interaction.channel.send(content="🏁 **Raid Report:**", embed=emb)
        await interaction.followup.send("✅ | تم النشر والتحديث بنجاح!", ephemeral=True)

class RaidSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_webhook_loop.start()
    def cog_unload(self): self.weekly_webhook_loop.cancel()

    async def send_or_update_webhook_top(self, gid, guild):
        data = load_raid_data()
        if gid not in data: return
        g_data = data[gid]
        channel_id = g_data.get("webhook_channel_id")
        if not channel_id: return
        channel = guild.get_channel(int(channel_id))
        if not channel: return

        stats = g_data.get("raider_stats", {})
        blacklist = g_data.get("blacklist", [])
        cdict = g_data.get("member_countries", {})
        custom_avs = g_data.get("custom_avatars", {})
        
        filtered = {u: c for u, c in stats.items() if u not in blacklist and c > 0}
        top = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if not top: return

        embeds = []
        for i, (uid, cnt) in enumerate(top, 1):
            member = guild.get_member(int(uid)) or self.bot.get_user(int(uid))
            name = member.mention if member else f"<@{uid}>"
            cou = cdict.get(uid, "—")
            
            # التصميم النصي الدقيق مع الشريط الجانبي الأحمر للـ Embed وخلوه تماماً من يوزر روبلوكس بالنص
            text_desc = f"╔══『 TOP {i} 』══╗\n│  │   │ {name}\n│  <<< •  • >>>\n│  \n│  Country: {cou}\n│  —\n│  Raids Joined: {cnt}"
            
            emb = discord.Embed(color=EMBED_COLOR, description=text_desc)
            
            # وضع صورة السكن كصورة رئيسية (Image) في أسفل بطاقة التوب تماماً كما في طلبك وصورتك
            if str(i) in custom_avs:
                emb.set_image(url=custom_avs[str(i)])
                
            embeds.append(emb)

        # إضافة الفيديو الـ GIF الجديد في رسالة منفصلة أو إيمبد مستقل في الأسفل تماماً كما طلبت بالمكان الأخضر
        gif_emb = discord.Embed(color=EMBED_COLOR)
        gif_emb.set_image(url=GIF_BANNER_URL)
        embeds.append(gif_emb)

        msg_id = g_data.get("webhook_message_id")
        try:
            if msg_id:
                msg = await channel.fetch_message(int(msg_id))
                await msg.edit(content="", embeds=embeds)
                return
        except:
            pass

        new_msg = await channel.send(embeds=embeds)
        g_data["webhook_message_id"] = new_msg.id
        save_raid_data(data)

    @tasks.loop(hours=168)
    async def weekly_webhook_loop(self):
        data = load_raid_data()
        for gid, g_data in data.items():
            if g_data.get("webhook_channel_id"):
                guild = self.bot.get_guild(int(gid))
                if guild:
                    await self.send_or_update_webhook_top(gid, guild)
                    g_data["raider_stats"] = {}
                    g_data["win_streak"] = 0
                    save_raid_data(data)

    @weekly_webhook_loop.before_loop
    async def before_weekly_webhook(self): await self.bot.wait_until_ready()

    @app_commands.command(name="set-top-channel", description="تعيين قناة التوبات الأسبوعية في السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_top_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "custom_avatars": {}, "blacklist": []})
        data[gid]["webhook_channel_id"] = channel.id
        data[gid].pop("webhook_message_id", None)
        save_raid_data(data)
        
        await interaction.response.send_message(f"✅ | تم تعيين قناة التوبات الأسبوعية في هذا السيرفر إلى {channel.mention} !", ephemeral=True)
        await self.send_or_update_webhook_top(gid, interaction.guild)

    @app_commands.command(name="set-avatar", description="تحديد سكن روبلوكس لأي توب معين")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_avatar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CustomAvatarRankModal())

    @app_commands.command(name="set-country", description="تحديد دولة العضو")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_country(self, interaction: discord.Interaction, member: discord.Member, country_value: str):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "custom_avatars": {}, "blacklist": []})
        data[gid]["member_countries"][str(member.id)] = country_value.strip()
        save_raid_data(data)
        await self.send_or_update_webhook_top(gid, interaction.guild)
        await interaction.response.send_message(f"✅ | تم تحديث دولة {member.mention}", ephemeral=True)

    @app_commands.command(name="end-raid", description="إنهاء الرايد وتسجيل النتائج")
    @app_commands.checks.has_permissions(administrator=True)
    async def end_raid(self, interaction: discord.Interaction):
        if interaction.user.id == OWNER_ID:
            await interaction.response.send_modal(RaidEndInfoModal())
            return
        gid = str(interaction.guild_id)
        now = time.time()
        cd = 3 * 3600
        if gid in admin_cooldowns and now - admin_cooldowns[gid] < cd:
            rem = int(cd - (now - admin_cooldowns[gid]))
            await interaction.response.send_message(f"⏳ انتظر `{rem // 3600}س و {(rem % 3600) // 60}د`", ephemeral=True)
            return
        admin_cooldowns[gid] = now
        await interaction.response.send_modal(RaidEndInfoModal())

    @app_commands.command(name="set-roblox", description="ربط يوزر روبلوكس العام")
    async def set_roblox(self, interaction: discord.Interaction, username: str):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "custom_avatars": {}, "blacklist": []})
        data[gid]["roblox_users"][str(interaction.user.id)] = username.strip()
        save_raid_data(data)
        await interaction.response.send_message(f"✅ | تم التحديث (`{username.strip()}`)", ephemeral=True)
        await self.send_or_update_webhook_top(gid, interaction.guild)

    @app_commands.command(name="sync", description="مزامنة الأوامر يدوياً")
    async def sync_commands(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | للمالك فقط!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        synced = await self.bot.tree.sync()
        await interaction.followup.send(f"✅ | تمت المزامنة بنجاح (`{len(synced)}` أمر)", ephemeral=True)

    @app_commands.command(name="raid-mentions", description="نشر المنشنات")
    async def raid_mentions(self, interaction: discord.Interaction, mentions_content: str):
        emb = discord.Embed(title="👥 | Mentions", description=mentions_content, color=EMBED_COLOR)
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="raid-add", description="إضافة نقاط لعضو")
    async def raid_add(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | للمالك فقط!", ephemeral=True)
            return
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "custom_avatars": {}, "blacklist": []})
        data[gid]["raider_stats"][str(member.id)] = amount
        save_raid_data(data)
        await self.send_or_update_webhook_top(gid, interaction.guild)
        await interaction.response.send_message(f"✅ | تم التحديث بنجاح", ephemeral=True)

    @app_commands.command(name="raid-reset", description="تصفير النقاط")
    async def raid_reset(self, interaction: discord.Interaction, member: discord.Member = None):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | للمالك فقط!", ephemeral=True)
            return
        gid = str(interaction.guild_id)
        data = load_raid_data()
        if gid not in data:
            await interaction.response.send_message("❌ | لا توجد بيانات!", ephemeral=True)
            return
        if member:
            data[gid]["raider_stats"][str(member.id)] = 0
            save_raid_data(data)
            await self.send_or_update_webhook_top(gid, interaction.guild)
            await interaction.response.send_message(f"✅ | تم تصفير نقاط العضو", ephemeral=True)
        else:
            data[gid]["raider_stats"] = {}
            data[gid]["win_streak"] = 0
            data[gid]["custom_avatars"] = {}
            save_raid_data(data)
            await self.send_or_update_webhook_top(gid, interaction.guild)
            await interaction.response.send_message("✅ | تم تصفير السيرفر بالكامل.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidSystemCog(bot))

