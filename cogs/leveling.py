import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import json
import os

DATA_FILE = "level_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_guild_settings(guild_id: str):
    data = load_data()
    if "guilds" not in data:
        data["guilds"] = {}
    
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {
            "leveling_status": False,
            "levels": {},
            "top_channel": None,
            "top_message": "🔥 | هؤلاء هم الأبطال الأكثر تفاعلاً لهذا الأسبوع !",
            "level_channel": None,
            "custom_level_message": "🎉 مبروك {member}! صعدت إلى **Level {level}** 🚀"
        }
        save_data(data)
    return data["guilds"][guild_id]

def update_guild_settings(guild_id: str, guild_data):
    data = load_data()
    if "guilds" not in data:
        data["guilds"] = {}
    data["guilds"][guild_id] = guild_data
    save_data(data)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_leaderboard_loop.start()

    def cog_unload(self):
        self.weekly_leaderboard_loop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        g_settings = get_guild_settings(guild_id)

        # التحقق هل نظام التلفيل مفعل في هذا السيرفر بالذات أم لا
        if not g_settings.get("leveling_status", False):
            return

        user_id = str(message.author.id)
        if "levels" not in g_settings:
            g_settings["levels"] = {}

        if user_id not in g_settings["levels"]:
            g_settings["levels"][user_id] = {"xp": 0, "level": 1}

        xp_gain = random.randint(15, 25)
        user_data = g_settings["levels"][user_id]
        user_data["xp"] += xp_gain

        xp_needed = user_data["level"] * 100

        if user_data["xp"] >= xp_needed:
            user_data["xp"] -= xp_needed
            user_data["level"] += 1
            new_level = user_data["level"]
            
            # تحديد القناة الخاصة بهذا السيرفر حصرياً
            target_channel = message.channel
            level_channel_id = g_settings.get("level_channel")
            if level_channel_id:
                custom_channel = message.guild.get_channel(level_channel_id)
                if custom_channel:
                    target_channel = custom_channel

            msg_template = g_settings.get("custom_level_message", "🎉 مبروك {member}! صعدت إلى **Level {level}** 🚀")
            final_msg = msg_template.replace("{member}", message.author.mention).replace("{level}", str(new_level))

            try:
                await target_channel.send(final_msg)
            except:
                pass
            
        update_guild_settings(guild_id, g_settings)

    @app_commands.command(name="toggle-leveling", description="[ خاص بالإدارة ] تفعيل أو إيقاف نظام التلفيل في هذا السيرفر فقط")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_leveling(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        g_settings = get_guild_settings(guild_id)
        
        current_status = g_settings.get("leveling_status", False)
        new_status = not current_status
        g_settings["leveling_status"] = new_status
        update_guild_settings(guild_id, g_settings)

        if new_status:
            await interaction.response.send_message("✅ | تم **تفعيل** نظام التلفيل بنجاح في هذا السيرفر فقط!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | تم **إيقاف وتعطيل** نظام التلفيل في هذا السيرفر فقط!", ephemeral=True)

    @app_commands.command(name="rank", description="معرفة لفلك الحالي ونقاط الـ XP الخاصة بك في هذا السيرفر")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer(ephemeral=False)
        
        target = member or interaction.user
        guild_id = str(interaction.guild_id)
        user_id = str(target.id)

        g_settings = get_guild_settings(guild_id)
        levels_data = g_settings.get("levels", {})

        if user_id not in levels_data:
            level = 1
            xp = 0
        else:
            level = levels_data[user_id]["level"]
            xp = levels_data[user_id]["xp"]

        xp_needed = level * 100

        embed = discord.Embed(
            title=f"📊 | إحصائيات الرانك لـ {target.name}",
            color=0x000000
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="المستوى ( Level )", value=str(level), inline=True)
        embed.add_field(name="النقاط ( XP )", value=f"{xp} / {xp_needed}", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="عرض قائمة أفضل 10 أعضاء متفاعلين في هذا السيرفر")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild_id = str(interaction.guild_id)

        g_settings = get_guild_settings(guild_id)
        levels_data = g_settings.get("levels", {})

        if not levels_data:
            await interaction.followup.send("لا توجد بيانات تفاعل مسجلة في هذا السيرفر حتى الآن ! ❌")
            return

        sorted_users = sorted(
            levels_data.items(),
            key=lambda item: (item[1]["level"], item[1]["xp"]),
            reverse=True
        )[:10]

        description = ""
        for index, (user_id, data) in enumerate(sorted_users, start=1):
            user = interaction.guild.get_member(int(user_id))
            name = user.mention if user else f"User ID: {user_id}"
            description += f"**#{index}** | {name}\n ┗ Level: **{data['level']}** | XP: **{data['xp']}**\n\n"

        embed = discord.Embed(
            title="🏆 | قائمة أفضل 10 متفاعلين في السيرفر",
            description=description,
            color=0x000000
        )
        embed.set_footer(text=f"Server: {interaction.guild.name}")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="set-level-channel", description="[ خاص بالإدارة ] تحديد القناة المخصصة لإرسال إشعارات صعود الفلل لهذا السيرفر")
    @app_commands.describe(channel="اختر القناة المخصصة للفلل")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        g_settings = get_guild_settings(guild_id)
        g_settings["level_channel"] = channel.id
        update_guild_settings(guild_id, g_settings)
        await interaction.response.send_message(f"✅ | تم تعيين قناة إشعارات التلفيل في هذا السيرفر إلى {channel.mention} !", ephemeral=True)

    @app_commands.command(name="disable-level-channel", description="[ خاص بالإدارة ] إلغاء قناة التلفيل المخصصة لتظهر الرسائل بنسس روم الدردشة")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_level_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        g_settings = get_guild_settings(guild_id)
        g_settings["level_channel"] = None
        update_guild_settings(guild_id, g_settings)
        await interaction.response.send_message("✅ | تم إلغاء قناة التلفيل المخصصة في هذا السيرفر. ستعود الرسائل في نفس روم الدردشة.", ephemeral=True)

    @app_commands.command(name="set-level-message", description="[ خاص بالإدارة ] تعديل رسالة التلفيل الخاصة بهذا السيرفر")
    @app_commands.describe(message="اكتب رسالة التلفيل الجديدة")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_message(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild_id)
        g_settings = get_guild_settings(guild_id)
        g_settings["custom_level_message"] = message
        update_guild_settings(guild_id, g_settings)
        await interaction.response.send_message(f"✅ | تم تحديث رسالة التلفيل في هذا السيرفر!\n📝 النص الجديد: `{message}`", ephemeral=True)

    @app_commands.command(name="set-top-channel", description="[ خاص بالإدارة ] تحديد قناة التوب الأسبوعي لهذا السيرفر")
    @app_commands.describe(channel="اختر القناة المخصصة")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_top_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        g_settings = get_guild_settings(guild_id)
        g_settings["top_channel"] = channel.id
        update_guild_settings(guild_id, g_settings)
        await interaction.response.send_message(f"✅ | تم تعيين قناة التوبات الأسبوعية في هذا السيرفر إلى {channel.mention} !", ephemeral=True)

    @app_commands.command(name="disable-top-channel", description="[ خاص بالإدارة ] إلغاء تفعيل قناة التوبات الأسبوعية لهذا السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_top_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        g_settings = get_guild_settings(guild_id)
        g_settings["top_channel"] = None
        update_guild_settings(guild_id, g_settings)
        await interaction.response.send_message("✅ | تم إلغاء تفعيل قناة التوبات الأسبوعية في هذا السيرفر.", ephemeral=True)

    @app_commands.command(name="set-top-message", description="[ خاص بالإدارة ] تخصيص رسالة التوب الأسبوعي لهذا السيرفر")
    @app_commands.describe(message="اكتب نص الرسالة الجديد")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_top_message(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild_id)
        g_settings = get_guild_settings(guild_id)
        g_settings["top_message"] = message
        update_guild_settings(guild_id, g_settings)
        await interaction.response.send_message(f"✅ | تم حفظ رسالة التوب الجديدة لهذا السيرفر بنجاح !", ephemeral=True)

    @tasks.loop(hours=168)
    async def weekly_leaderboard_loop(self):
        data = load_data()
        guilds_data = data.get("guilds", {})

        for guild_id, g_settings in guilds_data.items():
            if not g_settings.get("leveling_status", False):
                continue

            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            levels_data = g_settings.get("levels", {})
            top_channel_id = g_settings.get("top_channel")
            top_msg = g_settings.get("top_message", "🔥 | هؤلاء هم الأبطال الأكثر تفاعلاً لهذا الأسبوع !")

            if levels_data and top_channel_id:
                top_user_id = max(levels_data, key=lambda uid: (levels_data[uid]["level"], levels_data[uid]["xp"]))
                top_member = guild.get_member(int(top_user_id))
                
                if top_member:
                    channel = guild.get_channel(top_channel_id)
                    if channel:
                        embed = discord.Embed(
                            title="👑 | التوب الأسبوعي للمتفاعلين",
                            description=f"{top_msg}\n\n🏆 المركز الأول لهذا الأسبوع: {top_member.mention} 🎯",
                            color=0x000000
                        )
                        embed.set_thumbnail(url=top_member.display_avatar.url)
                        await channel.send(embed=embed)
                
                # تصفير رتب هذا السيرفر فقط للأسبوع الجديد
                g_settings["levels"] = {}
                update_guild_settings(guild_id, g_settings)

    @weekly_leaderboard_loop.before_loop
    async def before_weekly_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Leveling(bot))

