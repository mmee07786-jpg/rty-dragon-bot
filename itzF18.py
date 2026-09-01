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
    print("البوت جاهز ويعمل بكفاءة عالية على السحابة! 🚀")
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

# نظام التلفيل والتفاعل الأسبوعي التلقائي
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

@bot.tree.command(name="setwebhook")
@app_commands.describe(channel="القسم (القناة) الذي ستُرسل فيه توبات التفاعل أسبوعياً", url="رابط الويب هوك الخاص بالقناة")
@app_commands.checks.has_permissions(administrator=True)
async def set_webhook(interaction: discord.Interaction, channel: discord.TextChannel, url: str):
    server_webhooks[interaction.guild.id] = url
    await interaction.response.send_message(f"✅ | تم حفظ رابط الويب هوك بنجاح للقسم {channel.mention}! سيتم إرسال توب التفاعل تلقائياً بعد مرور أسبوع من الآن.", ephemeral=True)

@set_webhook.error
async def set_webhook_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message("عذراً، هذا الأمر مخصص للإداريين فقط! ❌", ephemeral=True)

@bot.tree.command(name="itzf18")
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
                
                payload = {
                    "content": message_content
                }
                
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
            description=(
                f"مرحباً بك {member.mention}!\n"
                "تم فتح هذه التذكرة الخاصة لك بنجاح.\n\n"
                "يرجى كتابة مشكلتك أو طلبك بالتفصيل، وسيتم الرد عليك من قبل الإدارة قريباً.\n"
                "⚠️ **ملاحظة:** إذا لم يتم إرسال أي رسالة خلال **ساعة كاملة**، سيتم إغلاق التذكرة تلقائياً.\n"
            ),
            color=0x000000
        )
        embed.set_footer(text=f"Requested by {member.name}", icon_url=member.display_avatar.url)

        await ticket_channel.send(content=f"{member.mention}", embed=embed, view=CloseTicketButtonView())
        await interaction.response.send_message(f"تم فتح تذكرتك بنجاح: {ticket_channel.mention} ✅", ephemeral=True)

        async def check_inactivity():
            try:
                def check(m):
                    return m.channel == ticket_channel and not m.author.bot
                await bot.wait_for('message', timeout=3600.0, check=check)
            except asyncio.TimeoutError:
                try:
                    await ticket_channel.delete()
                except:
                    pass

        bot.loop.create_task(check_inactivity())

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

@bot.tree.command(name="ticket")
@app_commands.checks.has_permissions(administrator=True)
async def slash_ticket(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="🎫 | قسم تذاكر الدعم الفني", description=message, color=0x000000)
    embed.set_footer(text=f"Server Support • {interaction.guild.name}")
    await interaction.channel.send(embed=embed, view=TicketButtonView())
    await interaction.followup.send("تم إرسال لوحة التكتات بنجاح ✅", ephemeral=True)

@slash_ticket.error
async def slash_ticket_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message("عذراً، هذا الأمر مخصص للإداريين فقط! ❌", ephemeral=True)

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    await interaction.response.defer()
    try:
        await member.kick(reason=reason)
        await interaction.followup.send(f"تم طرد العضو {member.mention} بنجاح ✅ (السبب: {reason})")
    except discord.Forbidden:
        await interaction.followup.send("فشل الإجراء: تأكد من صلاحيات البوت وترتيب رتبته ❌", ephemeral=True)

@slash_kick.error
async def slash_kick_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message("عذراً، لا تمتلك صلاحية طرد الأعضاء! ❌", ephemeral=True)

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, time_input: str, reason: str = "لا يوجد سبب"):
    await interaction.response.defer()
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
            await interaction.followup.send("صيغة الوقت غير صحيحة! ❌", ephemeral=True)
            return

        duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await interaction.followup.send(f"تم إعطاء تايم أوت للعضو {member.mention} بنجاح لمدة `{minutes} دقائق` ✅")
    except Exception as e:
        await interaction.followup.send(f"حدث خطأ: {e}", ephemeral=True)

@slash_timeout.error
async def slash_timeout_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message("عذراً، لا تمتلك صلاحية إسكات الأعضاء! ❌", ephemeral=True)

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
    await interaction.response.defer()
    try:
        await member.ban(reason=reason)
        await interaction.followup.send(f"تم حظر العضو {member.mention} نهائياً 🚷✅")
    except:
        await interaction.followup.send("فشل الإجراء ❌", ephemeral=True)

@slash_ban.error
async def slash_ban_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message("عذراً، لا تمتلك صلاحية الحظر! ❌", ephemeral=True)

@bot.tree.command(name="rank")
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

# قراءة التوكن بأمان من بيئة التشغيل في Railway
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("خطأ: لم يتم العثور على متغير DISCORD_TOKEN في إعدادات المنصة.")
