import os
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user.name} (ID: {bot.user.id})")
    
    # تحميل ملف الألعاب فقط
    try:
        await bot.load_extension("cogs.game")
        print("✅ تم تحميل ملف الألعاب (game.py) بنجاح!")
    except Exception as e:
        print(f"❌ خطأ في تحميل ملف الألعاب: {e}")

    # مزامنة أوامر السلاش
    try:
        synced = await bot.tree.sync()
        print(f"🔄 تمت مزامنة {len(synced)} أمر سلاش بنجاح.")
    except Exception as e:
        print(f"❌ خطأ في مزامنة الأوامر: {e}")

bot.run(os.getenv("TOKEN"))

