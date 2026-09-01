import discord
from discord.ext import commands
from discord import app_commands
import datetime

# قاموس لحفظ تحذيرات الأعضاء لكل سيرفر {guild_id: {user_id: count}}
server_warnings = {}

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="warn", description="تحذير عضو، وعند وصوله 3 تحذيرات يتم طرده تلقائياً")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        
        guild_id = interaction.guild.id
        user_id = member.id

        if guild_id not in server_warnings:
            server_warnings[guild_id] = {}
        if user_id not in server_warnings[guild_id]:
            server_warnings[guild_id][user_id] = 0

        server_warnings[guild_id][user_id] += 1
        warn_count = server_warnings[guild_id][user_id]

        # التحقق إذا وصل التحذيرات إلى 3
        if warn_count >= 3:
            try:
                await member.kick(reason=f"تخطي الحد الأقصى للتحذيرات (3 تحذيرات). آخر سبب: {reason}")
                server_warnings[guild_id][user_id] = 0 # تصفير التحذيرات بعد الطرد
                await interaction.followup.send(f"⚠️ | العضو {member.mention} وصل إلى **3 تحذيرات** وتم طرده تلقائياً من السيرفر! 👢")
            except Exception as e:
                await interaction.followup.send(f"وصل العضو 3 تحذيرات لكن فشل طرده بسبب صلاحيات البوت: `{e}`")
        else:
            await interaction.followup.send(f"⚠️ | تم تحذير العضو {member.mention} بنجاح.\nعدد تحذيراته الحالية: **{warn_count}/3**\nالسبب: {reason}")

    @app_commands.command(name="ban", description="حظر عضو من السيرفر نهائياً")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            await member.ban(reason=reason)
            await interaction.followup.send(f"تم حظر العضو {member.mention} بنجاح 🚷 (السبب: {reason})")
        except Exception as e:
            await interaction.followup.send(f"فشل الحظر: تأكد أن رتبة البوت أعلى من العضو المستهدف. ❌", ephemeral=True)

    @app_commands.command(name="kick", description="طرد عضو من السيرفر")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            await member.kick(reason=reason)
            await interaction.followup.send(f"تم طرد العضو {member.mention} بنجاح 👢 (السبب: {reason})")
        except Exception as e:
            await interaction.followup.send(f"فشل الطرد: تأكد من صلاحيات البوت. ❌", ephemeral=True)

    @app_commands.command(name="timeout", description="إسكات عضو مؤقتاً")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, time_input: str, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            time_input = time_input.lower().strip()
            minutes = 0
            if time_input.isdigit():
                minutes = int(time_input)
            elif time_input.endswith('m'):
                minutes = int(time_input[:-1])
            elif time_input.endswith('h'):
                minutes = int(time_input[:-1]) * 60
            elif time_input.endswith('d'):
                minutes = int(time_input[:-1]) * 1440
            else:
                await interaction.followup.send("صيغة الوقت غير صحيحة! استعمل m للدقائق أو h للساعات ❌", ephemeral=True)
                return

            duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
            await member.timeout(duration, reason=reason)
            await interaction.followup.send(f"تم إعطاء تايم أوت للعضو {member.mention} لمدة `{minutes} دقائق` ✅")
        except Exception as e:
            await interaction.followup.send(f"حدث خطأ: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))

