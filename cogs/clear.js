import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="[ Admin Only ] حذف عدد محدد من الرسائل الحديثة (من 1 إلى 1000)")
    @app_commands.describe(amount="عدد الرسائل المراد حذفها (بين 1 و 1000)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 1000:
            await interaction.response.send_message("❌ | يرجى إدخال عدد يتراوح بين **1** و **1000** رسالة فقط!", ephemeral=True)
            return

        # استجابة مخفية فورية لمنع خطأ التفاعل
        await interaction.response.defer(ephemeral=True)
        await asyncio.sleep(1)

        try:
            # حساب تاريخ قبل 14 يوم בדיוק حسب نظام ديسكورد لتجنب الخطأ 50034
            fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)

            messages = []
            # جلب الرسائل وفحص عمرها تلقائياً
            async for message in interaction.channel.history(limit=amount + 10):
                # ديسكورد يسمح بحذف الرسائل الأحدث من 14 يوم فقط جماعياً
                if message.created_at >= fourteen_days_ago:
                    messages.append(message)
                
                # إذا جمعنا العدد المطلوب نتوقف
                if len(messages) >= amount:
                    break

            if not messages:
                await interaction.followup.send("❌ | عذراً، لا توجد رسائل **حديثة (أقل من 14 يوم)** يمكن حذفها ضمن هذا العدد!", ephemeral=True)
                return

            # حذف الرسائل المقبولة دفعة واحدة (مقسمة لكتل 100 حسب قيود ديسكورد)
            for i in range(0, len(messages), 100):
                chunk = messages[i:i + 100]
                if len(chunk) > 1:
                    await interaction.channel.delete_messages(chunk)
                elif len(chunk) == 1:
                    await chunk[0].delete()
                await asyncio.sleep(0.5)

            await interaction.followup.send(f"✅ | تم مسح `{len(messages)}` رسالة حديثة بنجاح وتجاوز الرسائل القديمة تلقائياً!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء الحذف: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClearCog(bot))
