import discord
from discord import app_commands
from discord.ext import commands

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leave_channel_id = None

    @app_commands.command(name="leave_setup", description="تعيين روم رسائل المغادرة")
    @app_commands.default_permissions(administrator=True)
    async def leave_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.leave_channel_id = channel.id
        await interaction.response.send_message(f"✅ تم ضبط روم المغادرة بنجاح: {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if self.leave_channel_id is None:
            return

        channel = self.bot.get_channel(self.leave_channel_id)
        if channel:
            embed = discord.Embed(
                title="عضو غادر السيرفر 🚪",
                description=f"مع السلامة {member.name}، ننتظر عودتك يوماً ما.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leave(bot))

