import os
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"البوت جاهز الآن ويعمل باسم: {bot.user} (ID: {bot.user.id})")
    
    # تحميل الكوجات المطلوبة فقط
    cogs_list = ["cogs.game", "cogs.economy", "cogs.mitzF18", "cogs.tickets", "cogs.leveling"]
    
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            print(f"✅ تم تحميل الملف بنجاح: {cog}")
        except Exception as e:
            print(f"❌ فشل تحميل الملف {cog}: {e}")

    # مزامنة أوامر السلاش
    try:
        synced = await bot.tree.sync()
        print(f"🔄 تمت مزامنة (Slash Commands) تمت مزامنة {len(synced)} أمر.")
    except Exception as e:
        print(f"❌ خطأ في مزامنة الأوامر: {e}")

@bot.event
async def on_command_error(ctx, error):
    # لمعرفة سبب أي خطأ أمر يحدث بالكونسول
    if isinstance(error, commands.CommandNotFound):
        return  # يتجاهل الأوامر غير الموجودة
    print(f"⚠️ خطأ في الأمر: {error}")

bot.run(os.getenv("TOKEN"))
