import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class ActivityCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="activity_check", description="بدء فحص التفاعل وتحديد أسرع ثلاثة أعضاء تفاعلوا مع البوت")
    @app_commands.checks.has_permissions(administrator=True)
    async def activity_check(self, interaction: discord.Interaction):
        # إرسال رسالة البداية
        await interaction.response.send_message("Starting activity check....", ephemeral=True)
        
        # رسالة التفاعل الرسمية مع منشن everyone
        embed = discord.Embed(
            title="✅ ACTIVITY CHECK",
            description="React below if you're active!",
            color=discord.Color.green()
        )
        
        message = await interaction.channel.send(content="@everyone", embed=embed)
        
        # إضافة تفاعل علامة الصح تلقائياً
        check_emoji = "✅"
        await message.add_reaction(check_emoji)

        # ننتظر تفاعل الأعضاء (مثلاً خلال 30 ثانية أو دقيقة حسب رغبتك)
        # لتتبع أسرع الأشخاص، نراقب وقت إضافة الرياكشن
        active_users = []

        def check(reaction, user):
            return (
                reaction.message.id == message.id
                and str(reaction.emoji) == check_emoji
                and not user.bot
                and user not in active_users
            )

        # جمع أسرع 3 أشخاص يضغطون على التفاعل
        while len(active_users) < 3:
            try:
                # مهلة زمنية للتفاعل (مثلا دقيقة كاملة)
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                active_users.append(user)
            except asyncio.TimeoutError:
                break # إذا خلص الوقت وما ضغطوا غيرهم نتوقف

        # تعديل الرسالة وإعلان اكتمال الفحص مع القائمة
        complete_embed = discord.Embed(
            title="✅ ACTIVITY CHECK COMPLETE!",
            color=discord.Color.blue()
        )

        if active_users:
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉"]
            for index, user in enumerate(active_users):
                leaderboard_text += f"{medals[index]} {index + 1}. {user.mention}\n"
            
            complete_embed.description = leaderboard_text
        else:
            complete_embed.description = "لم يتفاعل أي عضو للأسف!"

        await message.edit(content=None, embed=complete_embed)

async def setup(bot):
    await bot.add_cog(ActivityCheck(bot))

