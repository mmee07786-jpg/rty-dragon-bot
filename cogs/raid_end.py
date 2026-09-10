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

def get_global_stats(d):
    gs = {}
    for g_id, g in d.items():
        if isinstance(g, dict) and "raider_stats" in g:
            blacklist = g.get("blacklist", [])
            for u, c in g["raider_stats"].items():
                if u not in blacklist:
                    gs[u] = gs.get(u, 0) + c
    return gs

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
    txt = f"╔══『 TOP {idx} 』══╗\n│  |   | {name}\n│  <<< •  • >>>\n│\n│  Country: {country}\n│  —\n│  Raids Joined: {count}"
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
    roblox_username = discord.ui.TextInput(label="يوزرك في روبلوكس", style=discord.TextStyle.short, required=True)
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
        if g and cog: await cog.send_or_update_top_message(self.gid, g)

class RaidEndInfoModal(discord.ui.Modal, title="🏁 | Raid Results"):
    raid_number = discord.ui.TextInput(label="RAID Number", required=True)
    enemy = discord.ui.TextInput(label="ENEMY", required=True)
    ally = discord.ui.TextInput(label="ALLY", required=True)
    duration = discord.ui.TextInput(label="DURATION", required=True)
    status_reason = discord.ui.TextInput(label="STATUS", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        view = RaidFinalMediaView(self.raid_number.value, self.enemy.value, self.ally.value, self.duration.value, self.status_reason.value, interaction.user)
        await interaction.response.send_message("👇 اضغط أدناه لإدخال المشاركين:", view=view, ephemeral=True)

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
                        await m.send("🎉 أرسل يوزر روبلوكس الخاص بك:", view=v)
                except: pass
        save_raid_data(data)
        cog = interaction.client.get_cog("RaidSystemCog")
        if cog: await cog.send_or_update_top_message(gid, interaction.guild)
        
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
        self.weekly_message_loop.start()
    def cog_unload(self): self.weekly_message_loop.cancel()

    async def send_or_update_top_message(self, gid, guild):
        data = load_raid_data()
        if gid not in data or not data[gid].get("top_channel_id"): return
        ch = guild.get_channel(int(data[gid]["top_channel_id"]))
        if not ch: return
        stats = data[gid].get("raider_stats", {})
        blacklist = data[gid].get("blacklist", [])
        rdict = data[gid].get("roblox_users", {})
        cdict = data[gid].get("member_countries", {})
        
        filtered = {u: c for u, c in stats.items() if u not in blacklist}
        top = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not top:
            emb = discord.Embed(title="🏆 | VLX Top Raiders", description="لا توجد نقاط مسجلة.", color=EMBED_COLOR)
            emb.set_image(url=GIF_BANNER_URL)
            mid = data[gid].get("top_message_id")
            if mid:
                try:
                    m = await ch.fetch_message(int(mid))
                    await m.edit(embed=emb, embeds=[], attachments=[])
                    return
                except: pass
            nm = await ch.send(embed=emb)
            data[gid]["top_message_id"] = str(nm.id)
            save_raid_data(data)
            return

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

        b_emb = discord.Embed(color=EMBED_COLOR)
        b_emb.set_image(url=GIF_BANNER_URL)
        embeds.append(b_emb)

        mid = data[gid].get("top_message_id")
        if mid:
            try:
                m = await ch.fetch_message(int(mid))
                await m.edit(embeds=embeds, attachments=files)
                return
            except: pass
        nm = await ch.send(embeds=embeds, files=files)
        data[gid]["top_message_id"] = str(nm.id)
        save_raid_data(data)

    @tasks.loop(hours=168)
    async def weekly_message_loop(self):
        for gid, gdata in load_raid_data().items():
            if gdata.get("top_channel_id"):
                g = self.bot.get_guild(int(gid))
                if g: await self.send_or_update_top_message(gid, g)

    @weekly_message_loop.before_loop
    async def before_weekly(self): await self.bot.wait_until_ready()

    @app_commands.command(name="set-country", description="تحديد دولة العضو")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_country(self, interaction: discord.Interaction, member: discord.Member, country_value: str):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
        data[gid]["member_countries"][str(member.id)] = country_value.strip()
        save_raid_data(data)
        await self.send_or_update_top_message(gid, interaction.guild)
        await interaction.response.send_message(f"✅ | تم تحديث دولة {member.mention} إلى: **{country_value.strip()}**", ephemeral=True)

    @app_commands.command(name="end-raid", description="إنهاء الرايد")
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
        await self.send_or_update_top_message(gid, interaction.guild)

    @app_commands.command(name="set-raid-top", description="تحديد قناة التوب")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raid_top(self, interaction: discord.Interaction, channel: discord.TextChannel):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
        data[gid]["top_channel_id"] = str(channel.id)
        data[gid].pop("top_message_id", None)
        save_raid_data(data)
        await interaction.response.send_message(f"✅ | تم التفعيل في {channel.mention}", ephemeral=True)
        await self.send_or_update_top_message(gid, interaction.guild)

    @app_commands.command(name="disable-raid-top", description="إلغاء التوب")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_raid_top(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        data = load_raid_data()
        if gid in data and "top_channel_id" in data[gid]:
            data[gid].pop("top_channel_id", None)
            data[gid].pop("top_message_id", None)
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

    @app_commands.command(name="raid-list", description="قائمة التوب 30")
    async def raid_list(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        gdata = load_raid_data().get(gid, {})
        stats = gdata.get("raider_stats", {})
        blacklist = gdata.get("blacklist", [])
        filtered = {u: c for u, c in stats.items() if u not in blacklist}
        if not filtered:
            await interaction.response.send_message("❌ | لا توجد بيانات!", ephemeral=True)
            return
        top30 = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:30]
        desc = "".join([f"#{i} <@{u}> ──> **{c}**\n" for i, (u, c) in enumerate(top30, 1)])
        emb = discord.Embed(title="📋 | Top 30 Raiders", description=desc, color=EMBED_COLOR)
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="raid-mentions", description="نشر المنشنات")
    async def raid_mentions(self, interaction: discord.Interaction, mentions_content: str):
        emb = discord.Embed(title="👥 | Mentions", description=mentions_content, color=EMBED_COLOR)
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="raid-rank", description="ترتيب العضو عالمياً")
    async def raid_rank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        cnt = get_global_stats(load_raid_data()).get(str(target.id), 0)
        emb = discord.Embed(title="📊 | Global Rank", color=EMBED_COLOR)
        emb.set_thumbnail(url=target.display_avatar.url)
        emb.add_field(name="User", value=target.mention)
        emb.add_field(name="Total", value=f"🛡️ `{cnt}`")
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="raid-top", description="التوب العالمي")
    async def raid_top(self, interaction: discord.Interaction):
        gs = get_global_stats(load_raid_data())
        if not gs:
            await interaction.response.send_message("❌ | لا توجد بيانات عالمية!", ephemeral=True)
            return
        top10 = sorted(gs.items(), key=lambda x: x[1], reverse=True)[:10]
        desc = "".join([f"#{i} <@{u}> ──> **{c}**\n" for i, (u, c) in enumerate(top10, 1)])
        emb = discord.Embed(title="🏆 | Global Leaderboard", description=desc, color=EMBED_COLOR)
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
        await self.send_or_update_top_message(gid, interaction.guild)
        await interaction.response.send_message(f"✅ | تم تحديث نقاط {member.mention} إلى {amount}", ephemeral=True)

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
            await self.send_or_update_top_message(gid, interaction.guild)
            await interaction.response.send_message(f"✅ | تم تصفير نقاط {member.mention}", ephemeral=True)
        else:
            data[gid]["raider_stats"] = {}
            data[gid]["win_streak"] = 0
            save_raid_data(data)
            await self.send_or_update_top_message(gid, interaction.guild)
            await interaction.response.send_message("✅ | تم تصفير إحصائيات السيرفر بالكامل.", ephemeral=True)

    @app_commands.command(name="raid-ban", description="[ Owner Only ] حظر عضو من التوبات")
    async def raid_ban(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | للمالك فقط!", ephemeral=True)
            return
        gid = str(interaction.guild_id)
        data = load_raid_data()
        data.setdefault(gid, {"raider_stats": {}, "win_streak": 0, "roblox_users": {}, "member_countries": {}, "blacklist": []})
        uid = str(member.id)
        if uid in data[gid]["blacklist"]:
            await interaction.response.send_message("⚠️ | العضو محظور مسبقاً!", ephemeral=True)
            return
        data[gid]["blacklist"].append(uid)
        save_raid_data(data)
        await self.send_or_update_top_message(gid, interaction.guild)
        await interaction.response.send_message(f"🚫 | تم حظر {member.mention} من التوبات بنجاح.", ephemeral=True)

    @app_commands.command(name="raid-unban", description="[ Owner Only ] رفع الحظر عن عضو")
    async def raid_unban(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | للمالك فقط!", ephemeral=True)
            return
        gid = str(interaction.guild_id)
        data = load_raid_data()
        uid = str(member.id)
        if gid not in data or uid not in data[gid].get("blacklist", []):
            await interaction.response.send_message("⚠️ | العضو ليس محظوراً!", ephemeral=True)
            return
        data[gid]["blacklist"].remove(uid)
        save_raid_data(data)
        await self.send_or_update_top_message(gid, interaction.guild)
        await interaction.response.send_message(f"✅ | تم رفع الحظر عن {member.mention} بنجاح.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidSystemCog(bot))

