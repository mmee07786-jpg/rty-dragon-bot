import discord
from discord.ext import commands, tasks
from discord import app_commands
import json, os, re, time, io, aiohttp
from PIL import Image, ImageDraw, ImageFont

DATA_FILE = "raid_data.json"
EMBED_COLOR = 0x8B0000
GIF_BANNER_URL = "https://cdn.discordapp.com/attachments/1479214156560466045/1542918296322572338/Comp1-ezgif.com-crop-2.gif?ex=6aa41da3&is=6aa2cc23&hm=d6ba53f570b7920d6f2f3fe64ae84729c07eaf4503123b6d2bb7c9f3733db944&"
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
                        d[g].setdefault("blacklist", [])
                return d
            except: return {}
    return {}

def save_raid_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

async def fetch_roblox_avatar(username):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username], "excludeBannedUsers": True}) as r:
                if r.status != 200: return None
                j = await r.json()
                dl = j.get("data", [])
                if not dl: return None
                uid = dl[0]["id"]
            async with s.get(f"https://thumbnails.roblox.com/v1/users/avatar-bust?userIds={uid}&size=420x420&format=Png&isCircular=false") as ir:
                if ir.status != 200: return None
                ij = await ir.json()
                idat = ij.get("data", [])
                if not idat: return None
                url = idat[0]["imageUrl"]
            async with s.get(url) as ar:
                if ar.status != 200: return None
                return await ar.read()
    except: return None

async def generate_top_card(idx, name, country, count, abytes):
    w, h = 600, 220
    card = Image.new("RGBA", (w, h), (20, 20, 20, 255))
    draw = ImageDraw.Draw(card)
    draw.rectangle([5, 5, w - 5, h - 5], outline=(139, 0, 0), width=3)
    txt = f"╔══『 TOP {idx} 』══╗\n│  {name}\n│  <<< •  • >>>\n│\n│  Country: {country}\n│  —\n│  Raids Joined: {count}"
    try: font = ImageFont.truetype("arial.ttf", 18)
    except: font = ImageFont.load_default()
    draw.text((20, 15), txt, fill=(255, 255, 255, 255), font=font)
    if abytes:
        aimg = Image.open(io.BytesIO(abytes)).convert("RGBA").resize((140, 140), Image.Resampling.LANCZOS)
        draw.rectangle([435, 38, 585, 188], outline=(0, 255, 100), width=3)
        card.paste(aimg, (440, 43), aimg)
    out = io.BytesIO()
    card.save(out, format="PNG")
    out.seek(0)
    return out

class RobloxUserModal(discord.ui.Modal, title="🎮 | ربط يوزر روبلوكس"):
    roblox_username = discord.ui.TextInput(label="شنو يوزرك بالعبة روبلوكس؟", style=discord.TextStyle.short, required=True)
    def __init__(self, gid):
        super().__init__()
        self.gid = gid
    async def on_submit(self, interaction: discord.Interaction):
        u = self.roblox_username.value.strip()
        data = load_raid_data()
        data.setdefault(self.gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
        data[self.gid]["roblox_users"][str(interaction.user.id)] = u
        save_raid_data(data)
        await interaction.response.send_message(f"✅ | تم حفظ يوزرك (`{u}`) بنجاح!", ephemeral=True)
        g = interaction.client.get_guild(int(self.gid))
        cog = interaction.client.get_cog("RaidSystemCog")
        if g and cog: await cog.send_or_update_webhook_top(self.gid, g)

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
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
        data[gid]["win_streak"] = data[gid].get("win_streak", 0) + 1
        streak = data[gid]["win_streak"]
        uids = re.findall(r'<@!?(\d+)>', self.mvps_input.value)
        rdict = data[gid]["roblox_users"]
        blacklist = data[gid].get("blacklist", [])
        
        for uid in uids:
            if uid in blacklist: continue
            data[gid]["raider_stats"][uid] = data[gid]["raider_stats"].get(uid, 0) + 1
            if uid not in rdict:
                try:
                    m = interaction.guild.get_member(int(uid)) or await interaction.client.fetch_user(int(uid))
                    if m:
                        v = discord.ui.View()
                        b = discord.ui.Button(label="🎮 ربط يوزر روبلوكس", style=discord.ButtonStyle.blurple)
                        b.callback = lambda i: i.response.send_modal(RobloxUserModal(gid))
                        v.add_item(b)
                        await m.send("🎉 مبروك دخولك التوبات! أرسل يوزر روبلوكس الخاص بك عبر الزر أدناه:", view=v)
                except: pass

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
                content += f"**𝐏𝐑𝐎𝐎𝐅🇸:**\n╰➤ {mval}\n\n"
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
        webhook_url = g_data.get("webhook_url")
        if not webhook_url: return

        stats = g_data.get("raider_stats", {})
        blacklist = g_data.get("blacklist", [])
        rdict = g_data.get("roblox_users", {})
        cdict = g_data.get("member_countries", {})
        
        filtered = {u: c for u, c in stats.items() if u not in blacklist}
        top = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if not top: return

        embeds, files = [], []
        for i, (uid, cnt) in enumerate(top, 1):
            usr = rdict.get(uid, "غير متوفر")
            cou = cdict.get(uid, "—")
            abytes = await fetch_roblox_avatar(usr) if usr != "غير متوفر" else None
            io_card = await generate_top_card(i, usr, cou, cnt, abytes)
            fname = f"top_{i}.png"
            files.append(discord.File(io_card, filename=fname))
            emb = discord.Embed(color=EMBED_COLOR)
            emb.set_image(url=f"attachment://{fname}")
            embeds.append(emb)

        banner_emb = discord.Embed(color=EMBED_COLOR)
        banner_emb.set_image(url=GIF_BANNER_URL)
        embeds.append(banner_emb)

        payload_embeds = []
        for idx, emb in enumerate(embeds):
            d = {"color": EMBED_COLOR}
            if emb.image and emb.image.url:
                d["image"] = {"url": emb.image.url}
            payload_embeds.append(d)

        form_data = aiohttp.FormData()
        form_data.add_field('payload_json', json.dumps({"embeds": payload_embeds}))
        for f in files:
            f.fp.seek(0)
            form_data.add_field(f'files[{files.index(f)}]', f.fp, filename=f.filename, content_type='image/png')

        async with aiohttp.ClientSession() as session:
            msg_id = g_data.get("webhook_message_id")
            if msg_id:
                edit_url = f"{webhook_url}/messages/{msg_id}"
                async with session.patch(edit_url, data=form_data) as resp:
                    if resp.status == 200: return
            
            async with session.post(f"{webhook_url}?wait=true", data=form_data) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    g_data["webhook_message_id"] = res_json.get("id")
                    save_raid_data(data)

    @tasks.loop(hours=168)
    async def weekly_webhook_loop(self):
        data = load_raid_data()
        for gid, g_data in data.items():
            if g_data.get("webhook_url"):
                guild = self.bot.get_guild(int(gid))
                if guild:
                    await self.send_or_update_webhook_top(gid, guild)
                    g_data["raider_stats"] = {}
                    g_data["win_streak"] = 0
                    save_raid_data(data)

    @weekly_webhook_loop.before_loop
    async def before_weekly_webhook(self): await self.bot.wait_until_ready()

    @app_commands.command(name="set-country", description="تحديد دولة العضو")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_country(self, interaction: discord.Interaction, member: discord.Member, country_value: str):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
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

    @app_commands.command(name="set-roblox", description="ربط يوزر روبلوكس")
    async def set_roblox(self, interaction: discord.Interaction, username: str):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
        data[gid]["roblox_users"][str(interaction.user.id)] = username.strip()
        save_raid_data(data)
        await interaction.response.send_message(f"✅ | تم التحديث (`{username.strip()}`)", ephemeral=True)
        await self.send_or_update_webhook_top(gid, interaction.guild)

    @app_commands.command(name="set-raid-webhook", description="تعيين ويب هوك توب الرايدات")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raid_webhook(self, interaction: discord.Interaction, webhook_url: str, channel: discord.TextChannel):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
        data[gid]["webhook_url"] = webhook_url
        data[gid]["webhook_channel_id"] = channel.id
        data[gid].pop("webhook_message_id", None)
        save_raid_data(data)
        await interaction.response.send_message("✅ | تم التفعيل بنجاح!", ephemeral=True)
        await self.send_or_update_webhook_top(gid, interaction.guild)

    @app_commands.command(name="disable-raid-webhook", description="تعطيل الويب هوك")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_raid_webhook(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        if gid in data and "webhook_url" in data[gid]:
            data[gid].pop("webhook_url", None)
            data[gid].pop("webhook_channel_id", None)
            data[gid].pop("webhook_message_id", None)
            save_raid_data(data)
            await interaction.response.send_message("✅ | تم التعطيل.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | غير مفعلة أساساً.", ephemeral=True)

    @app_commands.command(name="sync", description="مزامنة الأوامر")
    async def sync_commands(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | للمالك فقط!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        synced = await self.bot.tree.sync()
        await interaction.followup.send(f"✅ | تمت المزامنة (`{len(synced)}`)", ephemeral=True)

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
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
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
            save_raid_data(data)
            await self.send_or_update_webhook_top(gid, interaction.guild)
            await interaction.response.send_message("✅ | تم تصفير السيرفر بالكامل.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidSystemCog(bot))
