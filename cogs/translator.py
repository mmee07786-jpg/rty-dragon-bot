import discord
from discord.ext import commands
import aiohttp
import urllib.parse

class FlagTranslator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # قائمة شاملة لربط أعلام الدول برموز اللغات
        self.flag_to_lang = {
            # الدول العربية
            "🇮🇶": "ar", "🇸🇦": "ar", "🇪🇬": "ar", "🇦🇪": "ar", "🇸🇾": "ar",
            "🇯🇴": "ar", "🇱🇧": "ar", "🇰🇼": "ar", "🇶🇦": "ar", "🇧🇭": "ar",
            "🇴🇲": "ar", "🇾🇪": "ar", "🇵🇸": "ar", "🇩🇿": "ar", "🇲🇦": "ar",
            "🇹🇳": "ar", "🇸🇩": "ar", "🇱🇾": "ar", "🇸🇴": "ar", "🇲🇷": "ar",
            
            # اللغات الأجنبية الشائعة
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

    async def translate_text(self, text: str, target_lang: str) -> str:
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={encoded_text}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # تجميع أجزاء النص المترجم بدقة كاملة
                        translated_parts = [item[0] for item in data[0] if item[0]]
                        return "".join(translated_parts)
        except Exception as e:
            print(f"⚠️ خطأ في اتصال الترجمة: {e}")
        return None

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # تجاهل تفاعل البوت نفسه
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

            # التأكد من وجود محتوى نصي بالرسالة
            if not message.content or not message.content.strip():
                return

            try:
                text_to_translate = message.content.strip()
                
                # جلب الترجمة الفورية المباشرة
                translated_text = await self.translate_text(text_to_translate, target_lang)
                
                if not translated_text:
                    return

                # جلب معلومات العضو لعمل المنشن بدقة
                member = payload.member
                if not member:
                    member = channel.guild.get_member(payload.user_id)
                
                member_mention = member.mention if member else f"<@{payload.user_id}>"
                footer_name = member.display_name if member else "عضو"
                footer_avatar = member.display_avatar.url if member and member.display_avatar else None

                # تصميم الرد
                embed = discord.Embed(
                    description=translated_text,
                    color=0x2ECC71
                )
                embed.set_author(name="الترجمة الفورية", icon_url="https://i.imgur.com/3Z4h7uK.png")
                embed.set_footer(
                    text=f"تمت الترجمة بواسطة {footer_name}",
                    icon_url=footer_avatar
                )
                
                # الرد مع منشن الشخص
                await message.reply(content=f"🌐 | ترجمة الرسالة بناءً على طلب {member_mention}:", embed=embed, mention_author=False)

            except Exception as e:
                print(f"⚠️ خطأ أثناء تنفيذ الترجمة: {e}")

async def setup(bot):
    await bot.add_cog(FlagTranslator(bot))
