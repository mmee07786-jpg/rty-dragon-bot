import discord
from discord.ext import commands

class JoinMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        owner = None
        # محاولة معرفة الشخص الذي أضاف البوت عبر السجلات (Audit Log)
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                if entry.target.id == self.bot.user.id:
                    owner = entry.user
                    break
        except Exception:
            pass

        # إذا ما قدرنا نحصل الشخص من السجلات، نرسلها لصاحب السيرفر كخيار بديل
        if not owner:
            owner = guild.owner

        if owner:
            try:
                embed = discord.Embed(
                    title="✨ | هلا بيك نورت السيرفر",
                    description=(
                        f"يا هلا فيك! شكراً لإضافتك بوت **{self.bot.user.name}** إلى سيرفرك\n"
                        f"`{guild.name}`\n\n"
                        "بوت عربي متكامل ومخصص لإدارة السيرفرات باحترافية وسهولة 🛡️\n\n"
                        "📋 **الميزات والأوامر المتاحة حالياً:**\n\n"
                        "🔹 **1. نظام الترحيب والبوست والمغادرة:**\n"
                        "• تخصيص رومات الترحيب، إعلانات البوست، والمغادرة بسهولة.\n"
                        "• إمكانية تعديل رسائل الترحيب والصور المرتبطة بها لكل ميزة.\n"
                        "• أوامر تجريبية (`/test_welcome`, `/test_boost`, `/test_leave`) لمعاينة الرسائل.\n\n"
                        "💡 **ملاحظة هامة جداً للمنشن:**\n"
                        "عندما تقوم بتعديل رسالة الترحيب أو المغادرة أو البوست، وتريد من البوت أن **يمنشن العضو** تلقائياً داخل الرسالة، يجب عليك استخدام الكلمة التالية في المكان الذي تريده: `{member}`\n"
                        "(مثال: *أهلاً بك يا {member} في السيرفر*).\n\n"
                        "🔹 **2. نظام التذاكر (Tickets):**\n"
                        "• إعداد وتفعيل نظام التذاكر لتنظيم دعم الأعضاء.\n\n"
                        "🔹 **3. الإدارة والحماية:**\n"
                        "• أوامر الإدارة الأساسية مثل الحظر (`/ban`) وغيرها لتنظيم السيرفر.\n\n"
                        "🚀 **تحديثات قادمة قريباً:**\n"
                        "نحن نستمر دائماً بتطوير ميزات إضافية لتحسين تجربة سيرفرك!\n\n"
                        "جربني وما راح تندم، شكراً لثقتك ولانضمامك 🤍"
                    ),
                    color=discord.Color.from_rgb(35, 39, 42)
                )
                await owner.send(embed=embed)
            except discord.Forbidden:
                # إذا كانت رسائل الخاص مغلقة عند الشخص، نتجاهل الخطأ حتى لا يوقف البوت
                pass

async def setup(bot):
    await bot.add_cog(JoinMessage(bot))
