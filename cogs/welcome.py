import discord
from discord import app_commands
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = None
        self.welcome_message = "منورنا يا {member}، نتمنى لك أوقات ممتعة معنا."
        self.welcome_image = None

    @app_commands.command(name="welcome_setup", description="تعيين روم الترحيب بالأعضاء الجدد")
    @app_commands.default_permissions(administrator=True)
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.welcome_channel_id = channel.id
        await interaction.response.send_message(f"✅ تم ضبط روم الترحيب بنجاح: {channel.mention}", ephemeral=True)

    @app_commands.command(name="welcome_message", description="تعديل رسالة الترحيب (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def welcome_message_cmd(self, interaction: discord.Interaction, message: str):
        self.welcome_message = message
        await interaction.response.send_message(f"✅ تم تحديث رسالة الترحيب بنجاح!", ephemeral=True)

    @app_commands.command(name="welcome_image", description="تعديل رابط صورة الترحيب")
    @app_commands.default_permissions(administrator=True)
    async def welcome_image_cmd(self, interaction: discord.Interaction, image_url: str):
        self.welcome_image = image_url
        await interaction.response.send_message(f"✅ تم تحديث صورة الترحيب بنجاح!", ephemeral=True)

    @app_commands.command(name="test_welcome", description="تجربة رسالة الترحيب لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        formatted_msg = self.welcome_message.replace("{member}", interaction.user.mention)
        embed = discord.Embed(
            title="أهلاً بك في السيرفر! 🎉 (تجربة)",
            description=formatted_msg,
            color=discord.Color.green()
        )
        if self.welcome_image:
            embed.set_image(url=self.welcome_image)
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.welcome_channel_id is None:
            return
        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            formatted_msg = self.welcome_message.replace("{member}", member.mention)
            embed = discord.Embed(
                title="أهلاً بك في السيرفر! 🎉",
                description=formatted_msg,
                color=discord.Color.green()
            )
            if self.welcome_image:
                embed.set_image(url=self.welcome_image)
            await channel.send(content=f"{member.mention}", embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
