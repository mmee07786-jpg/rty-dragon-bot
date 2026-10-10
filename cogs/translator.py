import discord
from discord.ext import commands
from deep_translator import GoogleTranslator

class FlagTranslator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ربط الأعلام برمجة لغة الترجمة الشاملة
        self.flag_to_lang = {
            # الدول العربية
            "🇮🇶": "ar", "🇸🇦": "ar", "🇪🇬": "ar", "🇦🇪": "ar", "🇸🇾": "ar",
            "🇯🇴": "ar", "🇱🇧": "ar", "🇰🇼": "ar", "🇶🇦": "ar", "🇧🇭": "ar",
            "🇴🇲": "ar", "🇾🇪": "ar", "🇵🇸": "ar", "🇩🇿": "ar", "🇲🇦": "ar",
            "🇹🇳": "ar", "🇸🇩": "ar", "🇱🇾": "ar", "🇸🇴": "ar", "🇲🇷": "ar",
            
            # اللغات الأجنبية العالمية
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

            # التأكد من وجود نص بالرسالة
            if not message.content or message.content.strip() == "":
                return

            try:
                # ترجمة كاملة للنص الأصلي
                translator = GoogleTranslator(source='auto', target=target_lang)
                translated_text = translator.translate(message.content)
                
                if not translated_text:
                    return

                # جلب معلومات العضو الذي وضع الريأكشن بشكل آمن لعمل المنشن
                member = payload.member
                if not member:
                    member = channel.guild.get_member(payload.user_id)
                
                member_mention = member.mention if member else f"<@{payload.user_id}>"
                footer_name = member.display_name if member else "عضو"
                footer_avatar = member.display_avatar.url if member and member.display_avatar else None

                # تصميم الـ Embed مع تضمين منشن الشخص
                embed = discord.Embed(
                    title=f"🌐 | الترجمة إلى اللغة المطلوبة",
                    description=f"{translated_text}",
                    color=0x3498DB
                )
                
                embed.set_footer(
                    text=f"تمت الترجمة بواسطة {footer_name} عبر العلم {emoji_str}",
                    icon_url=footer_avatar
                )
                
                # إرسال الرد مع منشن صريح للشخص الذي وضع العلم
                await message.reply(content=f"📌 | الترجمة بناءً على طلب {member_mention}:", embed=embed, mention_author=False)

            except Exception as e:
                print(f"⚠️ خطأ أثناء الترجمة الكاملة مع المنشن: {e}")

async def setup(bot):
    await bot.add_cog(FlagTranslator(bot))
