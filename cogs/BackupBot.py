import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os

OWNER_ID = 1107355943408259112  # آونر البوت الأساسي
BACKUP_FILE = "server_backup.json"

class BackupBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🛡 | نظام النسخ الاحتياطي (مع الحماية القصوى ضد التكرار) جاهز للعمل.")

    def serialize_overwrites(self, guild, channel):
        overwrites_data = {}
        for target, overwrite in channel.overwrites.items():
            target_id = str(target.id)
            if isinstance(target, discord.Role):
                target_type = "role"
            elif isinstance(target, discord.Member):
                target_type = "member"
            else:
                continue
            
            allow_val, deny_val = overwrite.pair()
            overwrites_data[target_id] = {
                "name": target.name,
                "type": target_type,
                "allow": allow_val.value,
                "deny": deny_val.value
            }
        return overwrites_data

    def apply_overwrites(self, guild, channel_data):
        overwrites = {}
        role_map = {role.name.strip().lower(): role for role in guild.roles}
        
        for target_id_str, ow_data in channel_data.get("overwrites", {}).items():
            try:
                target = None
                target_type = ow_data.get("type")
                target_name = ow_data.get("name", "").strip().lower()

                if target_type == "role":
                    try:
                        target = guild.get_role(int(target_id_str))
                    except:
                        pass
                    if not target and target_name in role_map:
                        target = role_map[target_name]
                
                elif target_type == "member":
                    try:
                        target = guild.get_member(int(target_id_str))
                    except:
                        pass

                if target:
                    overwrite = discord.PermissionOverwrite.from_pair(
                        discord.Permissions(ow_data["allow"]),
                        discord.Permissions(ow_data["deny"])
                    )
                    overwrites[target] = overwrite
            except Exception as e:
                print(f"⚠️ خطأ في تطبيق صلاحيات الروم: {e}")
        return overwrites

    # 1. أمر أخذ النسخة الاحتياطية الشاملة
    @app_commands.command(
        name="backup",
        description="أخذ نسخة احتياطية مطابقة 100% وتحديثها مع إرسال إشعار للأونر."
    )
    async def backup_server(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً فهد، هذا الأمر مخصص لك حصراً!", ephemeral=True)
            return

        await interaction.response.send_message("⏳ جاري إنشاء النسخة الاحتياطية الشاملة لكافة تفاصيل السيرفر...", ephemeral=False)
        guild = interaction.guild

        try:
            if os.path.exists(BACKUP_FILE):
                os.remove(BACKUP_FILE)

            roles_data = []
            for role in reversed(guild.roles):
                if role.is_default() or role.managed:
                    continue
                roles_data.append({
                    "id": role.id,
                    "name": role.name,
                    "permissions": role.permissions.value,
                    "color": role.color.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "position": role.position
                })

            categories_data = []
            no_category_channels = []

            for channel in guild.text_channels:
                if channel.category is None:
                    no_category_channels.append({
                        "name": channel.name,
                        "type": "text",
                        "topic": channel.topic,
                        "slowmode": channel.slowmode_delay,
                        "nsfw": channel.nsfw,
                        "overwrites": self.serialize_overwrites(guild, channel)
                    })
            
            for channel in guild.voice_channels:
                if channel.category is None:
                    no_category_channels.append({
                        "name": channel.name,
                        "type": "voice",
                        "bitrate": channel.bitrate,
                        "user_limit": channel.user_limit,
                        "overwrites": self.serialize_overwrites(guild, channel)
                    })

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
                            "nsfw": channel.nsfw,
                            "overwrites": self.serialize_overwrites(guild, channel)
                        })
                    elif isinstance(channel, discord.VoiceChannel):
                        cat_channels.append({
                            "name": channel.name,
                            "type": "voice",
                            "bitrate": channel.bitrate,
                            "user_limit": channel.user_limit,
                            "overwrites": self.serialize_overwrites(guild, channel)
                        })
                
                categories_data.append({
                    "name": category.name,
                    "overwrites": self.serialize_overwrites(guild, category),
                    "channels": cat_channels
                })

            backup_dict = {
                "guild_name": guild.name,
                "roles": roles_data,
                "categories": categories_data
            }

            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump(backup_dict, f, ensure_ascii=False, indent=4)

            total_channels = sum(len(cat["channels"]) for cat in categories_data)
            server_owner = guild.owner
            owner_mention = server_owner.mention if server_owner else "الأونر"

            await interaction.edit_original_response(
                content=(
                    f"✅ **تمت عملية النسخ الاحتياطي وتحديث الملف بنجاح!** {owner_mention}\n"
                    f"- عدد الرتب المحفوظة: **{len(roles_data)}**\n"
                    f"- عدد الرومات والأقسام المحفوظة: **{total_channels}** (مع صلاحياتها بالكامل).\n\n"
                    f"**تم كملت**"
                )
            )

        except Exception as e:
            await interaction.edit_original_response(content=f"❌ حدث خطأ أثناء إنشاء النسخة: {e}")

    # 2. أمر الاستعادة مع فحص دقيق جداً لمنع التكرار (للرتب والأقسام والرومات)
    @app_commands.command(
        name="restore",
        description="استعادة السيرفر مع منع تكرار الرتب والرومات والأقسام نهائياً."
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

            # فحص الرتب الموجودة بدقة (بالحروف الصغيرة لتجنب تكرار مثل Hmm و hmm)
            existing_role_names = {role.name.strip().lower() for role in guild.roles}

            for r_data in backup_data["roles"]:
                r_name = r_data["name"].strip()
                if r_name.lower() in existing_role_names:
                    continue # تخطي إذا كانت الرتبة موجودة
                try:
                    await guild.create_role(
                        name=r_name,
                        permissions=discord.Permissions(r_data["permissions"]),
                        color=discord.Color(r_data["color"]),
                        hoist=r_data["hoist"],
                        mentionable=r_data["mentionable"],
                        reason="استعادة النسخة الاحتياطية بدون تكرار"
                    )
                    existing_role_names.add(r_name.lower()) # إضافتها للقائمة حتى لا تتكرر ضمن نفس العملية
                    await asyncio.sleep(1.2)
                except Exception as e:
                    print(f"⚠️ خطأ بإنشاء رتبة {r_name}: {e}")

            # فحص الأقسام والرومات الموجودة حالياً بالسيرفر لمنع تكرارها
            existing_categories = {cat.name.strip().lower(): cat for cat in guild.categories}
            existing_channels = {ch.name.strip().lower() for ch in guild.channels}

            for cat_data in backup_data["categories"]:
                category_obj = None
                cat_name = cat_data["name"].strip()

                if cat_name != "بدون قسم":
                    if cat_name.lower() in existing_categories:
                        category_obj = existing_categories[cat_name.lower()]
                    else:
                        try:
                            cat_overwrites = self.apply_overwrites(guild, cat_data)
                            category_obj = await guild.create_category(cat_name, overwrites=cat_overwrites)
                            existing_categories[cat_name.lower()] = category_obj
                            await asyncio.sleep(1.5)
                        except Exception as e:
                            print(f"⚠️ خطأ بإنشاء القسم {cat_name}: {e}")
                            continue

                for ch_data in cat_data["channels"]:
                    ch_name = ch_data["name"].strip()
                    if ch_name.lower() in existing_channels:
                        continue # تخطي الروم إذا كان موجوداً مسبقاً بأي مكان بالسيرفر

                    try:
                        ch_overwrites = self.apply_overwrites(guild, ch_data)
                        if ch_data["type"] == "text":
                            new_ch = await guild.create_text_channel(
                                name=ch_name,
                                category=category_obj,
                                topic=ch_data.get("topic"),
                                slowmode_delay=ch_data.get("slowmode", 0),
                                nsfw=ch_data.get("nsfw", False),
                                overwrites=ch_overwrites
                            )
                        elif ch_data["type"] == "voice":
                            new_ch = await guild.create_voice_channel(
                                name=ch_name,
                                category=category_obj,
                                bitrate=ch_data.get("bitrate", 64000),
                                user_limit=ch_data.get("user_limit", 0),
                                overwrites=ch_overwrites
                            )
                        existing_channels.add(ch_name.lower()) # إضافته للقائمة لمنع تكراره لاحقاً
                        await asyncio.sleep(1.2)
                    except Exception as e:
                        print(f"⚠️ خطأ بإنشاء الروم {ch_name}: {e}")

            await interaction.followup.send(
                f"✅ **تمت استعادة العناصر الجديدة فقط دون أي تكرار للرتب أو الرومات أو الأقسام!**\n\n"
                f"**تم كملت**",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ غير متوقع أثناء الاستعادة: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BackupBot(bot))
