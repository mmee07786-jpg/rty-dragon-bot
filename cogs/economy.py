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

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="معرفة رصيدك من عملة أورا أو رصيد عضو آخر (الرصيد عام بكل السيرفرات)")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        target = member or interaction.user
        user_id = str(target.id)

        data = load_data()
        # الأرصدة أصبحت عالمية وموحدة لكل السيرفرات
        balances = data.get("balances", {})
        bal = balances.get(user_id, 0)
        
        await interaction.followup.send(f"💰 | رصيد العضو {target.mention} هو: **{bal} أورا** 🪙")

    @app_commands.command(name="give", description="[خاص بمنشئ البوت فقط] إعطاء عملة أورا لعضو معين")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        if interaction.user.id != (await self.bot.application_info()).owner.id:
            await interaction.followup.send("❌ | عذراً، هذا الأمر مخصص **لمنشئ البوت** فقط ولا يحق لأحد استخدامه!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.followup.send("❌ | يجب أن يكون المبلغ أكبر من صفر!", ephemeral=True)
            return

        user_id = str(member.id)
        data = load_data()
        
        if "balances" not in data:
            data["balances"] = {}

        current_bal = data["balances"].get(user_id, 0)
        new_bal = current_bal + amount
        data["balances"][user_id] = new_bal
        save_data(data)

        await interaction.followup.send(f"✅ | تم بنجاح إضافة **{amount} أورا** إلى رصيد العضو {member.mention}.\nرصيده الحالي العام: **{new_bal} أورا** 🪙")

    @app_commands.command(name="store_add", description="[خاص بالإدارة] إضافة سلعة جديدة لمتجر هذا السيرفر فقط مع الوصف والسعر")
    @app_commands.checks.has_permissions(administrator=True)
    async def store_add(self, interaction: discord.Interaction, item_name: str, price: int, description: str, image_url: str = None):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "shops" not in data:
            data["shops"] = {}
        if guild_id not in data["shops"]:
            data["shops"][guild_id] = []

        item = {
            "name": item_name,
            "price": price,
            "description": description,
            "image": image_url
        }

        data["shops"][guild_id].append(item)
        save_data(data)

        await interaction.followup.send(f"✅ | تم إضافة السلعة **{item_name}** بنجاح إلى متجر **هذا السيرفر فقط**!\n💵 السعر: `{price} أورا`\n📝 الوصف: `{description}`")

    @app_commands.command(name="store_remove", description="[خاص بالإدارة] حذف سلعة من متجر هذا السيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    async def store_remove(self, interaction: discord.Interaction, item_name: str):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()

        if "shops" not in data or guild_id not in data["shops"] or not data["shops"][guild_id]:
            await interaction.followup.send("❌ | متجر هذا السيرفر فارغ أساساً!", ephemeral=True)
            return

        initial_len = len(data["shops"][guild_id])
        data["shops"][guild_id] = [item for item in data["shops"][guild_id] if item["name"].lower() != item_name.lower()]
        
        if len(data["shops"][guild_id]) < initial_len:
            save_data(data)
            await interaction.followup.send(f"🗑️ | تم حذف السلعة **{item_name}** من متجر هذا السيرفر بنجاح.")
        else:
            await interaction.followup.send(f"❌ | لم يتم العثور على سلعة بهذا الاسم في متجر هذا السيرفر.", ephemeral=True)

    @app_commands.command(name="store", description="عرض سلع متجر هذا السيرفر الحالية فقط")
    async def store(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()
        
        items = data.get("shops", {}).get(guild_id, [])

        if not items:
            await interaction.followup.send("🛒 | متجر هذا السيرفر فارغ حالياً، لم يقم الإداريون بإضافة أي سلع هنا بعد.")
            return

        embed = discord.Embed(title=f"🛍️ | متجر سيرفر: {interaction.guild.name} (عملة أورا)", color=0x9b59b6, description="قائمة السلع المخصصة لهذا السيرفر فقط:")
        
        for idx, item in enumerate(items, 1):
            embed.add_field(
                name=f"{idx}. {item['name']} - 💵 {item['price']} أورا",
                value=f"📝 **الوصف:** {item['description']}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="buy", description="شراء سلعة من متجر هذا السيرفر (يخصم من رصيدك العام)")
    async def buy(self, interaction: discord.Interaction, item_name: str):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)
        data = load_data()
        
        items = data.get("shops", {}).get(guild_id, [])
        target_item = next((i for i in items if i["name"].lower() == item_name.lower()), None)
        
        if not target_item:
            await interaction.followup.send("❌ | عذراً، هذه السلعة غير موجودة في متجر هذا السيرفر. تأكد من الاسم عبر أمر `/store`", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        
        if "balances" not in data:
            data["balances"] = {}

        user_balance = data["balances"].get(user_id, 0)
        item_price = target_item["price"]

        if user_balance < item_price:
            await interaction.followup.send(f"❌ | رصيدك غير كافٍ! رصيدك العام الحالي هو `{user_balance} أورا` بينما السعر المطلوب هو `{item_price} أورا`.", ephemeral=True)
            return

        # خصم المبلغ من رصيده العام
        data["balances"][user_id] -= item_price
        save_data(data)

        remaining_balance = data["balances"][user_id]
        await interaction.followup.send(f"🎉 | مبروك يا {interaction.user.mention}! اشتريت بنجاح سلعة **{target_item['name']}** مقابل `{item_price} أورا` من متجر هذا السيرفر.\n💰 رصيدك العام المتبقي: `{remaining_balance} أورا` 🪙✨")

async def setup(bot):
    await bot.add_cog(Economy(bot))
