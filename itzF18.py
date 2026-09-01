import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class SimpleBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("تم مزامنة أوامر الـ Slash بنجاح!")

bot = SimpleBot()

@bot.event
async def on_ready():
    print(f"✅ البوت متصل الآن بنجاح باسم: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="itzF18 Bot is Online! 🚀"))

@bot.tree.command(name="itzf18", description="أمر تجريبي للتأكد من عمل البوت")
async def slash_itzf18(interaction: discord.Interaction):
    await interaction.response.send_message("أهلاً بك! البوت يعمل بكفاءة عالية وبدون أي مشاكل 🔥")

# تشغيل البوت باستخدام التوكن من المتغيرات البيئية
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ خطأ: لم يتم العثور على التوكن في متغيرات البيئة!")

