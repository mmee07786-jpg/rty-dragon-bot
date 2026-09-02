import discord
from discord.ext import commands

# 1. تفعيل الصلاحيات (Intents) وقراءة محتوى الرسائل
intents = discord.Intents.default()
intents.message_content = True  # هذه هي المسؤولة عن قراءة -روليت وغيره
intents.members = True          # ضرورية عشان يشوف الأعضاء ويقدر يطرد بالروليت

# 2. تعريف البوت مع البادئة -
bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("-----------------------------------------")
    
    # تحميل ملف الألعاب (Cog) تلقائياً
    try:
        await bot.load_extension("cogs.games")
        print("تم تحميل ملف الألعاب (games.py) بنجاح! 🎮")
    except Exception as e:
        print(f"خطأ في تحميل ملف الألعاب: {e}")

    # مزامنة أوامر السلاش مثل /games
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"خطأ في مزامنة الأوامر: {e}")

# ضع التوكن الخاص بك هنا لتشغيل البوت
bot.run("YOUR_BOT_TOKEN")

