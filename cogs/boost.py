import discord
from discord import app_commands
from discord.ext import commands

class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boost_channel_id = None

    @app_commands.command(name="boost_setup", description="تعيين روم إعلانات بوست السيرفر")
    @app_commands.default_permissions(administrator=True)
    async def boost_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.boost_channel_id = channel.id
        await interaction.response.send_message(f"✅ تم ضبط روم إعلانات البوست بنجاح: {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if self.boost_channel_id is None:
            return

        # التحقق مما إذا قام العضو بعمل بوست للسيرفر للتو
        if before.premium_since is None and after.premium_since is not None:
            channel = self.bot.get_channel(self.boost_channel_id)
            if channel:
                embed = discord.Embed(
                    title="شكراً على البوست! 🚀",
                    description=f"عاشت ايدك {after.mention} على دعمك للسيرفر وعمل Boost!",
                    color=discord.Color.purple()
                )
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Boost(bot))

