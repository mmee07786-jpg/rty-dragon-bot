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

        if warn_count >= 3:
            try:
                await member.kick(reason=f"تخطي الحد الأقصى للتحذيرات (3 تحذيرات). آخر سبب: {reason}")
                server_warnings[guild_id][user_id] = 0
                await interaction.followup.send(f"⚠️ | العضو {member.mention} وصل إلى **3 تحذيرات** وتم طرده تلقائياً من السيرفر! 👢")
            except Exception as e:
                await interaction.followup.send(f"وصل العضو 3 تحذيرات لكن فشل طرده بسبب صلاحيات البوت: `{e}`")
        else:
            await interaction.followup.send(f"⚠️ | تم تحذير العضو {member.mention} بنجاح.\nعدد تحذيراته الحالية: **{warn_count}/3**\nالسبب: {reason}")

    @app_commands.command(name="clear_warnings", description="إزالة وتصفير تحذيرات العضو")
    @app_commands.checks.has_permissions(kick_members=True)
    async def clear_warnings(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()
        guild_id = interaction.guild.id
        user_id = member.id

        if guild_id in server_warnings and user_id in server_warnings[guild_id]:
            server_warnings[guild_id][user_id] = 0
            await interaction.followup.send(f"✅ | تم تصفير وإزالة جميع تحذيرات العضو {member.mention} بنجاح.")
        else:
            await interaction.followup.send(f"ℹ️ | العضو {member.mention} ليس لديه تحذيرات مسجلة أصلاً.", ephemeral=True)

    @app_commands.command(name="ban", description="حظر عضو من السيرفر نهائياً")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            await member.ban(reason=reason)
            await interaction.followup.send(f"تم حظر العضو {member.mention} بنجاح 🚷 (السبب: {reason})")
        except Exception as e:
            await interaction.followup.send(f"فشل الحظر: تأكد أن رتبة البوت أعلى من العضو المستهدف. ❌", ephemeral=True)

    @app_commands.command(name="unban", description="رفع الحظر عن عضو باستخدام الآيدي (ID)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)
            await interaction.followup.send(f"✅ | تم رفع الحظر عن العضو `{user.name}` بنجاح.")
        except Exception as e:
            await interaction.followup.send(f"❌ | فشل رفع الحظر، تأكد من صحة الآيدي (ID) أو صلاحيات البوت: `{e}`", ephemeral=True)

    @app_commands.command(name="kick", description="طرد عضو من السيرفر")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            await member.kick(reason=reason)
            await interaction.followup.send(f"تم طرد العضو {member.mention} بنجاح 👢 (السبب: {reason})")
        except Exception as e:
            await interaction.followup.send(f"فشل الطرد: تأكد من صلاحيات البوت. ❌", ephemeral=True)

    @app_commands.command(name="timeout", description="إسكات عضو مؤقتاً (تايم أوت)")
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

    @app_commands.command(name="untimeout", description="إزالة التايم أوت عن العضو")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            await member.timeout(None, reason=reason)
            await interaction.followup.send(f"✅ | تم إزالة التايم أوت عن العضو {member.mention} بنجاح.")
        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء إزالة التايم أوت: `{e}`", ephemeral=True)

    @app_commands.command(name="mute", description="كتم العضو صوتياً (Server Mute)")
    @app_commands.checks.has_permissions(mute_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            if member.voice:
                await member.edit(mute=True, reason=reason)
                await interaction.followup.send(f"🔇 | تم كتم العضو {member.mention} صوتياً بنجاح.")
            else:
                await interaction.followup.send(f"⚠️ | العضو {member.mention} ليس متصلاً بأي روم صوتي حالياً.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ | فشل كتم العضو صوتياً: `{e}`", ephemeral=True)

    @app_commands.command(name="unmute", description="إلغاء الكتم الصوتي عن العضو")
    @app_commands.checks.has_permissions(mute_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        await interaction.response.defer()
        try:
            if member.voice:
                await member.edit(mute=False, reason=reason)
                await interaction.followup.send(f"🔊 | تم رفع الكتم الصوتي عن العضو {member.mention} بنجاح.")
            else:
                await interaction.followup.send(f"⚠️ | العضو {member.mention} ليس متصلاً بأي روم صوتي حالياً.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ | فشل رفع الكتم الصوتي: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
