import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ تم تشغيل البوت بنجاح باسم: {bot.user}")
    # تعديل حالة البوت باسم السيرفر الخاص بك
    await bot.change_presence(activity=discord.Game(name="VALTRYX 🛡️"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg_content = message.content.lower()

    # الترحيب عند ذكر اسم السيرفر أو التحية
    if any(word in msg_content for word in ["هلا", "مرحبا", "السلام عليكم", "valtryx"]):
        response = (
            "هلا وغلا بك في سيرفر VALTRYX! 🛡️\n"
            "نورتنا يا بطل، إذا احتجت أي مساعدة أنا في الخدمة.\n"
            "━─━─━─━─━─━─━─━─━─━\n"
            "Welcome to VALTRYX! 🛡️\n"
            "Glad to have you here, hero! Let me know if you need anything."
        )
        await message.channel.send(response)

    await bot.process_commands(message)

token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ خطأ: لم يتم العثور على التوكن (DISCORD_TOKEN)!")

