import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class ActivityCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="activity_check", description="فحص التفاعل وتحديد أسرع الأشخاص خلال 5 ثواني")
    @app_commands.checks.has_permissions(administrator=True)
    async def activity_check(self, interaction: discord.Interaction):
        await interaction.response.send_message("Starting activity check....", ephemeral=True)
        
        embed = discord.Embed(
            title="✅ ACTIVITY CHECK",
            description="React below if you're active! (متاح لمدة 5 ثواني فقط)",
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

        # ننتظر لمدة 5 ثواني فقط لجمع التفاعلات
        try:
            while True:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=5.0, check=check)
                if user not in active_users:
                    active_users.append(user)
        except asyncio.TimeoutError:
            pass # انتهت الـ 5 ثواني بنجاح

        # تعديل الرسالة وعرض النتائج (حتى لو شخص واحد)
        complete_embed = discord.Embed(
            title="✅ ACTIVITY CHECK COMPLETE!",
            color=discord.Color.blue()
        )

        if active_users:
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
            for index, user in enumerate(active_users[:3]): # يعرض أول 3 أشخاص كحد أقصى
                leaderboard_text += f"{medals[index]} {index + 1}. {user.mention}\n"
            
            complete_embed.description = leaderboard_text
        else:
            complete_embed.description = "لم يتفاعل أي عضو خلال الـ 5 ثواني!"

        await message.edit(content=None, embed=complete_embed)

async def setup(bot):
    await bot.add_cog(ActivityCheck(bot))
