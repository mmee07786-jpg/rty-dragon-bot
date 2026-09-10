import discord
from discord import app_commands
from discord.ext import commands
import json
import os

BOOST_DATA_FILE = "boost_data.json"

def load_boost_data():
    if os.path.exists(BOOST_DATA_FILE):
        with open(BOOST_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_boost_data(data):
    with open(BOOST_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_guild_boost(guild_id: str):
    data = load_boost_data()
    if guild_id not in data:
        data[guild_id] = {
            "channel_id": None,
            "message": "عاشت ايدك {member} على دعمك للسيرفر وعمل Boost!",
            "image_url": None
        }
    return data[guild_id]

def update_guild_boost(guild_id: str, guild_data):
    data = load_boost_data()
    data[guild_id] = guild_data
    save_boost_data(data)

class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="boost_setup", description="تعيين روم إعلانات بوست السيرفر لهذا السيرفر")
    @app_commands.default_permissions(administrator=True)
    async def boost_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_boost(guild_id)
        g_data["channel_id"] = channel.id
        update_guild_boost(guild_id, g_data)
        await interaction.response.send_message(f"✅ تم ضبط روم إعلانات البوست في هذا السيرفر: {channel.mention}", ephemeral=True)

    @app_commands.command(name="boost_message", description="تعديل رسالة البوست (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def boost_message_cmd(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_boost(guild_id)
        g_data["message"] = message
        update_guild_boost(guild_id, g_data)
        await interaction.response.send_message(f"✅ تم تحديث رسالة البوست في هذا السيرفر بنجاح!", ephemeral=True)

    @app_commands.command(name="boost_image", description="تعديل صورة البوست")
    @app_commands.default_permissions(administrator=True)
    async def boost_image_cmd(self, interaction: discord.Interaction, image_url: str):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_boost(guild_id)
        g_data["image_url"] = image_url
        update_guild_boost(guild_id, g_data)
        await interaction.response.send_message(f"✅ تم تحديث صورة البوست في هذا السيرفر بنجاح!", ephemeral=True)

    @app_commands.command(name="test_boost", description="تجربة رسالة البوست لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_boost(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_boost(guild_id)
        
        formatted_msg = g_data["message"].replace("{member}", interaction.user.mention)
        embed = discord.Embed(description=formatted_msg, color=discord.Color.purple())
        if g_data["image_url"]:
            embed.set_image(url=g_data["image_url"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild_id = str(after.guild.id)
        g_data = get_guild_boost(guild_id)
        
        if g_data["channel_id"] is None:
            return
        if before.premium_since is None and after.premium_since is not None:
            channel = self.bot.get_channel(g_data["channel_id"])
            if channel:
                formatted_msg = g_data["message"].replace("{member}", after.mention)
                embed = discord.Embed(description=formatted_msg, color=discord.Color.purple())
                if g_data["image_url"]:
                    embed.set_image(url=g_data["image_url"])
                await channel.send(content=f"{after.mention}", embed=embed)

async def setup(bot):
    await bot.add_cog(Boost(bot))
