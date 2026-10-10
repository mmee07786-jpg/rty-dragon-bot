import discord
from discord.ext import commands
from googletrans import Translator

class FlagTranslator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()
        
        # قائمة الأعلام واللغات
        self.flag_to_lang = {
            # الدول العربية
            "🇮🇶": "ar", "🇸🇦": "ar", "🇪🇬": "ar", "🇦🇪": "ar", "🇸🇾": "ar",
            "🇯🇴": "ar", "🇱🇧": "ar", "🇰🇼": "ar", "🇶🇦": "ar", "🇧🇭": "ar",
            "🇴🇲": "ar", "🇾🇪": "ar", "🇵🇸": "ar", "🇩🇿": "ar", "🇲🇦": "ar",
            "🇹🇳": "ar", "🇸🇩": "ar", "🇱🇾": "ar", "🇸🇴": "ar", "🇲🇷": "ar",
            
            # اللغات الأجنبية
            "🇺🇸": "en", "🇬🇧": "en", "🇨🇦": "en", "🇦🇺": "en", # الإنجليزية
            "🇫🇷": "fr", # الفرنسية
            "🇪🇸": "es", # الإسبانية
            "🇩🇪": "de", # الألمانية
            "🇹🇷": "tr", # التركية
            "🇮🇷": "fa", # الفارسية
            "🇷🇺": "ru", # الروسية
            "🇮🇹": "it", # الإيطالية
            "🇨🇳": "zh-cn", # الصينية
            "🇯🇵": "ja", # اليابانية
            "🇰🇷": "ko", # الكورية
            "🇧🇷": "pt", "🇵🇹": "pt", # البرتغالية
            "🇮🇳": "hi", # الهندية
            "🇵🇰": "ur"  # الأوردو
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # تجنب تفاعل البوت مع نفسه
        if payload.user_id == self.bot.user.id:
            return

        emoji_str = str(payload.emoji)

        if emoji_str in self.flag_to_lang:
            target_lang = self.flag_to_lang[emoji_str]
            
            channel = self.bot.get_channel(payload.channel_id)
            if not channel:
                return
                
            try:
                message = await channel.fetch_message(payload.message_id)
            except Exception:
                return

            if not message.content:
                return

            try:
                translated = self.translator.translate(message.content, dest=target_lang)
                
                embed = discord.Embed(
                    description=f"**الترجمة:**\n{translated.text}",
                    color=0x3498DB
                )
                embed.set_footer(
                    text=f"تمت الترجمة بواسطة {payload.member.display_name if payload.member else 'عضو'} عبر العلم {emoji_str}",
                    icon_url=payload.member.display_avatar.url if payload.member else None
                )
                
                await message.reply(embed=embed, mention_author=False)

            except Exception as e:
                print(f"⚠️ خطأ أثناء الترجمة: {e}")

# دالة تحميل الـ Cog بالبوت الرئيسي
async def setup(bot):
    await bot.add_cog(FlagTranslator(bot))
