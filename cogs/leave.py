import discord
from discord import app_commands
from discord.ext import commands
import json
import os

DATA_FILE = "leave_data.json"

def load_leave_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_leave_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_guild_leave_data(guild_id: str):
    data = load_leave_data()
    if guild_id not in data:
        data[guild_id] = {
            "channel_id": None,
            "message": "مع السلامة {member}، ننتظر عودتك يوماً ما.",
            "image_url": None
        }
    return data[guild_id]

def update_guild_leave_data(guild_id: str, guild_data):
    data = load_leave_data()
    data[guild_id] = guild_data
    save_leave_data(data)


class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leave_setup", description="تعيين روم رسائل المغادرة لهذا السيرفر")
    @app_commands.default_permissions(administrator=True)
    async def leave_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild_id)
        guild_data = get_guild_leave_data(guild_id)
        
        guild_data["channel_id"] = channel.id
        update_guild_leave_data(guild_id, guild_data)

        await interaction.response.send_message(f"✅ تم ضبط روم المغادرة بنجاح في هذا السيرفر: {channel.mention}", ephemeral=True)

    @app_commands.command(name="leave_message", description="تعديل رسالة المغادرة (استخدم {member} للمنشن)")
    @app_commands.default_permissions(administrator=True)
    async def leave_message_cmd(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild_id)
        guild_data = get_guild_leave_data(guild_id)
        
        guild_data["message"] = message
        update_guild_leave_data(guild_id, guild_data)

        await interaction.response.send_message(f"✅ تم تحديث رسالة المغادرة بنجاح!", ephemeral=True)

    @app_commands.command(name="leave_image", description="تعديل صورة المغادرة")
    @app_commands.default_permissions(administrator=True)
    async def leave_image_cmd(self, interaction: discord.Interaction, image_url: str):
        guild_id = str(interaction.guild_id)
        guild_data = get_guild_leave_data(guild_id)
        
        guild_data["image_url"] = image_url
        update_guild_leave_data(guild_id, guild_data)

        await interaction.response.send_message(f"✅ تم تحديث صورة المغادرة بنجاح!", ephemeral=True)

    @app_commands.command(name="test_leave", description="تجربة رسالة المغادرة لنفسك")
    @app_commands.default_permissions(administrator=True)
    async def test_leave(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        guild_data = get_guild_leave_data(guild_id)
        
        msg_template = guild_data.get("message", "مع السلامة {member}")
        image_url = guild_data.get("image_url", None)

        formatted_msg = msg_template.replace("{member}", interaction.user.mention)
        embed = discord.Embed(
            description=formatted_msg,
            color=discord.Color.red()
        )
        if image_url:
            embed.set_image(url=image_url)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        guild_data = get_guild_leave_data(guild_id)
        
        channel_id = guild_data.get("channel_id")
        if not channel_id:
            return
        
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                return

        if channel:
            msg_template = guild_data.get("message", "مع السلامة {member}")
            image_url = guild_data.get("image_url", None)

            formatted_msg = msg_template.replace("{member}", member.mention)
            embed = discord.Embed(
                description=formatted_msg,
                color=discord.Color.red()
            )
            if image_url:
                embed.set_image(url=image_url)
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(Leave(bot))
