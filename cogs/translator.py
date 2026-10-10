import discord
from discord.ext import commands
from deep_translator import GoogleTranslator

class FlagTranslator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ربط الأعلام برمجة لغة الترجمة
        self.flag_to_lang = {
            # الدول العربية
            "🇮🇶": "ar", "🇸🇦": "ar", "🇪🇬": "ar", "🇦🇪": "ar", "🇸🇾": "ar",
            "🇯🇴": "ar", "🇱🇧": "ar", "🇰🇼": "ar", "🇶🇦": "ar", "🇧🇭": "ar",
            "🇴🇲": "ar", "🇾🇪": "ar", "🇵🇸": "ar", "🇩🇿": "ar", "🇲🇦": "ar",
            "🇹🇳": "ar", "🇸🇩": "ar", "🇱🇾": "ar", "🇸🇴": "ar", "🇲🇷": "ar",
            
            # اللغات الأجنبية
            "🇺🇸": "en", "🇬🇧": "en", "🇨🇦": "en", "🇦🇺": "en",
            "🇫🇷": "fr",
            "🇪🇸": "es",
            "🇩🇪": "de",
            "🇹🇷": "tr",
            "🇮🇷": "fa",
            "🇷🇺": "ru",
            "🇮🇹": "it",
            "🇨🇳": "zh-CN",
            "🇯🇵": "ja",
            "🇰🇷": "ko",
            "🇧🇷": "pt", "🇵🇹": "pt",
            "🇮🇳": "hi",
            "🇵🇰": "ur"
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # تجاهل بوت نفسه
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
                # ترجمة فورية ودقيقة عبر deep-translator
                translated_text = GoogleTranslator(source='auto', target=target_lang).translate(message.content)
                
                if not translated_text:
                    return

                embed = discord.Embed(
                    description=f"**الترجمة:**\n{translated_text}",
                    color=0x3498DB
                )
                
                # جلب اسم وصورة العضو الذي وضع الريأكشن بشكل آمن
                member = payload.member
                if not member:
                    member = channel.guild.get_member(payload.user_id)
                
                footer_name = member.display_name if member else "عضو"
                footer_avatar = member.display_avatar.url if member and member.display_avatar else None
                
                embed.set_footer(
                    text=f"تمت الترجمة بواسطة {footer_name} عبر العلم {emoji_str}",
                    icon_url=footer_avatar
                )
                
                await message.reply(embed=embed, mention_author=False)

            except Exception as e:
                print(f"⚠️ خطأ أثناء محاولة الترجمة: {e}")

async def setup(bot):
    await bot.add_cog(FlagTranslator(bot))
