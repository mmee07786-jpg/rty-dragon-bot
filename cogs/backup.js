import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os

OWNER_ID = 1107355943408259112  # آونر البوت الأساسي (فهد)
BACKUP_FILE = "server_backup.json"

# --- القائمة المنسدلة لاختيار السيرفر المصدر ---
class ServerSelectView(discord.ui.View):
    def __init__(self, bot, author_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.author_id = author_id
        self.selected_guild_id = None
        
        options = []
        for guild in bot.guilds:
            name = guild.name[:97] + "..." if len(guild.name) > 100 else guild.name
            options.append(discord.SelectOption(label=name, value=str(guild.id)))
            
        if options:
            self.add_item(GuildSelect(options))

class GuildSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="اختر السيرفر المراد نسخ محتواه...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.author_id:
            await interaction.response.send_message("❌ هذه القائمة مخصصة للمالك فقط!", ephemeral=True)
            return
            
        self.view.selected_guild_id = int(self.values[0])
        self.view.stop()
        await interaction.response.defer()

# --- أزرار التأكيد (✅ و ❌) ---
class ConfirmView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value = None

    @discord.ui.button(label="موافقة", emoji="✅", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذا الأمر مخصص للمالك فقط!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="إلغاء", emoji="❌", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ هذا الأمر مخصص للمالك فقط!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()


class BackupBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🛡 | نظام النسخ الاحتياطي والأمر السري !my جاهز للعمل.")

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

    # --- الأمر الخاص بك للنسخ المباشر بين السيرفرات (!my) ---
    @commands.command(name="my")
    async def my_server_clone(self, ctx):
        if ctx.author.id != OWNER_ID:
            return

        try:
            await ctx.message.delete()
        except Exception:
            pass

        view = ServerSelectView(self.bot, ctx.author.id)
        msg = await ctx.send("🌐 | **اختر السيرفر الذي تريد نسخ الرتب والأقسام والرومات منه:**", view=view)

        await view.wait()

        if not view.selected_guild_id:
            try:
                await msg.edit(content="❌ انتهى الوقت ولم تقم باختيار أي سيرفر.", view=None)
            except Exception:
                pass
            return

        source_guild = self.bot.get_guild(view.selected_guild_id)
        if not source_guild:
            try:
                await msg.edit(content="❌ لم يتم العثور على السيرفر المحدد.", view=None)
            except Exception:
                pass
            return

        # إرسال سؤال التأكيد مع زرين ✅ و ❌
        confirm_view = ConfirmView(ctx.author.id)
        await msg.edit(
            content=f"⚠️ | **تريد تسوي لصق هنا؟** (سيرفر المصدر: **{source_guild.name}**)",
            view=confirm_view
        )

        await confirm_view.wait()

        if confirm_view.value is not True:
            try:
                await msg.edit(content="❌ تم إلغاء عملية اللصق بناءً على رغبتك.", view=None)
            except Exception:
                pass
            return

        # عند الضغط على ✅ من قبلك حصراً
        target_guild = ctx.guild
        await msg.edit(content=f"⏳ | **تم تأكيد الموافقة! جاري نقل ولصق محتويات سيرفر ({source_guild.name}) بكل هدوء وبدون أي مشاكل...**", view=None)

        try:
            # 1. نسخ ونقل الرتب
            existing_roles = {r.name.strip().lower() for r in target_guild.roles}
            for role in reversed(source_guild.roles):
                if role.is_default() or role.managed:
                    continue
                if role.name.strip().lower() in existing_roles:
                    continue
                try:
                    await target_guild.create_role(
                        name=role.name,
                        permissions=role.permissions,
                        color=role.color,
                        hoist=role.hoist,
                        mentionable=role.mentionable,
                        reason="نسخ مباشر بواسطة المالك"
                    )
                    existing_roles.add(role.name.strip().lower())
                    await asyncio.sleep(1.2)
                except Exception as e:
                    print(f"⚠️ خطأ في إنشاء رتبة: {e}")

            # 2. نسخ ونقل الأقسام والرومات
            existing_categories = {cat.name.strip().lower(): cat for cat in target_guild.categories}
            existing_channels = {ch.name.strip().lower() for ch in target_guild.channels}

            # الرومات التي بدون قسم
            for channel in source_guild.text_channels:
                if channel.category is None:
                    if channel.name.strip().lower() in existing_channels:
                        continue
                    try:
                        await target_guild.create_text_channel(
                            name=channel.name,
                            topic=channel.topic,
                            slowmode_delay=channel.slowmode_delay,
                            nsfw=channel.nsfw
                        )
                        existing_channels.add(channel.name.strip().lower())
                        await asyncio.sleep(1.2)
                    except Exception as e:
                        print(f"⚠️ خطأ بروم نصي: {e}")

            for channel in source_guild.voice_channels:
                if channel.category is None:
                    if channel.name.strip().lower() in existing_channels:
                        continue
                    try:
                        await target_guild.create_voice_channel(
                            name=channel.name,
                            bitrate=channel.bitrate,
                            user_limit=channel.user_limit
                        )
                        existing_channels.add(channel.name.strip().lower())
                        await asyncio.sleep(1.2)
                    except Exception as e:
                        print(f"⚠️ خطأ بروم صوتي: {e}")

            # الأقسام وما بداخلها من رومات
            for category in source_guild.categories:
                cat_name = category.name.strip()
                cat_obj = None
                
                if cat_name.lower() in existing_categories:
                    cat_obj = existing_categories[cat_name.lower()]
                else:
                    try:
                        cat_obj = await target_guild.create_category(cat_name)
                        existing_categories[cat_name.lower()] = cat_obj
                        await asyncio.sleep(1.5)
                    except Exception as e:
                        print(f"⚠️ خطأ بإنشاء القسم: {e}")
                        continue

                for channel in category.channels:
                    ch_name = channel.name.strip()
                    if ch_name.lower() in existing_channels:
                        continue
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await target_guild.create_text_channel(
                                name=ch_name,
                                category=cat_obj,
                                topic=channel.topic,
                                slowmode_delay=channel.slowmode_delay,
                                nsfw=channel.nsfw
                            )
                        elif isinstance(channel, discord.VoiceChannel):
                            await target_guild.create_voice_channel(
                                name=ch_name,
                                category=cat_obj,
                                bitrate=channel.bitrate,
                                user_limit=channel.user_limit
                            )
                        existing_channels.add(ch_name.lower())
                        await asyncio.sleep(1.2)
                    except Exception as e:
                        print(f"⚠️ خطأ بروم داخل القسم: {e}")

            await ctx.send(f"✅ **تمت عملية نقل ولصق كافة الرتب والأقسام والرومات بنجاح تام وبدون مشاكل!**")

        except Exception as e:
            await ctx.send(f"❌ حدث خطأ أثناء عملية اللصق: {e}")

    # 1. أمر أخذ النسخة الاحتياطية الشاملة (متاح للأدمنية)
    @app_commands.command(
        name="backup",
        description="أخذ نسخة احتياطية مطابقة 100% وتحديثها مع إرسال إشعار للأونر."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_server(self, interaction: discord.Interaction):
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

    # 2. أمر الاستعادة مع فحص دقيق جداً لمنع التكرار (متاح للأدمنية)
    @app_commands.command(
        name="restore",
        description="استعادة السيرفر مع منع تكرار الرتب والرومات والأقسام نهائياً."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def restore_server(self, interaction: discord.Interaction):
        if not os.path.exists(BACKUP_FILE):
            await interaction.response.send_message("❌ عذراً، لا توجد أي نسخة احتياطية محفوظة حالياً! يرجى عمل `/backup` أولاً.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            existing_role_names = {role.name.strip().lower() for role in guild.roles}

            for r_data in backup_data["roles"]:
                r_name = r_data["name"].strip()
                if r_name.lower() in existing_role_names:
                    continue
                try:
                    await guild.create_role(
                        name=r_name,
                        permissions=discord.Permissions(r_data["permissions"]),
                        color=discord.Color(r_data["color"]),
                        hoist=r_data["hoist"],
                        mentionable=r_data["mentionable"],
                        reason="استعادة النسخة الاحتياطية بدون تكرار"
                    )
                    existing_role_names.add(r_name.lower())
                    await asyncio.sleep(1.2)
                except Exception as e:
                    print(f"⚠️ خطأ بإنشاء رتبة {r_name}: {e}")

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
                        continue

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
                        existing_channels.add(ch_name.lower())
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

    @backup_server.error
    @restore_server.error
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ عذراً، هذا الأمر مخصص للمسؤولين (Administrator) فقط!", ephemeral=True)
            else:
                await interaction.followup.send("❌ عذراً، هذا الأمر مخصص للمسؤولين (Administrator) فقط!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BackupBot(bot))
