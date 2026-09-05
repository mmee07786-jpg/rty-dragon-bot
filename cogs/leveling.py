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
            return json.load(f)
    return {
        "server_levels": {},
        "top_channels": {},
        "top_messages": {},
        "level_channels": {},
        "custom_level_messages": {},
        "leveling_status": {} # مخزن حالة التلفيل لكل سيرفر (True / False)
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.weekly_leaderboard_loop.start()

    def cog_unload(self):
        self.weekly_leaderboard_loop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)

        # التحقق هل نظام التلفيل مفعل في هذا السيرفر أم لا (افتراضياً مغلق False)
        leveling_status = self.data.get("leveling_status", {})
        if not leveling_status.get(guild_id, False):
            return # إذا كان مغلقاً، يتجاهل الرسالة بالكامل ولا يحسب أي XP

        user_id = str(message.author.id)

        if "server_levels" not in self.data:
            self.data["server_levels"] = {}
        if guild_id not in self.data["server_levels"]:
            self.data["server_levels"][guild_id] = {}
        if user_id not in self.data["server_levels"][guild_id]:
            self.data["server_levels"][guild_id][user_id] = {"xp": 0, "level": 1}

        xp_gain = random.randint(15, 25)
        user_data = self.data["server_levels"][guild_id][user_id]
        user_data["xp"] += xp_gain

        xp_needed = user_data["level"] * 100

        if user_data["xp"] >= xp_needed:
            user_data["xp"] -= xp_needed
            user_data["level"] += 1
            new_level = user_data["level"]
            
            # تحديد الروم المخصص للتلفيل، أو إرسالها في نفس روم الدردشة إذا لم يُحدد روم خاص
            target_channel = message.channel
            level_channels = self.data.get("level_channels", {})
            if guild_id in level_channels:
                custom_channel = message.guild.get_channel(level_channels[guild_id])
                if custom_channel:
                    target_channel = custom_channel

            # جلب رسالة التلفيل المخصصة أو استخدام الرسالة الافتراضية
            custom_msgs = self.data.get("custom_level_messages", {})
            msg_template = custom_msgs.get(guild_id, "🎉 مبروك {member}! صعدت إلى **Level {level}** 🚀")
            
            final_msg = msg_template.replace("{member}", message.author.mention).replace("{level}", str(new_level))

            try:
                await target_channel.send(final_msg)
            except:
                pass
            
            save_data(self.data)

    @app_commands.command(name="toggle-leveling", description="[ خاص بالإدارة ] تفعيل أو إيقاف نظام التلفيل في السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_leveling(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "leveling_status" not in self.data:
            self.data["leveling_status"] = {}
        
        current_status = self.data["leveling_status"].get(guild_id, False)
        new_status = not current_status
        self.data["leveling_status"][guild_id] = new_status
        save_data(self.data)

        if new_status:
            await interaction.response.send_message("✅ | تم **تفعيل** نظام التلفيل بنجاح في السيرفر! أصبح البوت يحسب النقاط الآن.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | تم **إيقاف وتعطيل** نظام التلفيل في السيرفر! لن يتم احتساب أي نقاط.", ephemeral=True)

    @app_commands.command(name="rank", description="معرفة لفلك الحالي ونقاط الـ XP بالتفصيل")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer(ephemeral=False)
        
        target = member or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(target.id)

        server_levels = self.data.get("server_levels", {})
        if guild_id not in server_levels or user_id not in server_levels[guild_id]:
            level = 1
            xp = 0
        else:
            level = server_levels[guild_id][user_id]["level"]
            xp = server_levels[guild_id][user_id]["xp"]

        xp_needed = level * 100

        embed = discord.Embed(
            title=f"📊 | إحصائيات الرانك لـ {target.name}",
            color=0x000000
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="المستوى ( Level )", value=str(level), inline=True)
        embed.add_field(name="النقاط ( XP )", value=f"{xp} / {xp_needed}", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="عرض قائمة أفضل 10 أعضاء متفاعلين في السيرفر")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild_id = str(interaction.guild.id)

        server_levels = self.data.get("server_levels", {})
        if guild_id not in server_levels or not server_levels[guild_id]:
            await interaction.followup.send("لا توجد بيانات تفاعل مسجلة حتى الآن ! ❌")
            return

        sorted_users = sorted(
            server_levels[guild_id].items(),
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

    @app_commands.command(name="set-level-channel", description="[ خاص بالإدارة ] تحديد القناة المخصصة لإرسال إشعارات صعود الفلل")
    @app_commands.describe(channel="اختر القناة المخصصة للفلل")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if "level_channels" not in self.data:
            self.data["level_channels"] = {}
        self.data["level_channels"][guild_id] = channel.id
        save_data(self.data)
        await interaction.response.send_message(f"✅ | تم تعيين قناة إشعارات التلفيل بنجاح إلى {channel.mention} !", ephemeral=True)

    @app_commands.command(name="disable-level-channel", description="[ خاص بالإدارة ] إلغاء وتعطيل قناة التلفيل المخصصة (لتظهر الرسائل بنفس روم الدردشة)")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_level_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "level_channels" in self.data and guild_id in self.data["level_channels"]:
            del self.data["level_channels"][guild_id]
            save_data(self.data)
            await interaction.response.send_message("✅ | تم إلغاء تفعيل قناة التلفيل المخصصة بنجاح. ستعود الرسائل للظهور في نفس روم الدردشة.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | لا توجد قناة تلفيل مخصصة مفعلة أساساً في هذا السيرفر!", ephemeral=True)

    @app_commands.command(name="set-level-message", description="[ خاص بالإدارة ] تعديل نص رسالة التلفيل (استخدم {member} لذكر العضو و {level} للمستوى)")
    @app_commands.describe(message="اكتب رسالة التلفيل الجديدة")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level_message(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild.id)
        if "custom_level_messages" not in self.data:
            self.data["custom_level_messages"] = {}
        self.data["custom_level_messages"][guild_id] = message
        save_data(self.data)
        await interaction.response.send_message(f"✅ | تم تحديث رسالة التلفيل بنجاح!\n📝 النص الجديد: `{message}`", ephemeral=True)

    @app_commands.command(name="set-top-channel", description="[ خاص بالإدارة ] تحديد القناة التي سيتم إرسال توبات التفاعل فيها أسبوعياً")
    @app_commands.describe(channel="اختر القناة المخصصة")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_top_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if "top_channels" not in self.data:
            self.data["top_channels"] = {}
        self.data["top_channels"][guild_id] = channel.id
        save_data(self.data)
        await interaction.response.send_message(f"✅ | تم تعيين قناة التوبات بنجاح إلى {channel.mention} !", ephemeral=True)

    @app_commands.command(name="disable-top-channel", description="[ خاص بالإدارة ] إلغاء وتعطيل إرسال التوبات الأسبوعية")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_top_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "top_channels" in self.data and guild_id in self.data["top_channels"]:
            del self.data["top_channels"][guild_id]
            save_data(self.data)
            await interaction.response.send_message("✅ | تم إلغاء تفعيل قناة وتوبات التفاعل الأسبوعية بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | لا توجد قناة توبات مفعلة أساساً في هذا السيرفر!", ephemeral=True)

    @app_commands.command(name="set-top-message", description="[ خاص بالإدارة ] تخصيص الرسالة التي ترافق إعلان التوب الأسبوعي")
    @app_commands.describe(message="اكتب نص الرسالة الجديد")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_top_message(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild.id)
        if "top_messages" not in self.data:
            self.data["top_messages"] = {}
        self.data["top_messages"][guild_id] = message
        save_data(self.data)
        await interaction.response.send_message(f"✅ | تم حفظ رسالة التوب الجديدة بنجاح !", ephemeral=True)

    @tasks.loop(hours=168)
    async def weekly_leaderboard_loop(self):
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            
            # التأكد أن السيرفر مفعل لديه التلفيل حتى يرسل التوب الأسبوعي
            leveling_status = self.data.get("leveling_status", {})
            if not leveling_status.get(guild_id, False):
                continue

            server_levels = self.data.get("server_levels", {})
            top_channels = self.data.get("top_channels", {})
            top_messages = self.data.get("top_messages", {})

            if guild_id in server_levels and server_levels[guild_id]:
                top_user_id = max(server_levels[guild_id], key=lambda uid: (server_levels[guild_id][uid]["level"], server_levels[guild_id][uid]["xp"]))
                top_member = guild.get_member(int(top_user_id))
                
                if top_member and guild_id in top_channels:
                    channel = guild.get_channel(top_channels[guild_id])
                    if channel:
                        custom_msg = top_messages.get(guild_id, "🔥 | هؤلاء هم الأبطال الأكثر تفاعلاً لهذا الأسبوع !")
                        
                        embed = discord.Embed(
                            title="👑 | التوب الأسبوعي للمتفاعلين",
                            description=f"{custom_msg}\n\n🏆 المركز الأول لهذا الأسبوع: {top_member.mention} 🎯",
                            color=0x000000
                        )
                        embed.set_thumbnail(url=top_member.display_avatar.url)
                        
                        await channel.send(embed=embed)
                
                # تصفير الرتب للأسبوع الجديد
                self.data["server_levels"][guild_id] = {}
                save_data(self.data)

    @weekly_leaderboard_loop.before_loop
    async def before_weekly_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Leveling(bot))
