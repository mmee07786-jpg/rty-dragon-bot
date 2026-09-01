import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # تحميل جميع ملفات الـ Cogs من مجلد cogs تلقائياً
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

bot = MyBot()

# تشغيل البوت عبر التوكن الخاص بك
bot.run(os.getenv("TOKEN"))
