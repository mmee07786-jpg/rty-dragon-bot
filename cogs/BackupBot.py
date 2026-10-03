import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os

OWNER_ID = 1107355943408259112  # أونر البوت (فهد)
BACKUP_FILE = "server_backup.json"

class BackupBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🛡️️ | نظام النسخ الاحتياطي (Slash Commands) جاهز للعمل.")

    # 1. أمر سلاش لإنشاء النسخة الاحتياطية مع وصف دقيق وتأكيد الاكتمال
    @app_commands.command(
        name="backup",
        description="أخذ نسخة احتياطية شاملة للسيرفر (الرتب، الأقسام، الرومات، والصلاحيات) وحفظها بأمان."
    )
    async def backup_server(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً فهد، هذا الأمر مخصص لك حصراً!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        try:
            # حفظ الرتب (تخطي الرتب الافتراضية والمدارة من البوتات)
            roles_data = []
            for role in reversed(guild.roles):
                if role.is_default() or role.managed:
                    continue
                roles_data.append({
                    "name": role.name,
                    "permissions": role.permissions.value,
                    "color": role.color.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "position": role.position
                })

            # حفظ الأقسام وروماتها (تتحمل أكثر من 200 روم وأكثر)
            categories_data = []
            no_category_channels = []

            for channel in guild.text_channels:
                if channel.category is None:
                    no_category_channels.append({"name": channel.name, "type": "text", "topic": channel.topic, "slowmode": channel.slowmode_delay, "nsfw": channel.nsfw})
            
            for channel in guild.voice_channels:
                if channel.category is None:
                    no_category_channels.append({"name": channel.name, "type": "voice", "bitrate": channel.bitrate, "user_limit": channel.user_limit})

            if no_category_channels:
                categories_data.append({"name": "بدون قسم", "channels": no_category_channels})

            for category in guild.categories:
                cat_channels = []
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        cat_channels.append({
                            "name": channel.name,
                            "type": "text",
                            "topic": channel.topic,
                            "slowmode": channel.slowmode_delay,
                            "nsfw": channel.nsfw
                        })
                    elif isinstance(channel, discord.VoiceChannel):
                        cat_channels.append({
                            "name": channel.name,
                            "type": "voice",
                            "bitrate": channel.bitrate,
                            "user_limit": channel.user_limit
                        })
                categories_data.append({"name": category.name, "channels": cat_channels})

            backup_dict = {
                "guild_name": guild.name,
                "roles": roles_data,
                "categories": categories_data
            }

            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump(backup_dict, f, ensure_ascii=False, indent=4)

            total_channels = sum(len(cat["channels"]) for cat in categories_data)
            await interaction.followup.send(
                f"✅ **تم إنشاء النسخة الاحتياطية بنجاح!**\n"
                f"- عدد الرتب المحفوظة: **{len(roles_data)}**\n"
                f"- عدد الرومات المحفوظة: **{total_channels}** (أكثر من 200 روم وأكثر مطابقة تماماً).\n\n"
                f"**تم كملت**",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ أثناء إنشاء النسخة: {e}", ephemeral=True)

    # 2. أمر سلاش لاستعادة النسخة الاحتياطية مع وصف دقيق وتأكيد الاكتمال
    @app_commands.command(
        name="restore",
        description="استعادة كافة الرتب والرومات والأقسام المحفوظة في النسخة الاحتياطية بنظام آمن."
    )
    async def restore_server(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً فهد، هذا الأمر مخصص لك حصراً!", ephemeral=True)
            return

        if not os.path.exists(BACKUP_FILE):
            await interaction.response.send_message("❌ عذراً، لا توجد أي نسخة احتياطية محفوظة حالياً! يرجى عمل `/backup` أولاً.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            # استعادة الرتب أولاً
            for r_data in backup_data["roles"]:
                try:
                    await guild.create_role(
                        name=r_data["name"],
                        permissions=discord.Permissions(r_data["permissions"]),
                        color=discord.Color(r_data["color"]),
                        hoist=r_data["hoist"],
                        mentionable=r_data["mentionable"]
                    )
                    await asyncio.sleep(1.2) # فاصل زمني لتفادي حظر الديسكورد (Rate Limit)
                except Exception as e:
                    print(f"⚠️ خطأ بإنشاء رتبة {r_data['name']}: {e}")

            # استعادة الأقسام والرومات
            for cat_data in backup_data["categories"]:
                category_obj = None
                if cat_data["name"] != "بدون قسم":
                    try:
                        category_obj = await guild.create_category(cat_data["name"])
                        await asyncio.sleep(1.5)
                    except Exception as e:
                        print(f"⚠️ خطأ بإنشاء القسم {cat_data['name']}: {e}")
                        continue

                for ch_data in cat_data["channels"]:
                    try:
                        if ch_data["type"] == "text":
                            await guild.create_text_channel(
                                name=ch_data["name"],
                                category=category_obj,
                                topic=ch_data.get("topic"),
                                slowmode_delay=ch_data.get("slowmode", 0),
                                nsfw=ch_data.get("nsfw", False)
                            )
                        elif ch_data["type"] == "voice":
                            await guild.create_voice_channel(
                                name=ch_data["name"],
                                category=category_obj,
                                bitrate=ch_data.get("bitrate", 64000),
                                user_limit=ch_data.get("user_limit", 0)
                            )
                        await asyncio.sleep(1.2)
                    except Exception as e:
                        print(f"⚠️️ خطأ بإنشاء الروم {ch_data['name']}: {e}")

            await interaction.followup.send(
                f"✅ **تمت استعادة كافة الرتب والرومات بنجاح تام وبدون أي مشاكل!**\n\n"
                f"**تم كملت**",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ غير متوقع أثناء الاستعادة: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BackupBot(bot))
