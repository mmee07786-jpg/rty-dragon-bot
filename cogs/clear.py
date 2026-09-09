import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="[ Admin Only ] حذف عدد محدد من الرسائل (من 100 إلى 1000)")
    @app_commands.describe(amount="عدد الرسائل المراد حذفها (بين 100 و 1000)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 100 or amount > 1000:
            await interaction.response.send_message("❌ | يرجى إدخال عدد يتراوح بين **100** و **1000** رسالة فقط!", ephemeral=True)
            return

        # استجابة مبدئية مخفية تمنع خطأ "التفاعل فشل" وتخلي البوت يفهم العملية بأمان
        await interaction.response.defer(ephemeral=True)
        
        # الانتظار لمدة 3 ثوانٍ لضمان استقرار البوت وتنظيم الطلب
        await asyncio.sleep(3)

        try:
            # تنفيذ عملية الحذف بالشات العام
            deleted = await interaction.channel.purge(limit=amount)
            
            # إرسال تأكيد سري مؤقت يخبرها أن العملية تمت بنجاح
            await interaction.followup.send(f"✅ | تم مسح `{len(deleted)}` رسالة بنجاح دون أي مشاكل!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء محاولة الحذف: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClearCog(bot))

