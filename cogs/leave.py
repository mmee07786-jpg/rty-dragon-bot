import discord
from discord import app_commands
from discord.ext import commands

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leave_channel_id = None
        self.leave_message = "مع السلامة {member}، ننتظر عودتك يوماً ما."
        self.leave_image = None

    @app_commands.command(name="leave_setup", description="تعيين روم رسائل المغادرة")
    @app_commands.default_permissions(administrator=True)
    async def leave_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.leave_channel_id = channel.id
        await interaction.response.send_message(f"✅ تم ضبط روم المغادرة بنجاح: {channel.mention}", ephemeral=True)

    @app_commands.command(name="leave_message", description="تعديل رسالة المغادرة (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def leave_message_cmd(self, interaction: discord.Interaction, message: str):
        self.leave_message = message
        await interaction.response.send_message(f"✅ تم تحديث رسالة المغادرة بنجاح!", ephemeral=True)

    @app_commands.command(name="leave_image", description="تعديل صورة المغادرة")
    @app_commands.default_permissions(administrator=True)
    async def leave_image_cmd(self, interaction: discord.Interaction, image_url: str):
        self.leave_image = image_url
        await interaction.response.send_message(f"✅ تم تحديث صورة المغادرة بنجاح!", ephemeral=True)

    @app_commands.command(name="test_leave", description="تجربة رسالة المغادرة لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_leave(self, interaction: discord.Interaction):
        formatted_msg = self.leave_message.replace("{member}", interaction.user.mention)
        embed = discord.Embed(
            title="عضو غادر السيرفر 🚪 (تجربة)",
            description=formatted_msg,
            color=discord.Color.red()
        )
        if self.leave_image:
            embed.set_image(url=self.leave_image)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if self.leave_channel_id is None:
            return
        
        # البحث الآمن عن الروم عبر الـ Cache أو الـ Fetch لمنع خطأ الـ ID
        channel = self.bot.get_channel(self.leave_channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self.leave_channel_id)
            except Exception:
                return

        if channel:
            formatted_msg = self.leave_message.replace("{member}", member.mention)
            embed = discord.Embed(
                title="عضو غادر السيرفر 🚪",
                description=formatted_msg,
                color=discord.Color.red()
            )
            if self.leave_image:
                embed.set_image(url=self.leave_image)
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(Leave(bot))
