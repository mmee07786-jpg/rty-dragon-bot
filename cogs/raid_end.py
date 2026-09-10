import discord
from discord.ext import commands, tasks
from discord import app_commands
import json, os, re, time, io, aiohttp
from PIL import Image, ImageDraw, ImageFont

DATA_FILE = "raid_data.json"
EMBED_COLOR = 0x8B0000
GIF_BANNER_URL = "https://cdn.discordapp.com/attachments/1479214156560466045/1542918296322572338/Comp1-ezgif.com-crop-2.gif"
OWNER_ID = 1107355943408259112

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

async def get_rob_avatar(username):
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

async def make_card(idx, name, country, count, abytes):
    w, h = 600, 220
    card = Image.new("RGBA", (w, h), (20, 20, 20, 255))
    draw = ImageDraw.Draw(card)
    draw.rectangle([5, 5, w - 5, h - 5], outline=(139, 0, 0), width=3)
    txt = f"╔══『 TOP {idx} 』══╗\n│  Name: {name}\n│  Country: {country}\n│  Raids Joined: {count}"
    try: font = ImageFont.truetype("arial.ttf", 18)
    except: font = ImageFont.load_default()
    draw.text((20, 20), txt, fill=(255, 255, 255, 255), font=font)
    if abytes:
        aimg = Image.open(io.BytesIO(abytes)).convert("RGBA").resize((140, 140), Image.Resampling.LANCZOS)
        draw.rectangle([435, 38, 585, 188], outline=(0, 255, 100), width=3)
        card.paste(aimg, (440, 43), aimg)
    out = io.BytesIO()
    card.save(out, format="PNG")
    out.seek(0)
    return out

class RaidModal(discord.ui.Modal, title="🏁 تسجيل نتائج الرايد"):
    rnum = discord.ui.TextInput(label="رقم الرايد (RAID Number)", required=True)
    enemy = discord.ui.TextInput(label="الكلان المنافس (ENEMY)", required=True)
    ally = discord.ui.TextInput(label="الحلفاء (ALLY)", required=True)
    dur = discord.ui.TextInput(label="الوقت (DURATION)", required=True)
    mvps = discord.ui.TextInput(label="منشنات المشاركين (MVPs)", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gid = str(interaction.guild_id)
        data = load_data()
        data.setdefault(gid, {"stats": {}, "streak": 0, "rob": {}, "countries": {}, "blacklist": [], "top_ch": None, "top_msg": None})
        
        data[gid]["streak"] += 1
        streak = data[gid]["streak"]
        
        uids = re.findall(r'<@!?(\d+)>', self.mvps.value)
        blacklist = data[gid].get("blacklist", [])
        
        for uid in uids:
            if uid in blacklist: continue
            data[gid]["stats"][uid] = data[gid]["stats"].get(uid, 0) + 1

        save_data(data)
        
        cog = interaction.client.get_cog("NewRaidSystem")
        if cog: await cog.update_top_board(gid, interaction.guild)

        desc = f"╭─〔 𝐒𝐂𝐎𝐑𝐄 〕─╮\n\n**𝐑𝐀𝐈𝐃:** {self.rnum.value}\n**𝐄𝐍𝐄𝐌𝐘:** {self.enemy.value}\n**𝐀𝐋𝐋𝐘:** {self.ally.value}\n**𝐃𝐔𝐑𝐀𝐓𝐈𝐎𝐍:** {self.dur.value}\n\n**𝐌𝐕𝐏🇸:**\n{self.mvps.value}\n\n🔥 **Win Streak:** `{streak}`\n╰────────────────╯"
        emb = discord.Embed(color=EMBED_COLOR, description=desc)
        emb.set_footer(text=f"Ended by {interaction.user.name}")
        
        await interaction.channel.send(content="🏁 **تقرير الرايد الجديد:**", embed=emb)
        await interaction.followup.send("✅ | تم تسجيل الرايد وتحديث التوب بنجاح!", ephemeral=True)

class NewRaidSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_top_board(self, gid, guild):
        data = load_data()
        if gid not in data or not data[gid].get("top_ch"): return
        ch = guild.get_channel(int(data[gid]["top_ch"]))
        if not ch: return
        
        stats = data[gid].get("stats", {})
        blacklist = data[gid].get("blacklist", [])
        rob = data[gid].get("rob", {})
        countries = data[gid].get("countries", {})
        
        filtered = {u: c for u, c in stats.items() if u not in blacklist}
        top = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if not top:
            emb = discord.Embed(title="🏆 | VLX Top 20 Raiders", description="لا توجد نقاط مسجلة حالياً.", color=EMBED_COLOR)
            emb.set_image(url=GIF_BANNER_URL)
            try:
                if data[gid].get("top_msg"):
                    m = await ch.fetch_message(int(data[gid]["top_msg"]))
                    await m.edit(embed=emb, attachments=[])
                else:
                    nm = await ch.send(embed=emb)
                    data[gid]["top_msg"] = str(nm.id)
                    save_data(data)
            except: pass
            return

        embeds, files = [], []
        for i, (uid, cnt) in enumerate(top, 1):
            uname = rob.get(uid, "غير متوفر")
            cou = countries.get(uid, "—")
            abytes = await get_rob_avatar(uname) if uname != "غير متوفر" else None
            card_io = await make_card(i, uname, cou, cnt, abytes)
            fname = f"card_{i}.png"
            files.append(discord.File(card_io, filename=fname))
            emb = discord.Embed(color=EMBED_COLOR)
            emb.set_image(url=f"attachment://{fname}")
            embeds.append(emb)

        banner = discord.Embed(color=EMBED_COLOR)
        banner.set_image(url=GIF_BANNER_URL)
        embeds.append(banner)

        try:
            if data[gid].get("top_msg"):
                m = await ch.fetch_message(int(data[gid]["top_msg"]))
                await m.edit(embeds=embeds, attachments=files)
            else:
                nm = await ch.send(embeds=embeds, files=files)
                data[gid]["top_msg"] = str(nm.id)
                save_data(data)
        except: pass

    @app_commands.command(name="end-raid", description="إنهاء وتسجيل الرايد الجديد")
    @app_commands.checks.has_permissions(administrator=True)
    async def end_raid(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidModal())

    @app_commands.command(name="set-top", description="تحديد قناة التوب 20")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_top(self, interaction: discord.Interaction, channel: discord.TextChannel):
        gid = str(interaction.guild_id)
        data = load_data()
        data.setdefault(gid, {"stats": {}, "streak": 0, "rob": {}, "countries": {}, "blacklist": [], "top_ch": None, "top_msg": None})
        data[gid]["top_ch"] = str(channel.id)
        data[gid]["top_msg"] = None
        save_data(data)
        await interaction.response.send_message(f"✅ | تم ربط لوحة التوب بقناة {channel.mention}", ephemeral=True)
        await self.update_top_board(gid, interaction.guild)

    @app_commands.command(name="set-roblox", description="ربط يوزر روبلوكس الخاص بك")
    async def set_roblox(self, interaction: discord.Interaction, username: str):
        gid = str(interaction.guild_id)
        data = load_data()
        data.setdefault(gid, {"stats": {}, "streak": 0, "rob": {}, "countries": {}, "blacklist": [], "top_ch": None, "top_msg": None})
        data[gid]["rob"][str(interaction.user.id)] = username.strip()
        save_data(data)
        await interaction.response.send_message(f"✅ | تم حفظ يوزرك بنجاح: `{username.strip()}`", ephemeral=True)
        await self.update_top_board(gid, interaction.guild)

    @app_commands.command(name="set-country", description="تحديد دولة العضو")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_country(self, interaction: discord.Interaction, member: discord.Member, country: str):
        gid = str(interaction.guild_id)
        data = load_data()
        data.setdefault(gid, {"stats": {}, "streak": 0, "rob": {}, "countries": {}, "blacklist": [], "top_ch": None, "top_msg": None})
        data[gid]["countries"][str(member.id)] = country.strip()
        save_data(data)
        await interaction.response.send_message(f"✅ | تم تحديث دولة {member.mention}", ephemeral=True)
        await self.update_top_board(gid, interaction.guild)

    @app_commands.command(name="sync", description="مزامنة الأوامر فورياً")
    async def sync_cmd(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ | للمالك فقط!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        self.bot.tree.copy_global_to(guild=interaction.guild)
        synced = await self.bot.tree.sync(guild=interaction.guild)
        await interaction.followup.send(f"✅ | تمت المزامنة الفورية بنجاح (`{len(synced)} أمر`)", ephemeral=True)

async def setup(bot):
    await bot.add_cog(NewRaidSystem(bot))
