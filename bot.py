import os
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت جاهز الان ويعمل باسم {bot.user} (ID: {bot.user.id})")
    
    # تحميل الملفات مباشرة من المجلد الرئيسي
    cogs_list = ["admin", "economy", "leveling", "mitzf18", "tickets", "welcome"]
    
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            print(f"✅ تم تحميل الملف بنجاح ({cog})")
        except Exception as e:
            print(f"❌ فشل تحميل الملف ({cog}) : {e}")

    # مزامنة عامة (Global) لتظهر الأوامر للكل في كل السيرفرات
    try:
        synced = await bot.tree.sync()
        print(f"✅ تمت مزامنة (Slash Commands) العامة لـ {len(synced)} أمر")
    except Exception as e:
        print(f"❌ خطأ في مزامنة الأوامر: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"⚠️ خطأ في الأمر: {error}")

bot.run(os.getenv("TOKEN"))
