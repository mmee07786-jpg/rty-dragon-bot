import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "economy_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"balances": {}, "shop_items": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    @app_commands.command(name="balance", description="معرفة رصيدك من عملة أورا أو رصيد عضو آخر")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        target = member or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(target.id)

        if guild_id not in self.data["balances"]:
            self.data["balances"][guild_id] = {}
        
        bal = self.data["balances"][guild_id].get(user_id, 0)
        await interaction.followup.send(f"💰 | رصيد العضو {target.mention} هو: **{bal} أورا** 🪙")

    @app_commands.command(name="give", description="[خاص بمنشئ البوت فقط] إعطاء عملة أورا لعضو معين")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await interaction.response.defer(ephemeral=True)

        # التحقق مما إذا كان المستخدم هو صاحب البوت (منشئ البوت)
        if interaction.user.id != (await self.bot.application_info()).owner.id:
            await interaction.followup.send("❌ | عذراً، هذا الأمر مخصص **لمنشئ البوت** فقط ولا يحق لأحد استخدامه!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.followup.send("❌ | يجب أن يكون المبلغ أكبر من صفر!", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id not in self.data["balances"]:
            self.data["balances"][guild_id] = {}

        current_bal = self.data["balances"][guild_id].get(user_id, 0)
        self.data["balances"][guild_id][user_id] = current_bal + amount
        save_data(self.data)

        await interaction.followup.send(f"✅ | تم بنجاح إضافة **{amount} أورا** إلى رصيد العضو {member.mention}.\nرصيده الحالي: **{self.data['balances'][guild_id][user_id]} أورا** 🪙")

    @app_commands.command(name="store_add", description="[خاص بالإدارة] إضافة سلعة جديدة للمتجر مع تحديد الوصف والسعر")
    @app_commands.checks.has_permissions(administrator=True)
    async def store_add(self, interaction: discord.Interaction, item_name: str, price: int, description: str, image_url: str = None):
        await interaction.response.defer()
        guild_id = str(interaction.guild.id)

        item = {
            "name": item_name,
            "price": price,
            "description": description,
            "image": image_url,
            "guild_id": guild_id
        }

        if "shop_items" not in self.data:
            self.data["shop_items"] = []

        self.data["shop_items"].append(item)
        save_data(self.data)

        await interaction.followup.send(f"✅ | تم إضافة السلعة **{item_name}** بنجاح إلى المتجر!\n💵 السعر: `{price} أورا`\n📝 الوصف: `{description}`")

    @app_commands.command(name="store_remove", description="[خاص بالإدارة] حذف سلعة من المتجر")
    @app_commands.checks.has_permissions(administrator=True)
    async def store_remove(self, interaction: discord.Interaction, item_name: str):
        await interaction.response.defer()
        if "shop_items" not in self.data:
            await interaction.followup.send("❌ | المتجر فارغ أساساً!", ephemeral=True)
            return

        initial_len = len(self.data["shop_items"])
        self.data["shop_items"] = [item for item in self.data["shop_items"] if item["name"] != item_name]
        
        if len(self.data["shop_items"]) < initial_len:
            save_data(self.data)
            await interaction.followup.send(f"🗑️ | تم حذف السلعة **{item_name}** من المتجر بنجاح.")
        else:
            await interaction.followup.send(f"❌ | لم يتم العثور على سلعة بهذا الاسم في المتجر.", ephemeral=True)

    @app_commands.command(name="store", description="عرض جميع سلع المتجر المتاحة للشراء")
    async def store(self, interaction: discord.Interaction):
        await interaction.response.defer()
        items = self.data.get("shop_items", [])

        if not items:
            await interaction.followup.send("🛒 | المتجر فارغ حالياً، لم يقم الإداريون بإضافة أي سلع بعد.")
            return

        embed = discord.Embed(title="🛍️ | متجر السيرفر (عملة أورا)", color=0x9b59b6, description="قائمة السلع المتاحة للشراء حالياً:")
        
        for idx, item in enumerate(items, 1):
            embed.add_field(
                name=f"{idx}. {item['name']} - 💵 {item['price']} أورا",
                value=f"📝 **الوصف:** {item['description']}",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="buy", description="شراء سلعة من المتجر")
    async def buy(self, interaction: discord.Interaction, item_name: str):
        await interaction.response.defer()
        items = self.data.get("shop_items", [])
        
        target_item = next((i for i in items if i["name"].lower() == item_name.lower()), None)
        if not target_item:
            await interaction.followup.send("❌ | عذراً، هذه السلعة غير موجودة في المتجر. تأكد من الاسم عبر أمر `/store`", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        if guild_id not in self.data["balances"]:
            self.data["balances"][guild_id] = {}

        user_balance = self.data["balances"][guild_id].get(user_id, 0)
        item_price = target_item["price"]

        if user_balance < item_price:
            await interaction.followup.send(f"❌ | رصيدك غير كافٍ! رصيدك الحالي هو `{user_balance} أورا` بينما السعر المطلوب هو `{item_price} أورا`.", ephemeral=True)
            return

        self.data["balances"][guild_id][user_id] -= item_price
        save_data(self.data)

        await interaction.followup.send(f"🎉 | مبروك يا {interaction.user.mention}! اشتريت بنجاح سلعة **{target_item['name']}** مقابل `{item_price} أورا` 🛒✨")

async def setup(bot):
    await bot.add_cog(Economy(bot))
