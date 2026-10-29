import discord
from discord import app_commands
from discord.ext import commands
import json
import os

WELCOME_DATA_FILE = "welcome_data.json"

def load_welcome_data():
    if os.path.exists(WELCOME_DATA_FILE):
        with open(WELCOME_DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_welcome_data(data):
    with open(WELCOME_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_guild_welcome(guild_id: str):
    data = load_welcome_data()
    if guild_id not in data:
        data[guild_id] = {
            "channel_id": None,
            "message": "منورنا يا {member}, نتمنى لك أوقات ممتعة معنا.",
            "image_url": None
        }
    return data[guild_id]

def update_guild_welcome(guild_id: str, guild_data):
    data = load_welcome_data()
    data[guild_id] = guild_data
    save_welcome_data(data)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="welcome_setup", description="تعيين روم الترحيب بالأعضاء الجدد لهذا السيرفر")
    @app_commands.default_permissions(administrator=True)
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_welcome(guild_id)
        g_data["channel_id"] = channel.id
        update_guild_welcome(guild_id, g_data)
        await interaction.response.send_message(f"✅ تم ضبط روم الترحيب بنجاح في هذا السيرفر: {channel.mention}", ephemeral=True)

    @app_commands.command(name="welcome_message", description="تعديل رسالة الترحيب (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def welcome_message_cmd(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_welcome(guild_id)
        g_data["message"] = message
        update_guild_welcome(guild_id, g_data)
        await interaction.response.send_message(f"✅ تم تحديث رسالة الترحيب في هذا السيرفر بنجاح!", ephemeral=True)

    @app_commands.command(name="welcome_image", description="تعديل رابط صورة الترحيب")
    @app_commands.default_permissions(administrator=True)
    async def welcome_image_cmd(self, interaction: discord.Interaction, image_url: str):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_welcome(guild_id)
        g_data["image_url"] = image_url
        update_guild_welcome(guild_id, g_data)
        await interaction.response.send_message(f"✅ تم تحديث صورة الترحيب في هذا السيرفر بنجاح!", ephemeral=True)

    @app_commands.command(name="test_welcome", description="تجربة رسالة الترحيب لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        g_data = get_guild_welcome(guild_id)
        
        formatted_msg = g_data["message"].replace("{member}", interaction.user.mention)
        embed = discord.Embed(description=formatted_msg, color=discord.Color.green())
        if g_data["image_url"]:
            embed.set_image(url=g_data["image_url"])
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        g_data = get_guild_welcome(guild_id)
        
        if g_data["channel_id"] is None:
            return
            
        channel = self.bot.get_channel(g_data["channel_id"])
        if channel:
            formatted_msg = g_data["message"].replace("{member}", member.mention)
            embed = discord.Embed(description=formatted_msg, color=discord.Color.green())
            if g_data["image_url"]:
                embed.set_image(url=g_data["image_url"])
            await channel.send(content=f"{member.mention}", embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
