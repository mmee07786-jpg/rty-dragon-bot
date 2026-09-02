import discord
from discord import app_commands
from discord.ext import commands

class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boost_channel_id = None
        self.boost_message = "عاشت ايدك {member} على دعمك للسيرفر وعمل Boost!"
        self.boost_image = None

    @app_commands.command(name="boost_setup", description="تعيين روم إعلانات بوست السيرفر")
    @app_commands.default_permissions(administrator=True)
    async def boost_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.boost_channel_id = channel.id
        await interaction.response.send_message(f"✅ تم ضبط روم إعلانات البوست بنجاح: {channel.mention}", ephemeral=True)

    @app_commands.command(name="boost_message", description="تعديل رسالة البوست (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def boost_message_cmd(self, interaction: discord.Interaction, message: str):
        self.boost_message = message
        await interaction.response.send_message(f"✅ تم تحديث رسالة البوست بنجاح!", ephemeral=True)

    @app_commands.command(name="boost_image", description="تعديل صورة البوست")
    @app_commands.default_permissions(administrator=True)
    async def boost_image_cmd(self, interaction: discord.Interaction, image_url: str):
        self.boost_image = image_url
        await interaction.response.send_message(f"✅ تم تحديث صورة البوست بنجاح!", ephemeral=True)

    @app_commands.command(name="test_boost", description="تجربة رسالة البوست لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_boost(self, interaction: discord.Interaction):
        formatted_msg = self.boost_message.replace("{member}", interaction.user.mention)
        embed = discord.Embed(
            title="شكراً على البوست! 🚀 (تجربة)",
            description=formatted_msg,
            color=discord.Color.purple()
        )
        if self.boost_image:
            embed.set_image(url=self.boost_image)
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if self.boost_channel_id is None:
            return
        if before.premium_since is None and after.premium_since is not None:
            channel = self.bot.get_channel(self.boost_channel_id)
            if channel:
                formatted_msg = self.boost_message.replace("{member}", after.mention)
                embed = discord.Embed(
                    title="شكراً على البوست! 🚀",
                    description=formatted_msg,
                    color=discord.Color.purple()
                )
                if self.boost_image:
                    embed.set_image(url=self.boost_image)
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Boost(bot))
