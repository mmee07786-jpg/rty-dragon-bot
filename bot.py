import os
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت جاهز الان ويعمل باسم {bot.user} (ID: {bot.user.id})")
    
    # قائمة بجميع ملفات الموديولات (Cogs) النشطة في مستودعك
    cogs_list = [
        "cogs.admin", 
        "cogs.economy", 
        "cogs.leveling", 
        "cogs.tickets", 
        "cogs.welcome", 
        "cogs.boost", 
        "cogs.leave",
        "cogs.raid_end",
        "cogs.activity_check",
        "cogs.automod",
        "cogs.autoroles",
        "cogs.join_message",
        "cogs.roblox"
    ]
    
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            print(f"✅ تم تحميل الملف بنجاح ({cog})")
        except Exception as e:
            print(f"❌ فشل تحميل الملف ({cog}) : {e}")

    # مزامنة أوامر السلاش (Slash Commands) العامة
    try:
        synced = await bot.tree.sync()
        print(f"✅ تمت مزامنة (Slash Commands) لـ {len(synced)} أمر")
    except Exception as e:
        print(f"❌ خطأ في مزامنة الأوامر: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"⚠️ خطأ في الأمر: {error}")

# تشغيل البوت باستخدام توكن الحماية الموجود في متغيرات البيئة
bot.run(os.getenv("TOKEN"))
