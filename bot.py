import os
import discord
from discord.ext import commands

# 1. تفعيل كافة الصلاحيات وقراءة محتوى الرسائل (ضروري لأوامر الـ - والالعاب)
intents = discord.Intents.all()

# 2. إنشاء البوت مع البادئة -
bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user.name} (ID: {bot.user.id})")
    
    # تحميل ملف الألعاب والاقتصاد من مجلد cogs
    try:
        await bot.load_extension("cogs.games")
        print("✅ تم تحميل ملف الألعاب (games.py) بنجاح!")
    except Exception as e:
        print(f"❌ خطأ في تحميل ملف الألعاب: {e}")

    try:
        await bot.load_extension("cogs.economy")
        print("✅ تم تحميل ملف الاقتصاد (economy.py) بنجاح!")
    except Exception as e:
        print(f"❌ خطأ في تحميل ملف الاقتصاد: {e}")

    # مزامنة أوامر السلاش (مثل /daily و /games)
    try:
        synced = await bot.tree.sync()
        print(f"🔄 تمت مزامنة {len(synced)} أمر سلاش بنجاح.")
    except Exception as e:
        print(f"❌ خطأ في مزامنة الأوامر: {e}")

# 3. تشغيل البوت باستخدام التوكن السري المخزن في Railway بأمان تام
bot.run(os.getenv("TOKEN"))
