import discord
from discord.ext import commands
from discord import app_commands
import os
import traceback

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # تحميل جميع ملفات الـ Cogs من مجلد cogs تلقائياً مع معالجة الأخطاء
        if os.path.exists("./cogs"):
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    cog_name = filename[:-3]
                    try:
                        await self.load_extension(f"cogs.{cog_name}")
                        print(f"تم تحميل الملف بنجاح: {cog_name}")
                    except Exception as e:
                        print(f"فشل تحميل الملف {cog_name}: {e}")

        # مزامنة الأوامر مع ديسكورد لتحديثها فوراً
        try:
            synced = await self.tree.sync()
            print(f"تمت مزامنة {len(synced)} أمر (Slash Commands) بنجاح.")
        except Exception as e:
            print(f"خطأ في مزامنة الأوامر: {e}")

    async def on_ready(self):
        print(f"البوت جاهز الآن ويعمل باسم: {self.user} (ID: {self.user.id})")
        print("-----------------------------------------")

    # نظام حماية عالمي لمنع البوت من الكراش إذا حدث خطأ غير متوقع بأي أمر
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print(f"خطأ تم رصده وتجاوزه لمنع الكراش: {error}")

bot = MyBot()

# معالجة أخطاء أوامر السلاش العامة لمنع توقف التطبيق
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"خطأ في أمر سلاش: {error}")
    try:
        if interaction.response.is_done():
            await interaction.followup.send("حدث خطأ بسيط أثناء تنفيذ الأمر، لكن البوت مستمر بالعمل ✅", ephemeral=True)
        else:
            await interaction.response.send_message("حدث خطأ بسيط أثناء تنفيذ الأمر، لكن البوت مستمر بالعمل ✅", ephemeral=True)
    except:
        pass

# تشغيل البوت مع التوكن الصحيح (يتأكد من قراءة متغيرات البيئة DISCORD_TOKEN)
token = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
if token:
    try:
        bot.run(token)
    except Exception as e:
        print(f"خطأ حرج في التشغيل: {e}")
else:
    print("خطأ: لم يتم العثور على التوكن في متغيرات البيئة!")
