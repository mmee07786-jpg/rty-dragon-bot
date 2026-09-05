import discord
from discord.ext import commands
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

class AutoRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="autorole_add", description="[خاص بالإدارة] إضافة رتبة لتُعطى تلقائياً لكل عضو جديد يدخل السيرفر")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def autorole_add(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "autoroles" not in data:
            data["autoroles"] = {}
        if guild_id not in data["autoroles"]:
            data["autoroles"][guild_id] = {"roles": [], "enabled": True}

        # التأكد إذا كان الهيكل قديماً وتم تحويله
        if isinstance(data["autoroles"][guild_id], list):
            old_list = data["autoroles"][guild_id]
            data["autoroles"][guild_id] = {"roles": old_list, "enabled": True}

        if role.id in data["autoroles"][guild_id]["roles"]:
            await interaction.followup.send(f"⚠️ | الرتبة {role.mention} موجودة مسبقاً في قائمة الرتب التلقائية!", ephemeral=True)
            return

        if role >= interaction.guild.me.top_role:
            await interaction.followup.send("❌ | عذراً، رتبة البوت أدنى من هذه الرتبة أو تساواها، يجب أن تكون رتبة البوت أعلى!", ephemeral=True)
            return

        data["autoroles"][guild_id]["roles"].append(role.id)
        save_data(data)

        await interaction.followup.send(f"✅ | تم بنجاح إضافة الرتبة {role.mention} إلى قائمة الرتب التلقائية للأعضاء الجدد.")

    @discord.app_commands.command(name="autorole_remove", description="[خاص بالإدارة] إزالة رتبة من قائمة الرتب التلقائية")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def autorole_remove(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "autoroles" not in data or guild_id not in data["autoroles"]:
            await interaction.followup.send("❌ | لا توجد أي رتب تلقائية مسجلة في هذا السيرفر أساساً!", ephemeral=True)
            return

        guild_data = data["autoroles"][guild_id]
        role_list = guild_data["roles"] if isinstance(guild_data, dict) else guild_data

        if role.id in role_list:
            role_list.remove(role.id)
            save_data(data)
            await interaction.followup.send(f"🗑️ | تم إزالة الرتبة {role.mention} من قائمة الرتب التلقائية بنجاح.")
        else:
            await interaction.followup.send(f"❌ | هذه الرتبة غير موجودة في قائمة الرتب التلقائية.", ephemeral=True)

    @discord.app_commands.command(name="autorole_toggle", description="[خاص بالإدارة] تفعيل أو إلغاء تفعيل نظام الرتب التلقائية بالكامل")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def autorole_toggle(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "autoroles" not in data or guild_id not in data["autoroles"]:
            await interaction.followup.send("❌ | لم تقم بإضافة أي رتب تلقائية بعد لتفعيل/إلغاء النظام.", ephemeral=True)
            return

        guild_data = data["autoroles"][guild_id]
        if isinstance(guild_data, list):
            data["autoroles"][guild_id] = {"roles": guild_data, "enabled": True}
            guild_data = data["autoroles"][guild_id]

        current_state = guild_data.get("enabled", True)
        new_state = not current_state
        guild_data["enabled"] = new_state
        save_data(data)

        status_text = "مفعل ✅" if new_state else "معطل (ملغي) ❌"
        await interaction.followup.send(f"🛡️ | حالة نظام الرتب التلقائية أصبحت الآن: **{status_text}**")

    @discord.app_commands.command(name="autorole_list", description="[خاص بالإدارة] عرض جميع الرتب التلقائية المعينة حالياً بالسيرفر")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def autorole_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        guild_data = data.get("autoroles", {}).get(guild_id)
        if not guild_data:
            await interaction.followup.send("📋 | لا توجد أي رتب تلقائية مفعلة في هذا السيرفر حالياً.")
            return

        role_ids = guild_data["roles"] if isinstance(guild_data, dict) else guild_data
        is_enabled = guild_data.get("enabled", True) if isinstance(guild_data, dict) else True

        if not role_ids:
            await interaction.followup.send("📋 | لا توجد رتب مسجلة في القائمة حالياً.")
            return

        roles_mention = [interaction.guild.get_role(r_id).mention for r_id in role_ids if interaction.guild.get_role(r_id)]

        embed = discord.Embed(
            title="🛡️ | قائمة الرتب التلقائية",
            description=f"**حالة النظام:** `{'مفعل ✅' if is_enabled else 'معطل ❌'}`\n\n**الرتب الممنوحة عند الدخول:**\n" + "\n".join([f"• {rm}" for rm in roles_mention]),
            color=discord.Color.blurple()
        )
        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        data = load_data()

        guild_data = data.get("autoroles", {}).get(guild_id)
        if not guild_data:
            return

        is_enabled = guild_data.get("enabled", True) if isinstance(guild_data, dict) else True
        if not is_enabled:
            return

        role_ids = guild_data["roles"] if isinstance(guild_data, dict) else guild_data

        for r_id in role_ids:
            role = member.guild.get_role(r_id)
            if role:
                try:
                    await member.add_roles(role, reason="توزيع الرتب التلقائية للأعضاء الجدد")
                except Exception as e:
                    print(f"Failed to assign role {r_id}: {e}")

async def setup(bot):
    await bot.add_cog(AutoRoles(bot))

