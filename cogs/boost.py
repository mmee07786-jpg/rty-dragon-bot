import discord
from discord import app_commands
from discord.ext import commands
from database import get_guild_setting, set_guild_setting

class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="boost_setup", description="تعيين روم إعلانات بوست السيرفر")
    @app_commands.default_permissions(administrator=True)
    async def boost_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # حفظ روم البوست بشكل دائم في قاعدة البيانات السحابية
        set_guild_setting(interaction.guild.id, "boost_channel_id", channel.id)
        await interaction.response.send_message(f"✅ تم ضبط روم إعلانات البوست بنجاح: {channel.mention}", ephemeral=True)

    @app_commands.command(name="boost_message", description="تعديل رسالة البوست (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def boost_message_cmd(self, interaction: discord.Interaction, message: str):
        # حفظ رسالة البوست بشكل دائم
        set_guild_setting(interaction.guild.id, "boost_message", message)
        await interaction.response.send_message(f"✅ تم تحديث رسالة البوست بنجاح!", ephemeral=True)

    @app_commands.command(name="boost_image", description="تعديل صورة البوست")
    @app_commands.default_permissions(administrator=True)
    async def boost_image_cmd(self, interaction: discord.Interaction, image_url: str):
        # حفظ صورة البوست بشكل دائم
        set_guild_setting(interaction.guild.id, "boost_image", image_url)
        await interaction.response.send_message(f"✅ تم تحديث صورة البوست بنجاح!", ephemeral=True)

    @app_commands.command(name="test_boost", description="تجربة رسالة البوست لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_boost(self, interaction: discord.Interaction):
        default_msg = "عاشت ايدك {member} على دعمك للسيرفر وعمل Boost!"
        boost_msg = get_guild_setting(interaction.guild.id, "boost_message", default_msg)
        boost_img = get_guild_setting(interaction.guild.id, "boost_image", None)

        formatted_msg = boost_msg.replace("{member}", interaction.user.mention)
        embed = discord.Embed(
            title="شكراً على البوست! 🚀 (تجربة)",
            description=formatted_msg,
            color=discord.Color.purple()
        )
        if boost_img:
            embed.set_image(url=boost_img)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild_id = member_guild_id = after.guild.id
        
        # جلب روم البوست من قاعدة البيانات السحابية
        channel_id = get_guild_setting(guild_id, "boost_channel_id")
        if channel_id is None:
            return
            
        if before.premium_since is None and after.premium_since is not None:
            channel = self.bot.get_channel(channel_id)
            if channel:
                default_msg = "عاشت ايدك {member} على دعمك للسيرفر وعمل Boost!"
                boost_msg = get_guild_setting(guild_id, "boost_message", default_msg)
                boost_img = get_guild_setting(guild_id, "boost_image", None)

                formatted_msg = boost_msg.replace("{member}", after.mention)
                embed = discord.Embed(
                    title="شكراً على البوست! 🚀",
                    description=formatted_msg,
                    color=discord.Color.purple()
                )
                if boost_img:
                    embed.set_image(url=boost_img)
                await channel.send(content=f"{after.mention}", embed=embed)

async def setup(bot):
    await bot.add_cog(Boost(bot))
