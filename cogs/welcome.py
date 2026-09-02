import discord
from discord.ext import commands
import json
import os

WELCOME_FILE = "welcome_data.json"

def load_welcome_data():
    if os.path.exists(WELCOME_FILE):
        with open(WELCOME_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "welcome_channels": {},
        "welcome_messages": {},
        "welcome_images": {},
        "boost_channels": {},
        "boost_messages": {},
        "boost_images": {},
        "leave_channels": {},
        "leave_messages": {},
        "leave_images": {}
    }

def save_welcome_data(data):
    with open(WELCOME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def send_webhook_message(channel, content, embed, avatar_url, name):
    try:
        webhooks = await channel.webhooks()
        webhook = next((w for w in webhooks if w.user == channel.guild.me), None)
        if not webhook:
            webhook = await channel.create_webhook(name="Bot Automation")
        
        await webhook.send(
            content=content,
            embed=embed,
            username=name,
            avatar_url=avatar_url
        )
    except Exception:
        if embed:
            await channel.send(content=content, embed=embed)
        else:
            await channel.send(content)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_welcome_data()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = str(member.guild.id)
        channels = self.data.get("welcome_channels", {})
        if guild_id not in channels:
            return
            
        channel = member.guild.get_channel(channels[guild_id])
        if not channel:
            return

        messages = self.data.get("welcome_messages", {})
        msg_template = messages.get(guild_id, "أهلاً بك يا {member} في سيرفر {server}! منورنا 🌸")
        final_msg = msg_template.replace("{member}", member.mention).replace("{server}", member.guild.name)

        images = self.data.get("welcome_images", {})
        image_url = images.get(guild_id, None)

        embed = None
        if image_url:
            embed = discord.Embed(description=final_msg, color=0x2b2d31)
            embed.set_image(url=image_url)
            embed.set_thumbnail(url=member.display_avatar.url)
            final_msg = member.mention

        await send_webhook_message(channel, final_msg, embed, self.bot.user.display_avatar.url, "Welcome Bot")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = str(member.guild.id)
        channels = self.data.get("leave_channels", {})
        if guild_id not in channels:
            return
            
        channel = member.guild.get_channel(channels[guild_id])
        if not channel:
            return

        messages = self.data.get("leave_messages", {})
        msg_template = messages.get(guild_id, "العضو **{member}** غادر السيرفر. نراَك لاحقاً! 👋")
        final_msg = msg_template.replace("{member}", str(member)).replace("{server}", member.guild.name)

        images = self.data.get("leave_images", {})
        image_url = images.get(guild_id, None)

        embed = None
        if image_url:
            embed = discord.Embed(description=final_msg, color=0xff4747)
            embed.set_image(url=image_url)
            embed.set_thumbnail(url=member.display_avatar.url)
            final_msg = ""

        await send_webhook_message(channel, final_msg, embed, self.bot.user.display_avatar.url, "Leave Bot")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.premium_since is None and after.premium_since is not None:
            guild_id = str(after.guild.id)
            channels = self.data.get("boost_channels", {})
            if guild_id not in channels:
                return
                
            channel = after.guild.get_channel(channels[guild_id])
            if not channel:
                return

            messages = self.data.get("boost_messages", {})
            msg_template = messages.get(guild_id, "شكراً يا {member} على دعم السيرفر بـ Boost جديد! 🚀✨")
            final_msg = msg_template.replace("{member}", after.mention).replace("{server}", after.guild.name)

            images = self.data.get("boost_images", {})
            image_url = images.get(guild_id, None)

            embed = None
            if image_url:
                embed = discord.Embed(description=final_msg, color=0xf47fff)
                embed.set_image(url=image_url)
                embed.set_thumbnail(url=after.display_avatar.url)
                final_msg = after.mention

            await send_webhook_message(channel, final_msg, embed, self.bot.user.display_avatar.url, "Boost Bot")

    # --- أوامر الترحيب ---
    @app_commands.command(name="set-welcome-channel", description="[ خاص بالإدارة ] تحديد قناة الترحيب بالأعضاء الجدد")
    @app_commands.describe(channel="اختر القناة المخصصة للترحيب")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if "welcome_channels" not in self.data:
            self.data["welcome_channels"] = {}
        self.data["welcome_channels"][guild_id] = channel.id
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم تعيين قناة الترحيب بنجاح إلى {channel.mention} !", ephemeral=True)

    @app_commands.command(name="disable-welcome-channel", description="[ خاص بالإدارة ] إلغاء وتعطيل نظام الترحيب في السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_welcome_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "welcome_channels" in self.data and guild_id in self.data["welcome_channels"]:
            del self.data["welcome_channels"][guild_id]
            save_welcome_data(self.data)
            await interaction.response.send_message("✅ | تم إلغاء وتعطيل نظام الترحيب بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | نظام الترحيب غير مفعل أساساً في هذا السيرفر!", ephemeral=True)

    @app_commands.command(name="set-welcome-message", description="[ خاص بالإدارة ] تخصيص رسالة الترحيب ({member} لذكر العضو و {server} لاسم السيرفر)")
    @app_commands.describe(message="اكتب نص رسالة الترحيب الجديد")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_message(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild.id)
        if "welcome_messages" not in self.data:
            self.data["welcome_messages"] = {}
        self.data["welcome_messages"][guild_id] = message
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم تحديث رسالة الترحيب بنجاح!\n📝 النص الجديد: `{message}`", ephemeral=True)

    @app_commands.command(name="set-welcome-image", description="[ خاص بالإدارة ] تعيين رابط صورة أو بانر لرسالة الترحيب")
    @app_commands.describe(image_url="ضع رابط الصورة المباشر هنا")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_image(self, interaction: discord.Interaction, image_url: str):
        guild_id = str(interaction.guild.id)
        if "welcome_images" not in self.data:
            self.data["welcome_images"] = {}
        self.data["welcome_images"][guild_id] = image_url
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم حفظ صورة الترحيب بنجاح!", ephemeral=True)

    @app_commands.command(name="remove-welcome-image", description="[ خاص بالإدارة ] حذف صورة الترحيب وجعلها نصية عبر الويب هوك")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_welcome_image(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "welcome_images" in self.data and guild_id in self.data["welcome_images"]:
            del self.data["welcome_images"][guild_id]
            save_welcome_data(self.data)
            await interaction.response.send_message("✅ | تم حذف صورة الترحيب بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | لا توجد صورة ترحيب مضافة أساساً!", ephemeral=True)

    # --- أوامر المغادرة (Leave) ---
    @app_commands.command(name="set-leave-channel", description="[ خاص بالإدارة ] تحديد قناة رسائل مغادرة الأعضاء")
    @app_commands.describe(channel="اختر القناة المخصصة للمغادرة")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_leave_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if "leave_channels" not in self.data:
            self.data["leave_channels"] = {}
        self.data["leave_channels"][guild_id] = channel.id
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم تعيين قناة المغادرة بنجاح إلى {channel.mention} !", ephemeral=True)

    @app_commands.command(name="disable-leave-channel", description="[ خاص بالإدارة ] إلغاء وتعطيل نظام رسائل المغادرة")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_leave_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "leave_channels" in self.data and guild_id in self.data["leave_channels"]:
            del self.data["leave_channels"][guild_id]
            save_welcome_data(self.data)
            await interaction.response.send_message("✅ | تم إلغاء وتعطيل نظام المغادرة بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | نظام المغادرة غير مفعل أساساً في هذا السيرفر!", ephemeral=True)

    @app_commands.command(name="set-leave-message", description="[ خاص بالإدارة ] تخصيص رسالة المغادرة ({member} لاسم العضو و {server} لاسم السيرفر)")
    @app_commands.describe(message="اكتب نص رسالة المغادرة الجديد")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_leave_message(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild.id)
        if "leave_messages" not in self.data:
            self.data["leave_messages"] = {}
        self.data["leave_messages"][guild_id] = message
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم تحديث رسالة المغادرة بنجاح!\n📝 النص الجديد: `{message}`", ephemeral=True)

    @app_commands.command(name="set-leave-image", description="[ خاص بالإدارة ] تعيين رابط صورة أو بانر لرسالة المغادرة")
    @app_commands.describe(image_url="ضع رابط الصورة المباشر هنا")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_leave_image(self, interaction: discord.Interaction, image_url: str):
        guild_id = str(interaction.guild.id)
        if "leave_images" not in self.data:
            self.data["leave_images"] = {}
        self.data["leave_images"][guild_id] = image_url
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم حفظ صورة المغادرة بنجاح!", ephemeral=True)

    @app_commands.command(name="remove-leave-image", description="[ خاص بالإدارة ] حذف صورة المغادرة وجعلها نصية عبر الويب هوك")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_leave_image(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "leave_images" in self.data and guild_id in self.data["leave_images"]:
            del self.data["leave_images"][guild_id]
            save_welcome_data(self.data)
            await interaction.response.send_message("✅ | تم حذف صورة المغادرة بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | لا توجد صورة مغادرة مضافة أساساً!", ephemeral=True)

    # --- أوامر البوست (Nitro Boost) ---
    @app_commands.command(name="set-boost-channel", description="[ خاص بالإدارة ] تحديد قناة إرسال رسائل بوست السيرفر (Nitro Boost)")
    @app_commands.describe(channel="اختر القناة المخصصة للبوستات")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_boost_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if "boost_channels" not in self.data:
            self.data["boost_channels"] = {}
        self.data["boost_channels"][guild_id] = channel.id
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم تعيين قناة البوستات بنجاح إلى {channel.mention} !", ephemeral=True)

    @app_commands.command(name="disable-boost-channel", description="[ خاص بالإدارة ] إلغاء وتعطيل رسائل بوست السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_boost_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "boost_channels" in self.data and guild_id in self.data["boost_channels"]:
            del self.data["boost_channels"][guild_id]
            save_welcome_data(self.data)
            await interaction.response.send_message("✅ | تم إلغاء وتعطيل نظام بوستات السيرفر بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | نظام البوستات غير مفعل أساساً في هذا السيرفر!", ephemeral=True)

    @app_commands.command(name="set-boost-message", description="[ خاص بالإدارة ] تخصيص رسالة البوست ({member} لذكر الداعم و {server} لاسم السيرفر)")
    @app_commands.describe(message="اكتب نص رسالة البوست الجديد")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_boost_message(self, interaction: discord.Interaction, message: str):
        guild_id = str(interaction.guild.id)
        if "boost_messages" not in self.data:
            self.data["boost_messages"] = {}
        self.data["boost_messages"][guild_id] = message
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم تحديث رسالة البوست بنجاح!\n📝 النص الجديد: `{message}`", ephemeral=True)

    @app_commands.command(name="set-boost-image", description="[ خاص بالإدارة ] تعيين رابط صورة أو بانر لرسالة البوست")
    @app_commands.describe(image_url="ضع رابط الصورة المباشر هنا")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_boost_image(self, interaction: discord.Interaction, image_url: str):
        guild_id = str(interaction.guild.id)
        if "boost_images" not in self.data:
            self.data["boost_images"] = {}
        self.data["boost_images"][guild_id] = image_url
        save_welcome_data(self.data)
        await interaction.response.send_message(f"✅ | تم حفظ صورة البوست بنجاح!", ephemeral=True)

    @app_commands.command(name="remove-boost-image", description="[ خاص بالإدارة ] حذف صورة البوست وجعلها نصية عبر الويب هوك")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_boost_image(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if "boost_images" in self.data and guild_id in self.data["boost_images"]:
            del self.data["boost_images"][guild_id]
            save_welcome_data(self.data)
            await interaction.response.send_message("✅ | تم حذف صورة البوست بنجاح.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ | لا توجد صورة بوست مضافة أساساً!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))

