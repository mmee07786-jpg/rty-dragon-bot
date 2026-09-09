import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="[ Admin Only ] حذف عدد محدد من الرسائل (من 100 إلى 1000) على دفعات ذكية")
    @app_commands.describe(amount="عدد الرسائل المراد حذفها (بين 100 و 1000)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 100 or amount > 1000:
            await interaction.response.send_message("❌ | يرجى إدخال عدد يتراوح بين **100** و **1000** رسالة فقط!", ephemeral=True)
            return

        # استجابة مبدئية مخفية لمنع خطأ التفاعل وتأكيد بدء العملية
        await interaction.response.defer(ephemeral=True)
        
        # الانتظار لمدة 3 ثوانٍ لضمان استقرار البوت وفهمه للأمر
        await asyncio.sleep(3)

        try:
            total_deleted = 0
            # تحديد حجم الدفعة بناءً على العدد المطلوب
            chunk_size = 150 if amount >= 250 else 60

            # حلقة تكرارية لحذف الرسائل على دفعات متتالية
            while total_deleted < amount:
                remaining = amount - total_deleted
                current_limit = min(chunk_size, remaining)

                # حذف الدفعة الحالية
                deleted = await interaction.channel.purge(limit=current_limit)
                
                if not deleted:
                    break  # إذا لم تعد هناك رسائل للحذف، نوقف الحلقة

                total_deleted += len(deleted)
                
                # استراحة قصيرة ثانية واحدة بين كل دفعة وأخرى لحماية البوت من الحظر مؤقتاً (Rate Limit)
                await asyncio.sleep(1)

            # إرسال رسالة نهائية تؤكد اكتمال العملية بنجاح
            await interaction.followup.send(f"✅ | تم مسح إجمالي `{total_deleted}` رسالة بنجاح على دفعات منظمة دون أي مشاكل!", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء محاولة الحذف: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClearCog(bot))
