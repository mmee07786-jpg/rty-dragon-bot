import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&"
CONFIG_FILE = "clan_config.json"
DATA_FILE = "raid_data.json"
ENTRANTS_FILE = "raid_entrants.json"

def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return default
    return default

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_config():
    return load_json(CONFIG_FILE, {"clan_name": "VLX", "embed_color": 0x8B0000})

def save_config(config):
    save_json(CONFIG_FILE, config)

def load_raid_data():
    return load_json(DATA_FILE, {"raider_stats": {}, "win_streak": 0})

# مودال بداية الرايد (النسخة النظيفة الأصلية)
class RaidStartModal(discord.ui.Modal, title="⚔️ | Raid Start & Announcement"):
    server_link = discord.ui.TextInput(label="Server Link", placeholder="", style=discord.TextStyle.short, required=True)
    difficulty = discord.ui.TextInput(label="Difficulty", placeholder="", style=discord.TextStyle.short, required=True)
    targets = discord.ui.TextInput(label="Targets / Matchup", placeholder="", style=discord.TextStyle.short, required=True, default="")
    counts = discord.ui.TextInput(label="Our Count & Their Count", placeholder="", style=discord.TextStyle.short, required=True, default="")
    region = discord.ui.TextInput(label="Region", placeholder="", style=discord.TextStyle.short, required=True, default="")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚀 | جاري إرسال إشعار الرايد...", ephemeral=True)

        config = load_config()
        clan = config.get("clan_name", "VLX")
        embed_color = config.get("embed_color", 0x8B0000)

        # تصفير أو بدء سجل دخول جديد لهذا الإعلان (اختياري، أو يتم تسجيلهم مباشرة)
        # حفظ رابط السيرفر مؤقتاً في ملف المشاركين لتوجيه الزر
        entrants_data = load_json(ENTRANTS_FILE, {"link": "", "users": []})
        entrants_data["link"] = self.server_link.value
        entrants_data["users"] = [] # تصفير القائمة للرايد الجديد
        save_json(ENTRANTS_FILE, entrants_data)

        embed = discord.Embed(title=f"⚔️ **{clan} Clan Raid Notification** ⚔️", color=embed_color)
        embed.add_field(name="⚔️ Difficulty", value=f"`{self.difficulty.value}`", inline=False)
        embed.add_field(name="🎯 Targets", value=f"`{self.targets.value}`", inline=False)
        embed.add_field(name="🔢 Our Count & Their Count", value=f"`{self.counts.value}`", inline=False)
        embed.add_field(name="📡 Region", value=f"🌍 `{self.region.value}`", inline=False)
        
        instructions = (
            "→ Click **Join** below to enter the server & record your entry\n"
            "→ Click **Leaderboard** to check top active raiders\n"
            "→ Follow callouts from raid leadership\n"
            "→ Stay until the raid is concluded"
        )
        embed.add_field(name="📜 Instructions", value=instructions, inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | {clan} Clan")

        class RaidView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Join", style=discord.ButtonStyle.link, url=self.server_link.value, emoji="🎮", custom_id="join_raid_btn")
            async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                pass # أزرار الروابط الخارجية لا تفعل كود داخلي مباشرة، لذلك سنستخدم System Listener بالأفل

        # طريقة بديلة لزر Join لضمان تسجيل من يضغط وتوجيهه للرابط:
        class JoinTrackerView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                self.link = link

            @discord.ui.button(label="Join", style=discord.ButtonStyle.green, emoji="🎮", custom_id="track_join_btn")
            async def track_join(self, interaction: discord.Interaction):
                data = load_json(ENTRANTS_FILE, {"link": self.link, "users": []})
                user_id = str(interaction.user.id)
                
                # التحقق إذا مسبقاً مسجل حتى لا يتكرر الشخص
                existing_ids = [u["id"] for u in data["users"]]
                if user_id not in existing_ids:
                    data["users"].append({
                        "id": user_id,
                        "time": datetime.now().strftime("%H:%M:%S")
                    })
                    save_json(ENTRANTS_FILE, data)
                
                # توجيهه للرابط عبر رسالة خاصة مؤقتة تحتوي على رابط السيرفر الحقيقي
                await interaction.response.send_message(f"🔗 | اضغط على الرابط أدناه للانضمام للسيرفر:\n{self.link}", ephemeral=True)

            @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.secondary, custom_id="show_leaderboard", emoji="🏆")
            async def leaderboard_btn(self, interaction: discord.Interaction):
                # يتم معالجتها عبر الـ Listener العام
                pass

        view = JoinTrackerView(self.server_link.value)
        await interaction.channel.send(content="@here 🔔 **New Raid Notification:**", embed=embed, view=view)

class RaidStartCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="[ Admin Only ] Start a raid with announcement")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="name_clan", description="[ Admin Only ] تعيين اسم الكلان الظهور بإعلانات الرايد")
    @app_commands.describe(name="اكتب اسم الكلان الجديد (اتركه فارغاً ليعود VLX)")
    @app_commands.checks.has_permissions(administrator=True)
    async def name_clan(self, interaction: discord.Interaction, name: str = "VLX"):
        config = load_config()
        config["clan_name"] = name
        save_config(config)
        await interaction.response.send_message(f"✅ | تم تحديث اسم الكلان بنجاح إلى: **{name}**", ephemeral=True)

    @app_commands.command(name="color_emed", description="[ Admin Only ] تغيير لون شريط إعلان الرايد")
    @app_commands.describe(hex_code="اكتب كود اللون (مثل #FF0000 أو 8B0000)")
    @app_commands.checks.has_permissions(administrator=True)
    async def color_emed(self, interaction: discord.Interaction, hex_code: str):
        cleaned_code = hex_code.strip()
        if cleaned_code.startswith("#"):
            cleaned_code = cleaned_code[1:]
        
        try:
            color_int = int(cleaned_code, 16)
        except ValueError:
            await interaction.response.send_message("❌ | كود اللون غير صحيح! استخدم صيغة صحيحة مثل `#FF0000`.", ephemeral=True)
            return

        config = load_config()
        config["embed_color"] = color_int
        save_config(config)
        await interaction.response.send_message(f"✅ | تم تحديث لون إعلان الرايد بنجاح إلى `#{cleaned_code}`", ephemeral=True)

    # الأمر الجديد: عرض قائمة الأشخاص الذين دخلوا الرابط بالترتيب
    @app_commands.command(name="raid-entrants", description="عرض قائمة الأشخاص الذين ضغطوا على زر الانضمام من الأول إلى الأخير")
    async def raid_entrants(self, interaction: discord.Interaction):
        entrants_data = load_json(ENTRANTS_FILE, {"users": []})
        users = entrants_data.get("users", [])

        if not users:
            await interaction.response.send_message("❌ | لم يقم أي شخص بالضغط على زر الانضمام حتى الآن!", ephemeral=True)
            return

        description = ""
        for index, entry in enumerate(users, start=1):
            user_obj = interaction.guild.get_member(int(entry["id"]))
            name = user_obj.mention if user_obj else f"User ID: {entry['id']}"
            medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
            description += f"{medal} {name} ──> `[ {entry['time']} ]`\n"

        config = load_config()
        embed = discord.Embed(
            title="📋 | Raid Entrants List (First to Last)",
            description=description,
            color=config.get("embed_color", 0x8B0000)
        )
        embed.set_footer(text=f"Total Entrants: {len(users)} | {config.get('clan_name', 'VLX')} Clan")
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id")
            
            if custom_id == "show_leaderboard":
                data = load_raid_data()
                stats = data.get("raider_stats", {})
                
                if not stats:
                    await interaction.response.send_message("❌ | No raid statistics recorded yet!", ephemeral=True)
                    return

                sorted_raiders = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
                
                description = ""
                for index, (uid, count) in enumerate(sorted_raiders, start=1):
                    user = interaction.guild.get_member(int(uid))
                    name = user.mention if user else f"User ID: {uid}"
                    medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
                    description += f"{medal} {name} ──> **{count}** Raids\n"

                config = load_config()
                lb_embed = discord.Embed(title="🏆 | Clan Top Raiders (Leaderboard)", description=description, color=config.get("embed_color", 0x8B0000))
                lb_embed.set_footer(text="Clan Statistics")
                await interaction.response.send_message(embed=lb_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidStartCog(bot))
