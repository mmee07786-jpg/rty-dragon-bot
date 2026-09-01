import discord
from discord.ext import commands, tasks
from discord import app_commands
import random

# قاموس لحفظ بيانات الأعضاء والتحكم
server_levels = {}
top_channels = {}  # {guild_id: channel_id}
top_messages = {}  # {guild_id: custom_message}

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_leaderboard_loop.start()

    def cog_unload(self):
        self.weekly_leaderboard_loop.cancel()

    # نظام حساب الـ XP والفلل عند كتابة رسالة
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        if guild_id not in server_levels:
            server_levels[guild_id] = {}
        if user_id not in server_levels[guild_id]:
            server_levels[guild_id][user_id] = {"xp": 0, "level": 1}

        xp_gain = random.randint(15, 25)
        user_data = server_levels[guild_id][user_id]
        user_data["xp"] += xp_gain

        xp_needed = user_data["level"] * 100

        if user_data["xp"] >= xp_needed:
            user_data["xp"] -= xp_needed
            user_data["level"] += 1
            new_level = user_data["level"]
            
            try:
                await message.channel.send(f"🎉 مبروك {message.author.mention}! صعدت إلى **Level {new_level}** 🚀")
            except:
                pass

    @app_commands.command(name="rank", description="معرفة لفلك الحالي ونقاط الـ XP")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        target = member or interaction.user
        guild_id = interaction.guild.id

        if guild_id not in server_levels or target.id not in server_levels[guild_id]:
            level = 1
            xp = 0
        else:
            level = server_levels[guild_id][target.id]["level"]
            xp = server_levels[guild_id][target.id]["xp"]

        xp_needed = level * 100

        embed = discord.Embed(
            title=f"📊 | إحصائيات الرانك لـ {target.name}",
            color=0x000000
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="المستوى (Level)", value=str(level), inline=True)
        embed.add_field(name="النقاط (XP)", value=f"{xp} / {xp_needed}", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="عرض أفضل 10 أعضاء متفاعلين في السيرفر")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild.id

        if guild_id not in server_levels or not server_levels[guild_id]:
            await interaction.followup.send("لا توجد بيانات تفاعل مسجلة حتى الآن! ❌")
            return

        # جلب أفضل 10 أعضاء
        sorted_users = sorted(
            server_levels[guild_id].items(),
            key=lambda item: (item[1]["level"], item[1]["xp"]),
            reverse=True
        )[:10]

        description = ""
        for index, (user_id, data) in enumerate(sorted_users, start=1):
            user = interaction.guild.get_member(user_id)
            name = user.mention if user else f"User ID: {user_id}"
            description += f"**#{index}** | {name}\n ┗ Level: **{data['level']}** | XP: **{data['xp']}**\n\n"

        embed = discord.Embed(
            title="🏆 | قائمة أفضل 10 متفاعلين في السيرفر",
            description=description,
            color=0x000000
        )
        embed.set_footer(text=f"Server: {interaction.guild.name}")

        await interaction.followup.send(embed=embed)

    # أمر لتخصيص قناة إرسال التوبات الأسبوعية
    @app_commands.command(name="settopchannel", description="تحديد القناة التي سيتم إرسال توبات التفاعل فيها أسبوعياً")
    @app_commands.describe(channel="اختر القناة المخصصة")
    @app_commands.checks.has_permissions(administrator=True)
    async def settopchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        top_channels[interaction.guild.id] = channel.id
        await interaction.response.send_message(f"✅ | تم تعيين قناة التوبات بنجاح إلى {channel.mention}!", ephemeral=True)

    # أمر لتخصيص نص رسالة التوب الأسبوعي
    @app_commands.command(name="settopmessage", description="تخصيص الرسالة التي ترافق إعلان التوب الأسبوعي")
    @app_commands.describe(message="اكتب نص الرسالة الجديد")
    @app_commands.checks.has_permissions(administrator=True)
    async def settopmessage(self, interaction: discord.Interaction, message: str):
        top_messages[interaction.guild.id] = message
        await interaction.response.send_message(f"✅ | تم حفظ رسالة التوب الجديدة بنجاح!", ephemeral=True)

    # مهام تلقائية تُنفذ كل أسبوع (168 ساعة = 7 أيام) لإرسال التوب وتصفير النقاط
    @tasks.loop(hours=168)
    async def weekly_leaderboard_loop(self, interaction=None):
        for guild in self.bot.guilds:
            guild_id = guild.id
            if guild_id in server_levels and server_levels[guild_id]:
                # البحث عن الشخص الأكثر تفاعلاً
                top_user_id = max(server_levels[guild_id], key=lambda uid: (server_levels[guild_id][uid]["level"], server_levels[guild_id][uid]["xp"]))
                top_member = guild.get_member(top_user_id)
                
                if top_member and guild_id in top_channels:
                    channel = guild.get_channel(top_channels[guild_id])
                    if channel:
                        custom_msg = top_messages.get(guild_id, "🔥 | هؤلاء هم الأبطال الأكثر تفاعلاً لهذا الأسبوع!")
                        
                        embed = discord.Embed(
                            title="👑 | التوب الأسبوعي للمتفاعلين",
                            description=f"{custom_msg}\n\n🏆 المركز الأول لهذا الأسبوع: {top_member.mention} 🎯",
                            color=0x000000
                        )
                        embed.set_thumbnail(url=top_member.display_avatar.url)
                        
                        await channel.send(embed=embed)
                
                # تصفير النقاط لبدء أسبوع جديد وعادل
                server_levels[guild_id] = {}

    @weekly_leaderboard_loop.before_loop
    async def before_weekly_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Leveling(bot))
