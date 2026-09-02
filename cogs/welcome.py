import discord
from discord import app_commands
from discord.ext import commands
from database import get_guild_setting, set_guild_setting

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="welcome_setup", description="تعيين روم الترحيب بالأعضاء الجدد")
    @app_commands.default_permissions(administrator=True)
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # حفظ روم الترحيب بشكل دائم في قاعدة البيانات
        set_guild_setting(interaction.guild.id, "welcome_channel_id", channel.id)
        await interaction.response.send_message(f"✅ تم ضبط روم الترحيب بنجاح: {channel.mention}", ephemeral=True)

    @app_commands.command(name="welcome_message", description="تعديل رسالة الترحيب (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def welcome_message_cmd(self, interaction: discord.Interaction, message: str):
        # حفظ رسالة الترحيب بشكل دائم
        set_guild_setting(interaction.guild.id, "welcome_message", message)
        await interaction.response.send_message(f"✅ تم تحديث رسالة الترحيب بنجاح!", ephemeral=True)

    @app_commands.command(name="welcome_image", description="تعديل رابط صورة الترحيب")
    @app_commands.default_permissions(administrator=True)
    async def welcome_image_cmd(self, interaction: discord.Interaction, image_url: str):
        # حفظ رابط الصورة بشكل دائم
        set_guild_setting(interaction.guild.id, "welcome_image", image_url)
        await interaction.response.send_message(f"✅ تم تحديث صورة الترحيب بنجاح!", ephemeral=True)

    @app_commands.command(name="test_welcome", description="تجربة رسالة الترحيب لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        # جلب الرسالة والصورة المحفوظة أو استخدام الافتراضية
        default_msg = "منورنا يا {member}، نتمنى لك أوقات ممتعة معنا."
        welcome_msg = get_guild_setting(interaction.guild.id, "welcome_message", default_msg)
        welcome_img = get_guild_setting(interaction.guild.id, "welcome_image", None)

        formatted_msg = welcome_msg.replace("{member}", interaction.user.mention)
        embed = discord.Embed(
            title="أهلاً بك في السيرفر! 🎉 (تجربة)",
            description=formatted_msg,
            color=discord.Color.green()
        )
        if welcome_img:
            embed.set_image(url=welcome_img)
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        
        # جلب الإعدادات المحفوظة بشكل دائم من ملف الـ database
        channel_id = get_guild_setting(guild_id, "welcome_channel_id")
        if channel_id is None:
            return
            
        channel = self.bot.get_channel(channel_id)
        if channel:
            default_msg = "منورنا يا {member}، نتمنى لك أوقات ممتعة معنا."
            welcome_msg = get_guild_setting(guild_id, "welcome_message", default_msg)
            welcome_img = get_guild_setting(guild_id, "welcome_image", None)

            formatted_msg = welcome_msg.replace("{member}", member.mention)
            embed = discord.Embed(
                title="أهلاً بك في السيرفر! 🎉",
                description=formatted_msg,
                color=discord.Color.green()
            )
            if welcome_img:
                embed.set_image(url=welcome_img)
            await channel.send(content=f"{member.mention}", embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
