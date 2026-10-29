import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os

CONFIG_FILE = "activity_config.json"

class ActivityCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_config(self, data):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # أمر منفصل لتحديد وحفظ الرتبة التلقائية
    @app_commands.command(
        name="set_activity_role",
        description="تحديد وحفظ الرتبة التلقائية التي سيتم منحها في فعاليات فحص التفاعل."
    )
    @app_commands.describe(role="اختر الرتبة التي تريد حفظها للفعاليات")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_activity_role(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild.id)
        config = self.load_config()
        
        config[guild_id] = role.id
        self.save_config(config)

        await interaction.response.send_message(
            f"✅ **تم حفظ رتبة الفعالية بنجاح!**\nالرتبة المعتمدة حالياً: {role.mention}",
            ephemeral=True
        )

    # أمر فحص التفاعل (يستخدم الرتبة المحفوظة تلقائياً)
    @app_commands.command(
        name="activity_check",
        description="فحص التفاعل وتحديد النشطين خلال 5 ثواني مع منحهم الرتبة المحفوظة تلقائياً."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def activity_check(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        config = self.load_config()
        role_id = config.get(guild_id)

        if not role_id:
            await interaction.response.send_message(
                "❌ عذراً، لم تقم بتحديد رتبة الفعالية بعد!\nيرجى استخدام الأمر `/set_activity_role` أولاً لاختيار الرتبة.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(
                "❌ عذراً، الرتبة المحفوظة سابقاً لم تعد موجودة في السيرفر! يرجى إعادة تحديدها بـ `/set_activity_role`.",
                ephemeral=True
            )
            return

        # التحقق من صلاحيات البوت
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ عذراً، لا أملك صلاحية (Manage Roles) لإعطاء الرتب للأعضاء!", ephemeral=True)
            return

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(f"❌ عذراً، رتبة ({role.name}) أعلى من رتبتي أو تساويها، لا يمكنني إعطاؤها للأعضاء!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="✅ ACTIVITY CHECK",
            description=f"اضغط على التفاعل أدناه لتأكيد تفاعلك والحصول على رتبة ({role.mention})!\n*(متاح لمدة 5 ثواني فقط)*",
            color=discord.Color.green()
        )
        
        message = await interaction.channel.send(content="@everyone", embed=embed)
        check_emoji = "✅"
        await message.add_reaction(check_emoji)

        active_users = []

        def check(reaction, user):
            return (
                reaction.message.id == message.id
                and str(reaction.emoji) == check_emoji
                and not user.bot
                and user not in active_users
            )

        try:
            while True:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=5.0, check=check)
                if user not in active_users:
                    active_users.append(user)
                    
                    try:
                        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(user.id)
                        if member and role not in member.roles:
                            await member.add_roles(role, reason="التفاعل السريع في فعالية Activity Check")
                    except Exception as e:
                        print(f"⚠️ لم أستطع إعطاء الرتبة لـ {user.name}: {e}")

        except asyncio.TimeoutError:
            pass

        complete_embed = discord.Embed(
            title="✅ ACTIVITY CHECK COMPLETE!",
            color=discord.Color.blue()
        )

        if active_users:
            leaderboard_text = f"🏆 **تم منح رتبة ({role.name}) لكل من:**\n\n"
            medals = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"]
            for index, user in enumerate(active_users[:10]):
                medal = medals[index] if index < len(medals) else "🔹"
                leaderboard_text += f"{medal} {index + 1}. {user.mention}\n"
            
            complete_embed.description = leaderboard_text
        else:
            complete_embed.description = "لم يتفاعل أي عضو خلال الـ 5 ثواني!"

        await message.edit(content=None, embed=complete_embed)

async def setup(bot):
    await bot.add_cog(ActivityCheck(bot))
