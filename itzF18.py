import os
import asyncio
import datetime
import aiohttp
import discord
from discord.ext import commands, tasks
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

user_xp = {}
weekly_activity = {}

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        self.weekly_leaderboard_loop.start()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user}")
    print("البوت يعمل بكفاءة وجاهز للأوامر! 🚀")
    await bot.change_presence(activity=discord.Game(name="I see you"))

@bot.event
async def on_guild_join(guild):
    try:
        owner = guild.owner or await guild.fetch_owner()
        if owner:
            embed = discord.Embed(
                title="✨ | هلا بيك نورت السيرفر",
                description=(
                    f"يا هلا فيك! شكراً لإضافتك بوت `itzF18` إلى سيرفرك **{guild.name}**.\n\n"
                    "بوت حماية وإدارة وسيرفرات متكامل مع نظام تبرعات وتلفيل وتوبات أسبوعية تلقائية 🛡️🔥\n"
                ),
                color=0x000000
            )
            embed.set_footer(text="itzF18 Bot • 24/7 Online")
            await owner.send(embed=embed)
    except Exception as e:
        print(f"خطأ في إرسال رسالة الترحيب: {e}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    guild_id = message.guild.id
    user_id = message.author.id

    if guild_id not in user_xp:
        user_xp[guild_id] = {}
    if user_id not in user_xp[guild_id]:
        user_xp[guild_id][user_id] = 0
    user_xp[guild_id][user_id] += 10

    if guild_id not in weekly_activity:
        weekly_activity[guild_id] = {}
    if user_id not in weekly_activity[guild_id]:
        weekly_activity[guild_id][user_id] = 0
    weekly_activity[guild_id][user_id] += 1

    await bot.process_commands(message)

server_webhooks = {}

@bot.tree.command(name="setwebhook", description="تعيين ويب هوك لتوب التفاعل الأسبوعي")
@app_commands.describe(channel="القناة", url="رابط الويب هوك")
@app_commands.checks.has_permissions(administrator=True)
async def set_webhook(interaction: discord.Interaction, channel: discord.TextChannel, url: str):
    server_webhooks[interaction.guild.id] = url
    await interaction.response.send_message(f"✅ | تم حفظ رابط الويب هوك بنجاح للقناة {channel.mention}!", ephemeral=True)

@bot.tree.command(name="itzf18", description="معلومات عن البوت")
async def slash_itzf18(interaction: discord.Interaction):
    await interaction.response.send_message("ترا ادري بيك تجرب، ليش ما عندك معرفه بالبوتات؟")

@tasks.loop(hours=168)
async def weekly_leaderboard_loop():
    for guild in bot.guilds:
        guild_id = guild.id
        if guild_id in weekly_activity and weekly_activity[guild_id]:
            top_user_id = max(weekly_activity[guild_id], key=weekly_activity[guild_id].get)
            top_member = guild.get_member(top_user_id)
            
            if top_member and guild_id in server_webhooks:
                webhook_url = server_webhooks[guild_id]
                message_content = f"الف مبروك {top_member.mention} انت الاكثر تفاعل بالسيرفر 💥🔥💯"
                payload = {"content": message_content}
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(webhook_url, json=payload) as resp:
                            pass
                except Exception as e:
                    print(f"خطأ في إرسال الويب هوك: {e}")
            weekly_activity[guild_id] = {}

@weekly_leaderboard_loop.before_loop
async def before_weekly_loop():
    await bot.wait_until_ready()

class TicketButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تذكرة 🎫", style=discord.ButtonStyle.secondary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"لديك تذكرة مفتوحة بالفعل هنا: {existing_channel.mention} ❌", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{member.name}",
            overwrites=overwrites,
            topic=f"تذكرة دعم فني خاصة بالعضو: {member.name}"
        )

        embed = discord.Embed(
            title="🎫 | تذكرة دعم فني جديدة",
            description=f"مرحباً بك {member.mention}!\nتم فتح هذه التذكرة الخاصة لك بنجاح.\nيرجى كتابة مشكلتك أو طلبك بالتفصيل.",
            color=0x000000
        )
        await ticket_channel.send(content=f"{member.mention}", embed=embed, view=CloseTicketButtonView())
        await interaction.response.send_message(f"تم فتح تذكرتك بنجاح: {ticket_channel.mention} ✅", ephemeral=True)

class CloseTicketButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إغلاق التكت 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("عذراً، زر إغلاق التكت مخصص للإداريين فقط! ❌", ephemeral=True)
            return
        await interaction.response.send_message("جاري إغلاق وحذف التذكرة خلال 3 ثوانٍ... ⏱️")
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete()
        except:
            pass

@bot.tree.command(name="ticket", description="إنشاء لوحة التذاكر")
@app_commands.describe(message="رسالة اللوحة")
@app_commands.checks.has_permissions(administrator=True)
async def slash_ticket(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="🎫 | قسم تذاكر الدعم الفني", description=message, color=0x000000)
    await interaction.channel.send(embed=embed, view=TicketButtonView())
    await interaction.followup.send("تم إرسال لوحة التكتات بنجاح ✅", ephemeral=True)

# الأوامر الإدارية مع معالجة الأخطاء الدقيقة لمنع توقف الاستجابة
@bot.tree.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.describe(member="العضو المراد طرده", reason="السبب")
@app_commands.checks.has_permissions(kick_members=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    await interaction.response.defer(ephemeral=False)
    try:
        await member.kick(reason=reason)
        await interaction.followup.send(f"تم طرد العضو {member.mention} بنجاح ✅ (السبب: {reason})")
    except Exception as e:
        await interaction.followup.send(f"فشل الإجراء ❌. تأكد من صلاحيات البوت وترتيب رتبته.\nالخطأ: `{e}`", ephemeral=True)

@bot.tree.command(name="timeout", description="إسكات عضو مؤقتاً")
@app_commands.describe(member="العضو", time_input="المدة مثل 10m أو 1h", reason="السبب")
@app_commands.checks.has_permissions(moderate_members=True)
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, time_input: str, reason: str = "لا يوجد سبب"):
    await interaction.response.defer(ephemeral=False)
    try:
        time_input = time_input.lower().strip()
        minutes = 0
        if time_input.isdigit():
            minutes = int(time_input)
        elif time_input.endswith('m'):
            minutes = int(time_input[:-1])
        elif time_input.endswith('h'):
            minutes = int(time_input[:-1]) * 60
        elif time_input.endswith('d'):
            minutes = int(time_input[:-1]) * 1440
        else:
            await interaction.followup.send("صيغة الوقت غير صحيحة! استعمل m للدقائق أو h للساعات ❌", ephemeral=True)
            return

        duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await interaction.followup.send(f"تم إعطاء تايم أوت للعضو {member.mention} لمدة `{minutes} دقائق` ✅")
    except Exception as e:
        await interaction.followup.send(f"حدث خطأ أثناء إعطاء التايم أوت: `{e}`", ephemeral=True)

@bot.tree.command(name="ban", description="حظر عضو من السيرفر نهائياً")
@app_commands.describe(member="العضو المراد حظره", reason="السبب")
@app_commands.checks.has_permissions(ban_members=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    await interaction.response.defer(ephemeral=False)
    try:
        await member.ban(reason=reason)
        await interaction.followup.send(f"تم حظر العضو {member.mention} نهائياً 🚷✅ (السبب: {reason})")
    except Exception as e:
        await interaction.followup.send(f"فشل حظر العضو ❌. تأكد أن رتبة البوت أعلى من رتبة العضو المستهدف.\nالخطأ: `{e}`", ephemeral=True)

@bot.tree.command(name="rank", description="عرض مستواك ونقاطك بالسيرفر")
async def rank(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    user_id = interaction.user.id
    points = user_xp.get(guild_id, {}).get(user_id, 0)
    lvl = (points // 100) + 1
    
    embed = discord.Embed(
        title="📊 | بطاقة الرانك الخاصة بك",
        description=f"العضو: {interaction.user.mention}\n⭐ المستوى: **{lvl}**\n📈 النقاط الكلية: **{points} XP**",
        color=0x000000
    )
    await interaction.response.send_message(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! البوت شغال 🚀")

# معالجة الأخطاء العامة للأذونات حتى لا يعلق البوت
@slash_kick.error
@slash_timeout.error
@slash_ban.error
@slash_ticket.error
async def admin_errors(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if interaction.response.is_done():
            await interaction.followup.send("عذراً، لا تمتلك الصلاحيات الكافية لتنفيذ هذا الأمر! ❌", ephemeral=True)
        else:
            await interaction.response.send_message("عذراً، لا تمتلك الصلاحيات الكافية لتنفيذ هذا الأمر! ❌", ephemeral=True)
    else:
        print(f"خطأ غير متوقع في الأوامر: {error}")

token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("خطأ: لم يتم العثور على متغير DISCORD_TOKEN في إعدادات المنصة.")

