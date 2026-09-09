import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="[ Admin Only ] حذف عدد محدد من الرسائل دفعة واحدة (من 100 إلى 1000)")
    @app_commands.describe(amount="عدد الرسائل المراد حذفها (بين 100 و 1000)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 100 or amount > 1000:
            await interaction.response.send_message("❌ | يرجى إدخال عدد يتراوح بين **100** و **1000** رسالة فقط!", ephemeral=True)
            return

        # استجابة مخفية فورية حتى يضل البوت فاهم الأمر وما يصير بيه تصفير
        await interaction.response.defer(ephemeral=True)
        
        # انتظار بسيط جداً لتهيئة العملية
        await asyncio.sleep(2)

        try:
            # جلب الرسائل المطلوبة دفعة واحدة وحذفها مباشرة
            messages = []
            async for message in interaction.channel.history(limit=amount):
                messages.append(message)

            if messages:
                # ديسكورد يسمح بحذف حتى 100 رسالة بالطلب الواحد للـ bulk_delete، لذا نقسمها لطلبات سريعة جداً ورا بعض بدون توقف ملحوظ
                for i in range(0, len(messages), 100):
                    chunk = messages[i:i + 100]
                    await interaction.channel.delete_messages(chunk)

            await interaction.followup.send(f"✅ | تم حذف `{len(messages)}` رسالة بنجاح دفعة واحدة!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء الحذف: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClearCog(bot))
