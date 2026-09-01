import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! البوت شغال 🚀")

# قراءة التوكن من متغيرات البيئة في Railway
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("خطأ: لم يتم العثور على متغير DISCORD_TOKEN")
