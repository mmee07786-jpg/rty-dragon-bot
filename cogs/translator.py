import discord
from discord.ext import commands
from deep_translator import GoogleTranslator

class FlagTranslator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # قائمة الأعلام ولغات الترجمة
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

    # دالة لتقسيم النص الطويل جداً إلى أجزاء لا تتجاوز حجماً معيناً
    def split_text(self, text: str, max_length: int = 3000):
        chunks = []
        while len(text) > max_length:
            # البحث عن آخر سطر أو مسافة لعدم كسر الكلمات
            split_idx = text.rfind('\n', 0, max_length)
            if split_idx == -1:
                split_idx = text.rfind(' ', 0, max_length)
            if split_idx == -1:
                split_idx = max_length
                
            chunks.append(text[:split_idx])
            text = text[split_idx:].lstrip()
        if text:
            chunks.append(text)
        return chunks

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

            # التأكد من وجود محتوى
            if not message.content or not message.content.strip():
                return

            try:
                raw_text = message.content.strip()

                # معالجة للكلمات والحروف القليلة جداً
                if len(raw_text) <= 3 and target_lang == "ar":
                    quick_dict = {
                        "hi": "مرحباً", "hello": "أهلاً", "hey": "هلا",
                        "ok": "تمام", "yes": "نعم", "no": "لا",
                        "hmmm": "همم", "hmm": "همم", "oh": "أوه", "ah": "آه",
                        "lol": "هههه", "rip": "الله يرحمه"
                    }
                    translated_text = quick_dict.get(raw_text.lower(), None)
                    if not translated_text:
                        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(raw_text)
                    translated_chunks = [translated_text]
                else:
                    # تقسيم النص إلى أجزاء لترجمته إذا كان طويلاً جداً (أكثر من 200 سطر)
                    raw_chunks = self.split_text(raw_text, max_length=2000)
                    translated_chunks = []
                    
                    translator = GoogleTranslator(source='auto', target=target_lang)
                    for chunk in raw_chunks:
                        res = translator.translate(chunk)
                        if res:
                            translated_chunks.append(res)

                if not translated_chunks:
                    return

                # جلب العضو صاحب الريأكشن للمنشن
                member = payload.member
                if not member:
                    member = channel.guild.get_member(payload.user_id)
                
                member_mention = member.mention if member else f"<@{payload.user_id}>"
                footer_name = member.display_name if member else "عضو"
                footer_avatar = member.display_avatar.url if member and member.display_avatar else None

                # إرسال الجزء الأول مع المنشن كـ Reply
                first_embed = discord.Embed(
                    description=translated_chunks[0],
                    color=0x2ECC71
                )
                first_embed.set_author(name="الترجمة الفورية", icon_url="https://i.imgur.com/3Z4h7uK.png")
                first_embed.set_footer(text=f"تمت الترجمة بواسطة {footer_name} (1/{len(translated_chunks)})", icon_url=footer_avatar)

                await message.reply(content=f"🌐 | الترجمة بناءً على طلب {member_mention}:", embed=first_embed, mention_author=False)

                # إرسال باقي الأجزاء إذا كان النص أطول من حد الرسالة الواحدة
                for idx, chunk in enumerate(translated_chunks[1:], start=2):
                    next_embed = discord.Embed(
                        description=chunk,
                        color=0x2ECC71
                    )
                    next_embed.set_footer(text=f"تمت الترجمة بواسطة {footer_name} ({idx}/{len(translated_chunks)})", icon_url=footer_avatar)
                    await channel.send(embed=next_embed)

            except Exception as e:
                print(f"⚠️ خطأ أثناء ترجمة النص الطويل: {e}")

async def setup(bot):
    await bot.add_cog(FlagTranslator(bot))
