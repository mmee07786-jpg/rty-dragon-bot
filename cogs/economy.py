import discord
from discord.ext import commands
import json
import os

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.balance_file = "balance.json"
        self.load_balances()

    def load_balances(self):
        if not os.path.exists(self.balance_file):
            with open(self.balance_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def get_balances(self):
        if not os.path.exists(self.balance_file):
            return {}
        with open(self.balance_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_balances(self, data):
        with open(self.balance_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # أمر الرصيد
    @commands.command(name="credit", aliases=["فلوسي", "رصيد"])
    async def credit(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        balances = self.get_balances()
        user_id = str(target.id)
        
        user_balance = balances.get(user_id, 500)
        
        embed = discord.Embed(
            title="💰 | حساب الرصيد",
            description=f"رصيد العضو {target.mention} هو: **{user_balance} كوينز** ✨",
            color=0xf1c40f
        )
        await ctx.send(embed=embed)

    # أمر الراتب اليومي
    @commands.command(name="daily", aliases=["راتب"])
    async def daily(self, ctx):
        balances = self.get_balances()
        user_id = str(ctx.author.id)
        
        current = balances.get(user_id, 500)
        reward = 200
        balances[user_id] = current + reward
        self.save_balances(balances)
        
        embed = discord.Embed(
            title="🎁 | الراتب اليومي",
            description=f"عاشت إيدك يا {ctx.author.mention}! استلمت راتبك اليومي بنجاح **+{reward} كوينز** 💵\nرصيدك الحالي: **{balances[user_id]}**",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)

    # أمر تحويل الأموال
    @commands.command(name="transfer", aliases=["تحويل"])
    async def transfer(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("❌ | لا يمكنك تحويل مبالغ سالبة أو صفرية!")
            return

        if member.id == ctx.author.id:
            await ctx.send("❌ | لا يمكنك تحويل الأموال لنفسك يا غالي!")
            return

        balances = self.get_balances()
        author_id = str(ctx.author.id)
        member_id = str(member.id)

        author_balance = balances.get(author_id, 500)

        if author_balance < amount:
            await ctx.send(f"❌ | رصيدك غير كافي! رصيدك الحالي هو: **{author_balance} كوينز** فقط.")
            return

        balances[author_id] = author_balance - amount
        balances[member_id] = balances.get(member_id, 500) + amount
        self.save_balances(balances)

        embed = discord.Embed(
            title="💸 | عملية تحويل ناجحة",
            description=f"تم تحويل **{amount} كوينز** بنجاح إلى العضو {member.mention} 🤝",
            color=0x3498db
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))

