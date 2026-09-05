import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class ModActionView(discord.ui.View):
    def __init__(self, member: discord.Member, offending_text: str):
        super().__init__(timeout=None)
        self.member = member
        self.offending_text = offending_text

    @discord.ui.button(label="⚠️ تحذير", style=discord.ButtonStyle.secondary)
    async def warn_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"✅ | تم إعطاء تحذير رسمي للعضو {self.member.mention} بواسطة {interaction.user.mention}.", ephemeral=False)
        self.disable_buttons()
        await interaction.message.edit(view=self)

    @discord.ui.button(label="👢 طرد", style=discord.ButtonStyle.danger)
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.kick(reason=f"استخدام كلمات ممنوعة متكررة: {self.offending_text}")
            await interaction.response.send_message(f"👢 | تم طرد العضو {self.member.mention} بنجاح بواسطة {interaction.user.mention}.", ephemeral=False)
        except:
            await interaction.response.send_message("❌ | لا أملك صلاحية طرد هذا العضو!", ephemeral=True)
        self.disable_buttons()
        await interaction.message.edit(view=self)

    @discord.ui.button(label="⏳ ميوت 30 دقيقة", style=discord.ButtonStyle.primary)
    async def mute_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        import datetime
        try:
            duration = discord.utils.utcnow() + datetime.timedelta(minutes=30)
            await self.member.timeout(duration, reason=f"استخدام كلمات ممنوعة متكررة: {self.offending_text}")
            await interaction.response.send_message(f"⏳ | تم إعطاء ميوت (Timeout) لمدة 30 دقيقة للعضو {self.member.mention} بواسطة {interaction.user.mention}.", ephemeral=False)
        except:
            await interaction.response.send_message("❌ | لا أملك صلاحية عمل ميوت لهذا العضو!", ephemeral=True)
        self.disable_buttons()
        await interaction.message.edit(view=self)

    def disable_buttons(self):
        for child in self.children:
            child.disabled = True

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # لتخزين عدد المخالفات المؤقتة للجلسة الحالية لكل عضو (User ID -> Count)
        self.warnings_count = {}

    @app_commands.command(name="set_mod_channel", description="[خاص بالإدارة] تعيين روم تنبيهات المخالفات والكلمات الممنوعة")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_mod_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "automod" not in data:
            data["automod"] = {}
        if guild_id not in data["automod"]:
            data["automod"][guild_id] = {"words": [], "channel_id": None, "enabled": True}

        data["automod"][guild_id]["channel_id"] = channel.id
        save_data(data)

        await interaction.followup.send(f"✅ | تم بنجاح تعيين روم الإدارة للتنبيهات إلى: {channel.mention}")

    @app_commands.command(name="automod_toggle", description="[خاص بالإدارة] تفعيل أو إلغاء تفعيل حماية الكلمات الممنوعة بالسيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def automod_toggle(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "automod" not in data or guild_id not in data["automod"]:
            await interaction.followup.send("❌ | نظام الحماية غير معدّ بعد في هذا السيرفر. استخدم أوامر الكلمات أولاً.", ephemeral=True)
            return

        current_state = data["automod"][guild_id].get("enabled", True)
        new_state = not current_state
        data["automod"][guild_id]["enabled"] = new_state
        save_data(data)

        status_text = "مفعل ✅" if new_state else "معطل (ملغي) ❌"
        await interaction.followup.send(f"🛡️ | حالة نظام الحماية التلقائية الآن أصبحت: **{status_text}**")

    @app_commands.command(name="add_badword", description="[خاص بالإدارة] إضافة كلمة ممنوعة لقائمة الحظر بالسيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_badword(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "automod" not in data:
            data["automod"] = {}
        if guild_id not in data["automod"]:
            data["automod"][guild_id] = {"words": [], "channel_id": None, "enabled": True}

        clean_word = word.lower()
        if clean_word in data["automod"][guild_id]["words"]:
            await interaction.followup.send(f"⚠️ | الكلمة **`{word}`** موجودة مسبقاً في قائمة الكلمات الممنوعة!", ephemeral=True)
            return

        data["automod"][guild_id]["words"].append(clean_word)
        save_data(data)

        await interaction.followup.send(f"✅ | تمت إضافة الكلمة **`{word}`** إلى قائمة الحظر بنجاح.")

    @app_commands.command(name="remove_badword", description="[خاص بالإدارة] إزالة كلمة من قائمة الكلمات الممنوعة")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_badword(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "automod" not in data or guild_id not in data["automod"] or not data["automod"][guild_id]["words"]:
            await interaction.followup.send("❌ | لا توجد كلمات ممنوعة مسجلة في هذا السيرفر أساساً!", ephemeral=True)
            return

        clean_word = word.lower()
        if clean_word in data["automod"][guild_id]["words"]:
            data["automod"][guild_id]["words"].remove(clean_word)
            save_data(data)
            await interaction.followup.send(f"🗑️ | تم إزالة الكلمة **`{word}`** من قائمة الحظر بنجاح.")
        else:
            await interaction.followup.send(f"❌ | الكلمة **`{word}`** غير موجودة في قائمة الحظر.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if message.author.guild_permissions.administrator:
            return

        guild_id = str(message.guild.id)
        data = load_data()
        
        automod_data = data.get("automod", {}).get(guild_id, {})
        
        # التحقق هل النظام مفعل أصلاً؟
        if not automod_data.get("enabled", True):
            return

        bad_words = automod_data.get("words", [])
        mod_channel_id = automod_data.get("channel_id")

        if not bad_words:
            return

        content_lower = message.content.lower()
        triggered_word = next((w for w in bad_words if w in content_lower), None)

        if triggered_word:
            try:
                await message.delete()
            except:
                pass

            user_key = f"{guild_id}-{message.author.id}"
            self.warnings_count[user_key] = self.warnings_count.get(user_key, 0) + 1
            current_strikes = self.warnings_count[user_key]

            # أول مرتين: منش مباشر وتنبيه شخصي بالروم نفسه
            if current_strikes < 3:
                warning_msg = await message.channel.send(
                    f"⚠️ | {message.author.mention} احذر! لقد استخدمت كلمة ممنوعة (تنبيه رقم {current_strikes}/2)."
                )
                # حذف تنبيه البوت بعد 5 ثواني حتى لا يملي الروم
                import asyncio
                await asyncio.sleep(5)
                try:
                    await warning_msg.delete()
                except:
                    pass
                return

            # المرة الثالثة: إعادة تعيين العداد وإرسال التقرير الكامل لروم الإدارة مع الأزرار
            self.warnings_count[user_key] = 0

            if mod_channel_id:
                mod_channel = message.guild.get_channel(mod_channel_id)
                if mod_channel:
                    embed = discord.Embed(
                        title="🚨 تنبيه تكرار مخالفة الكلمات الممنوعة (المرة الثالثة)!",
                        description=(
                            f"• **العضو المخالف:** {message.author.mention} (`{message.author.id}`)\n"
                            f"• **الروم:** {message.channel.mention}\n"
                            f"• **الكلمة الممنوعة المستخدمة:** `{triggered_word}`\n\n"
                            f"💬 **آخر رسالة نصية تسببت بالمخالفة:**\n> {message.content}"
                        ),
                        color=discord.Color.red()
                    )
                    embed.set_footer(text="تجاوز الحد المسموح للتنبيهات! اختر العقوبة المناسبة أدناه 👇")

                    view = ModActionView(message.author, message.content)
                    await mod_channel.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))

