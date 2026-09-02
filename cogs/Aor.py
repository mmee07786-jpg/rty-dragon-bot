import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime, timedelta

user_economy = {}
daily_cooldowns = {}
server_shops = {}

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # أمر المساعدة الجديد بنظام السلاش /help-aur
    @app_commands.command(name="help-aur", description="دليل استخدام نظام عملة اور والألعاب والمتجر بالكامل")
    async def help_aur(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 | دليل استخدام نظام اور (Aur System)",
            description=(
                "أهلاً بك في نظام عملة **اور** والألعاب! إليك كافة الأوامر وطريقة استخدامها:\n\n"
                "🎁 **الأوامر اليومية (Slash Commands):**\n"
                "• `/daily` ➜ للحصول على جائزتك اليومية من 100 إلى 1000 اور (مرة كل 24 ساعة).\n"
                "• `/help-aur` ➜ لعرض هذه القائمة الإرشادية.\n\n"
                "💳 **أوامر الرصيد والمتجر (Prefix Commands):**\n"
                "• `-credit` (أو `-اور`) ➜ لمعرفة رصيدك أو رصيد غيرك.\n"
                "• `-shop` ➜ لعرض متجر السيرفر والرتب المتاحة للشراء.\n"
                "• `-buy [الرقم]` ➜ لشراء رتبة معينة من المتجر.\n"
                "• `-addshop [السعر] [@الرتبة] [الوصف]` ➜ (للأدمن) لإضافة رتبة جديدة للمتجر.\n\n"
                "🎮 **أوامر الألعاب السريعة (بدون مسافة):**\n"
                "• `-game` ➜ لعرض قائمة الألعاب الشاملة.\n"
                "• `-روليت` أو `-roulette` ➜ لعبة الروليت (تنتظر 15 ثانية، 4 لاعبين والخاسر ينطرد).\n"
                "• `-زر` أو `-reflex` ➜ لعبة الزر السريع وتغيير اللون.\n"
                "• `-لوخيروك` أو `-wouldyourather` ➜ لعبة لو خيروك.\n"
                "• `-مافيا` أو `-mafia` ➜ توزيع أدوار المافيا السريعة.\n"
                "• `-أسرع` أو `-fasttype` ➜ أسرع شخص يكتب الكلمة.\n"
                "• `-أعلام` أو `-flags` ➜ تحدي تخمين أعلام الدول.\n\n"
                "💎 **ملاحظة:** أمر الإعطاء `-give` حصري ومخصص لمطور البوت (`itzf18`) فقط!"
            ),
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="daily", description="احصل على جائزتك اليومية من عملة اور بشكل عشوائي (مرة كل 24 ساعة)")
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        now = datetime.utcnow()

        if user_id in daily_cooldowns:
            last_time = daily_cooldowns[user_id]
            if now - last_time < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_time)
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                await interaction.response.send_message(f"⏳ | يا {interaction.user.mention}, لقد استلمت جائزتك اليومية مسبقاً! انتظر **{hours} ساعة و {minutes} دقيقة**.", ephemeral=True)
                return

        daily_cooldowns[user_id] = now
        reward = random.randint(100, 1000)

        if guild_id not in user_economy:
            user_economy[guild_id] = {}
        if user_id not in user_economy[guild_id]:
            user_economy[guild_id][user_id] = 0

        user_economy[guild_id][user_id] += reward

        embed = discord.Embed(
            title="🎁 | جائزة الديلي اليومية",
            description=f"مبروك يا {interaction.user.mention}! فتحت صندوق الحظ وحصلت على **{reward} اور** 🪙",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

    @commands.command(name="credit", aliases=["نقاط", "فلوسي", "اور"])
    async def credit(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        guild_id = ctx.guild.id
        balance = user_economy.get(guild_id, {}).get(target.id, 0)
        
        embed = discord.Embed(
            title="💳 | رصيد العملة",
            description=f"العضو {target.mention} يمتلك في رصيده **{balance} اور** 🪙",
            color=0x000000
        )
        await ctx.send(embed=embed)

    @commands.command(name="give", aliases=["اعطاء"])
    async def give_currency(self, ctx, member: discord.Member, amount: int):
        if ctx.author.name.lower() != "itzf18":
            await ctx.send("❌ | عذراً، هذا الأمر مخصص حصراً لمطور وبوت `itzf18` فقط!")
            return

        if amount <= 0:
            await ctx.send("❌ | يرجى تحديد كمية أكبر من الصفر!")
            return

        guild_id = ctx.guild.id
        if guild_id not in user_economy:
            user_economy[guild_id] = {}
        if member.id not in user_economy[guild_id]:
            user_economy[guild_id][member.id] = 0

        user_economy[guild_id][member.id] += amount

        embed = discord.Embed(
            title="💎 | تحويل عملات إداري",
            description=f"تم منح {member.mention} مبلغ **{amount} اور** بنجاح! 🪙",
            color=0xffd700
        )
        await ctx.send(embed=embed)

    @commands.command(name="addshop", aliases=["اضافة_للمتجر"])
    @commands.has_permissions(administrator=True)
    async def addshop(self, ctx, price: int, role: discord.Role, *, desc: str = "رتبة مميزة"):
        guild_id = ctx.guild.id
        if guild_id not in server_shops:
            server_shops[guild_id] = {}

        item_id = len(server_shops[guild_id]) + 1
        server_shops[guild_id][item_id] = {
            "name": role.name,
            "role_id": role.id,
            "price": price,
            "desc": desc
        }

        await ctx.send(f"✅ | تم إضافة رتبة **{role.name}** بنجاح إلى متجر السيرفر برقم **{item_id}** بسعر **{price} اور**! 🛒")

    @commands.command(name="shop", aliases=["المتجر"])
    async def shop(self, ctx):
        guild_id = ctx.guild.id
        shop_items = server_shops.get(guild_id, {})

        if not shop_items:
            embed = discord.Embed(
                title=f"🛒 | متجر سيرفر {ctx.guild.name}",
                description="المتجر فارغ حالياً! يمكن لأدمن السيرفر إضافة رتب عبر الأمر:\n`-addshop [السعر] [@الرتبة] [الوصف]`",
                color=0x000000
            )
        else:
            desc_text = "أهلاً بك في متجر السيرفر! استخدم عملة **اور** للشراء عبر `-buy [رقم العنصر]`:\n\n"
            for item_id, data in shop_items.items():
                desc_text += f"**{item_id} ➜ {data['name']}**\n   ┗ السعر: **{data['price']} اور** | التفاصيل: {data['desc']}\n\n"
            
            embed = discord.Embed(title=f"🛒 | متجر سيرفر {ctx.guild.name}", description=desc_text, color=0x000000)

        await ctx.send(embed=embed)

    @commands.command(name="buy", aliases=["شراء"])
    async def buy(self, ctx, item_id: int = None):
        if not item_id:
            await ctx.send("❌ | يرجى تحديد رقم العنصر المراد شراؤه! (مثال: `-buy 1`)")
            return

        guild_id = ctx.guild.id
        shop_items = server_shops.get(guild_id, {})

        if item_id not in shop_items:
            await ctx.send("❌ | رقم العنصر غير موجود في متجر هذا السيرفر! تأكد من `-shop`")
            return

        item = shop_items[item_id]
        cost = item["price"]
        user_id = ctx.author.id
        balance = user_economy.get(guild_id, {}).get(user_id, 0)

        if balance < cost:
            await ctx.send(f"⚠️ | رصيدك غير كافي! تمتلك **{balance} اور** وتحتاج إلى **{cost} اور**.")
            return

        user_economy[guild_id][user_id] -= cost
        role = ctx.guild.get_role(item["role_id"])

        if role:
            try:
                await ctx.author.add_roles(role)
                await ctx.send(f"🎉 | مبروك يا {ctx.author.mention}! تم خصم {cost} اور وشراء رتبة **{role.name}** بنجاح! 🛍️")
            except:
                await ctx.send(f"⚠️ | تم خصم النقاط، ولكن البوت لا يملك صلاحية لإعطاء هذه الرتبة (تأكد أن رتبة البوت أعلى من الرتبة المطلوبة).")
        else:
            await ctx.send(f"✅ | تم خصم {cost} اور بنجاح! (ولكن الرتبة حُذفت من السيرفر).")

async def setup(bot):
    await bot.add_cog(Economy(bot))
