import discord
from discord import app_commands
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # هنا تقدر تحط آيدي الروم أو تخزنه بطريقتك
        self.welcome_channel_id = None

    @app_commands.command(name="welcome_setup", description="تعيين روم الترحيب بالأعضاء الجدد")
    @app_commands.default_permissions(administrator=True)
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.welcome_channel_id = channel.id
        await interaction.response.send_message(f"✅ تم ضبط روم الترحيب بنجاح: {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.welcome_channel_id is None:
            return
        
        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            # تقدر تعدل النص والـ Embed براحتك هنا
            embed = discord.Embed(
                title="أهلاً بك في السيرفر! 🎉",
                description=f"منورنا يا {member.mention}، نتمنى لك أوقات ممتعة معنا.",
                color=discord.Color.green()
            )
            # إذا تريد تضيف صورة ترحيبية:
            # embed.set_image(url="رابط_الصورة_هنا")
            await channel.send(content=f"welcome {member.mention}", embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
