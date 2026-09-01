import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime, timedelta

# قاموس لتخزين النقاط وتوقيت الديلي
user_economy = {}
daily_cooldowns = {}

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. أمر الديلي بنظام السلاش (/daily) - حظ عشوائي من 100 إلى 1000 كل 24 ساعة
    @app_commands.command(name="daily", description="احصل على جائزتك اليومية من عملة اور بشكل عشوائي (مرة كل 24 ساعة)")
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        now = datetime.utcnow()

        # التحقق من وقت الاستخدام الأخير
        if user_id in daily_cooldowns:
            last_time = daily_cooldowns[user_id]
            if now - last_time < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_time)
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                await interaction.response.send_message(f"⏳ | يا {interaction.user.mention}, لقد استلمت جائزتك اليومية مسبقاً! يمكنك استخدام الأمر مرة أخرى بعد **{hours} ساعة و {minutes} دقيقة**.", ephemeral=True)
                return

        # تحديث وقت الديلي ومنح حظ عشوائي حقيقي بين 100 و 1000
        daily_cooldowns[user_id] = now
        reward = random.randint(100, 1000)

        if guild_id not in user_economy:
            user_economy[guild_id] = {}
        if user_id not in user_economy[guild_id]:
            user_economy[guild_id][user_id] = 0

        user_economy[guild_id][user_id] += reward

        embed = discord.Embed(
            title="🎁 | جائزة الديلي اليومية",
            description=f"مبروك يا {interaction.user.mention}! فتحت صندوق الحظ اليومي وحصلت على **{reward} اور** 🪙",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

    # 2. أمر الرصيد (-credit أو -points)
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

    # 3. أمر إعطاء العملات الحصري لمالك البوت (itzf18) فقط
    @commands.command(name="give", aliases=["اعطاء"])
    async def give_currency(self, ctx, member: discord.Member, amount: int):
        # التحقق الحصري من يوزرك بالديسكورد
        if ctx.author.name.lower() != "itzf18":
            await ctx.send("❌ | عذراً، هذا الأمر مخصص حصراً لمطور ومالك البوت (`itzf18`) فقط!")
            return

        if amount <= 0:
            await ctx.send("❌ | يرجى تحديد كمية صحيحة أكبر من الصفر!")
            return

        guild_id = ctx.guild.id
        if guild_id not in user_economy:
            user_economy[guild_id] = {}
        if member.id not in user_economy[guild_id]:
            user_economy[guild_id][member.id] = 0

        user_economy[guild_id][member.id] += amount

        embed = discord.Embed(
            title="💎 | تحويل عملات إداري (حصري للمطور)",
            description=f"قام مطور البوت `{ctx.author.name}` بمنح {member.mention} مبلغ **{amount} اور** بنجاح! 🪙",
            color=0xffd700
        )
        await ctx.send(embed=embed)

    # 4. عرض متجر السيرفر (-shop)
    @commands.command(name="shop", aliases=["المتجر"])
    async def shop(self, ctx):
        embed = discord.Embed(
            title="🛒 | متجر سيرفر itzF18",
            description=(
                "أهلاً بك في متجر السيرفر! استخدم عملة **اور** للشراء:\n\n"
                "1️⃣ **رتبة أسطورة السيرفر** (لون مميز)\n"
                "   ┗ السعر: **500 اور** | الأمر: `-buy 1`\n\n"
                "2️⃣ **رتبة VIP** (صلاحيات خاصة)\n"
                "   ┗ السعر: **1000 اور** | الأمر: `-buy 2`\n\n"
                "*(اكتب `-buy` مع رقم العنصر للشراء)*"
            ),
            color=0x000000
        )
        await ctx.send(embed=embed)

    # 5. شراء العناصر من المتجر (-buy)
    @commands.command(name="buy", aliases=["شراء"])
    async def buy(self, ctx, item_id: int = None):
        if not item_id:
            await ctx.send("❌ | يرجى تحديد رقم العنصر الذي تريد شراءه من المتجر! (مثال: `-buy 1`)")
            return

        guild_id = ctx.guild.id
        user_id = ctx.author.id
        balance = user_economy.get(guild_id, {}).get(user_id, 0)

        prices = {1: 500, 2: 1000}
        roles_names = {1: "أساطير السيرفر", 2: "VIP"}

        if item_id not in prices:
            await ctx.send("❌ | رقم العنصر غير موجود في المتجر! تأكد من `-shop`")
            return

        cost = prices[item_id]

        if balance < cost:
            await ctx.send(f"⚠️ | رصيد غير كافي! تمتلك **{balance} اور** فقط، وتحتاج إلى **{cost} اور**.")
            return

        user_economy[guild_id][user_id] -= cost
        role_name = roles_names[item_id]
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role:
            try:
                await ctx.author.add_roles(role)
                await ctx.send(f"🎉 | مبروك يا {ctx.author.mention}! تم خصم {cost} اور وشراء رتبة **{role_name}** بنجاح! 🛍️")
            except:
                await ctx.send(f"⚠️ | تم خصم النقاط، ولكن البوت لا يملك صلاحية إعطاء رتبة `{role_name}` (تأكد من ترتيب رتبة البوت).")
        else:
            await ctx.send(f"✅ | تم خصم {cost} اور بنجاح! (ملاحظة: الرتبة `{role_name}` غير متواجدة بالسيرفر حالياً).")

async def setup(bot):
    await bot.add_cog(Economy(bot))
