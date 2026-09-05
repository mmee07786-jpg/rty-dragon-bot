import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
import google.generativeai as genai
import aiohttp
import io

DATA_FILE = "data.json"
RAID_FILE = "raid_data.json"

BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&"
EMBED_COLOR = 0x8B0000

# 🔴 ضع مفتاح الـ API الخاص بـ Gemini هنا
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    genai.configure(api_key=GEMINI_API_KEY)
    generation_config = {"temperature": 0.7, "top_p": 0.95, "top_k": 40, "max_output_tokens": 1024}
    ai_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction="You are a smart, friendly AI assistant on Discord. You must always reply in the exact same language the user writes to you in."
    )

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ----------------- قسم الريدات -----------------
class RaidStartModal(discord.ui.Modal, title="⚔️ | Raid Start & Announcement"):
    server_link = discord.ui.TextInput(label="Server Link", placeholder="", style=discord.TextStyle.short, required=True)
    difficulty = discord.ui.TextInput(label="Difficulty", placeholder="e.g., Hard / Extreme", style=discord.TextStyle.short, required=True)
    targets = discord.ui.TextInput(label="Targets / Matchup", placeholder="", style=discord.TextStyle.short, required=True, default="")
    counts = discord.ui.TextInput(label="Our Count & Their Count", placeholder="e.g., 4 vs 11", style=discord.TextStyle.short, required=True, default="? vs ?")
    region = discord.ui.TextInput(label="Region", placeholder="EU / ME", style=discord.TextStyle.short, required=True, default="EU")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 | جاري إرسال الريد بالخاص للأعضاء على شكل دفعات...", ephemeral=True)

        embed = discord.Embed(title="⚔️ **VLX Clan Raid Notification** ⚔️", color=EMBED_COLOR)
        embed.add_field(name="⚔️ Difficulty", value=f"`{self.difficulty.value}`", inline=False)
        embed.add_field(name="🎯 Targets", value=f"`{self.targets.value}`", inline=False)
        embed.add_field(name="🔢 Our Count & Their Count", value=f"`{self.counts.value}`", inline=False)
        embed.add_field(name="📡 Region", value=f"🌍 `{self.region.value}`", inline=False)
        
        instructions = "→ Click **Join** below to enter the server\n→ Follow callouts from raid leadership\n→ Stay until the raid is concluded"
        embed.add_field(name="📜 Instructions", value=instructions, inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link, emoji="🎮"))

        view = RaidView(self.server_link.value)
        await interaction.channel.send(content="@here 🔔 **New Raid Notification:**", embed=embed, view=view)

        online_members, offline_members = [], []
        for member in interaction.guild.members:
            if member.bot: continue
            if member.status != discord.Status.offline:
                online_members.append(member)
            else:
                offline_members.append(member)

        async def send_in_batches(member_list, batch_size, delay):
            for i in range(0, len(member_list), batch_size):
                batch = member_list[i:i + batch_size]
                tasks = [m.send(content="📩 **Raid Notification Direct Message:**", embed=embed, view=view) for m in batch if not m.bot]
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception:
                    pass
                await asyncio.sleep(delay)

        asyncio.create_task(send_in_batches(online_members, batch_size=30, delay=1.5))
        asyncio.create_task(send_in_batches(offline_members, batch_size=20, delay=2.0))

class RaidEndModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    duration = discord.ui.TextInput(label="Raid Duration", placeholder="e.g., 1:11:40", style=discord.TextStyle.short, required=True)
    result_status = discord.ui.TextInput(label="Raid Result", placeholder="VICTORY", style=discord.TextStyle.short, required=True, default="VICTORY")
    win_reason = discord.ui.TextInput(label="Reason / Operation Status", placeholder="e.g., Operation successful.", style=discord.TextStyle.short, required=True, default="Operation successful.")

    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        non_bots = [m for m in interaction.guild.members if not m.bot][:25]
        if not non_bots:
            await interaction.response.send_message("❌ | No members found in server!", ephemeral=True)
            return
        view = RaidSelectView(self.duration.value, self.result_status.value, self.win_reason.value, non_bots, interaction.user)
        await interaction.response.send_message("👇 **اختر المشاركين في الريد من القائمة أدناه:**", view=view, ephemeral=True)

class RaidSelectView(discord.ui.View):
    def __init__(self, duration, result_status, win_reason, members, author):
        super().__init__(timeout=180)
        self.duration, self.result_status, self.win_reason, self.author = duration, result_status, win_reason, author
        options = [discord.SelectOption(label=m.display_name[:50], value=str(m.id), description=f"User: {m.name}") for m in members]
        self.select_menu = discord.ui.Select(placeholder="⭐ اختر المشاركين من القائمة...", min_values=1, max_values=len(options), options=options)
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ | هذه القائمة ليست لك!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        data = load_json(RAID_FILE)
        
        participants = [interaction.guild.get_member(int(uid)) for uid in self.select_menu.values if interaction.guild.get_member(int(uid))]
        if not participants:
            await interaction.followup.send("❌ | لم تقم بتحديد أي مشارك!", ephemeral=True)
            return

        if "raider_stats" not in data: data["raider_stats"] = {}
        raider_list_text = ""
        for member in participants:
            m_id = str(member.id)
            data["raider_stats"][m_id] = data["raider_stats"].get(m_id, 0) + 1
            raider_list_text += f"★ <@{m_id}> — {data['raider_stats'][m_id]} RP\n"

        data["win_streak"] = data.get("win_streak", 0) + 1
        save_json(RAID_FILE, data)

        embed = discord.Embed(title="〈★〉🏁 **RAID CONCLUDED**", description=f"`{self.win_reason}`", color=EMBED_COLOR)
        embed.add_field(name="🏁 Result", value=f"`✅ {self.result_status}`", inline=False)
        embed.add_field(name="⏱️ Duration", value=f"`{self.duration}`", inline=False)
        embed.add_field(name="👥 Total Raiders", value=f"`{len(participants)}`", inline=False)
        embed.add_field(name="✅ Raider List", value=raider_list_text[:1024], inline=False)
        embed.add_field(name="🔥 Win Streak", value=f"`{data['win_streak']} in a row`", inline=False)
        if BANNER_URL: embed.set_image(url=BANNER_URL)
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="🏁 **Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("✅ | Results recorded successfully!", ephemeral=True)


# ----------------- الكلاس المجمع الأساسي (Bot Core) -----------------
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.chat_sessions = {}

    async def setup_hook(self):
        # تسجيل أوامر الريدات
        @self.tree.command(name="raid-start", description="[Admin Only] Start a raid")
        @app_commands.checks.has_permissions(administrator=True)
        async def raid_start(interaction: discord.Interaction):
            await interaction.response.send_modal(RaidStartModal())

        @self.tree.command(name="raid-end", description="[Admin Only] Conclude the raid")
        @app_commands.checks.has_permissions(administrator=True)
        async def raid_end(interaction: discord.Interaction):
            await interaction.response.send_modal(RaidEndModal(interaction.channel))

        # أوامر الذكاء الاصطناعي وتوليد الصور
        @self.tree.command(name="ai", description="تحدث مع الذكاء الاصطناعي بأي لغة")
        @app_commands.describe(prompt="اكتب سؤالك أو رسالتك")
        async def ai_chat(interaction: discord.Interaction, *, prompt: str):
            await interaction.response.defer()
            try:
                user_id = interaction.user.id
                if user_id not in self.chat_sessions:
                    self.chat_sessions[user_id] = ai_model.start_chat(history=[])
                response = self.chat_sessions[user_id].send_message(prompt)
                reply = response.text
                await interaction.followup.send(reply[:2000] if len(reply) > 2000 else reply)
            except Exception as e:
                await interaction.followup.send(f"❌ | خطأ: `{e}`", ephemeral=True)

        @self.tree.command(name="image", description="توليد صورة بالذكاء الاصطناعي")
        @app_commands.describe(prompt="اكتب وصف الصورة باللغة الإنجليزية")
        async def image(interaction: discord.Interaction, *, prompt: str):
            await interaction.response.defer()
            url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ | فشل توليد الصورة.", ephemeral=True)
                        return
                    data = await resp.read()
            file = discord.File(io.BytesIO(data), filename="image.png")
            embed = discord.Embed(title="🎨 | AI Image", description=f"**Prompt:** `{prompt}`", color=0x9b59b6)
            embed.set_image(url="attachment://image.png")
            await interaction.followup.send(embed=embed, file=file)

        @self.tree.command(name="clear-ai", description="مسح ذاكرة المحادثة مع الذكاء الاصطناعي")
        async def clear_ai(interaction: discord.Interaction):
            if interaction.user.id in self.chat_sessions:
                del self.chat_sessions[interaction.user.id]
                await interaction.response.send_message("🧹 | تم مسح الذاكرة بنجاح!", ephemeral=True)
            else:
                await interaction.response.send_message("ℹ️ | ليس لديك ذاكرة مخزنة.", ephemeral=True)

        # 🚀 المزامنة الفورية للأوامر
        await self.tree.sync()
        print("✅ | تمت مزامنة جميع الأوامر بنجاح وتظهر الآن في البوت!")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

# تشغيل البوت مع السحب التلقائي للتوكن من Railway
if __name__ == "__main__":
    bot = MyBot()
    token = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
    bot.run(token)
