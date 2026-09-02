import discord
from discord.ext import commands
import random

class MentionSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # التحقق إذا تم عمل منشن للبوت
        if self.bot.user.mentioned_in(message) and not message.mention_everyone:
            # 1. يحط تفاعل عشوائي على رسالتك
            emoji = random.choice(["🙂‍↕️", "🙂‍↔️"])
            try:
                await message.add_reaction(emoji)
            except:
                pass

            # 2. يرد عليك بالرسالة المطلوبة
            await message.reply("حبيبي هلا بيك، تريد تلعب العاب ويه الشباب؟")

async def setup(bot):
    await bot.add_cog(MentionSystem(bot))
