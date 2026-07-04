
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
    await bot.change_presence(activity=discord.Game(name="VALTRYX 🛡️"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # الشرط الجديد: البوت سيرد فقط إذا قام أحد بعمل منشن (Mention) له في الرسالة
    if bot.user.mentioned_in(message):
        response = (
            f"هلا وغلا بك يا {message.author.mention} في سيرفر VALTRYX! 🛡️\n"
            "نورتنا يا بطل، إذا احتجت أي مساعدة أنا في الخدمة.\n"
            "━─━─━─━─━─━─━─━─━─━\n"
            f"Welcome {message.author.mention} to VALTRYX! 🛡️\n"
            "Glad to have you here, hero! Let me know if you need anything."
        )
        await message.channel.send(response)

    await bot.process_commands(message)

token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ خطأ: لم يتم العثور على التوكن (DISCORD_TOKEN)!")
