import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class CloseTicketButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إغلاق التكت 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # شرط منع الأعضاء من إغلاق التكت وقصرها على الإداريين فقط
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("عذراً، زر إغلاق التكت مخصص للإداريين فقط! ❌", ephemeral=True)
            return

        await interaction.response.send_message("جاري إغلاق وحذف التذكرة خلال 3 ثوانٍ... ⏱️")
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete()
        except:
            pass

class TicketButtonView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

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
                await self.bot.wait_for('message', timeout=3600.0, check=check)
            except asyncio.TimeoutError:
                try:
                    await ticket_channel.delete()
                except:
                    pass

        self.bot.loop.create_task(check_inactivity())

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="إرسال لوحة تذاكر الدعم الفني")
    @app_commands.describe(message="رسالة اللوحة التي ستظهر للأعضاء")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_ticket(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="🎫 | قسم تذاكر الدعم الفني",
            description=message,
            color=0x000000
        )
        embed.set_footer(text=f"Server Support • {interaction.guild.name}")
        
        await interaction.channel.send(embed=embed, view=TicketButtonView(self.bot))
        await interaction.followup.send("تم إرسال لوحة التكتات بنجاح ✅", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))

