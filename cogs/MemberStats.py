import discord
from discord.ext import commands
from discord import app_commands
import json
import os

OWNER_ID = 1107355943408259112  # أونر البوت الأساسي
STATS_FILE = "stats.json"

class MemberStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_data()

    def load_data(self):
        if not os.path.exists(STATS_FILE):
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

    def get_data(self):
        if not os.path.exists(STATS_FILE):
            return {}
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_data(self, data):
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_ready(self, *args, **kwargs):
        print(f"📊 | نظام إحصائيات الأعضاء والتعديل (!id, !add_stats) جاهز للعمل.")

    # دالة موحدة لإنشاء وعرض بطاقة الـ ID
    async def send_id_card(self, destination, member: discord.Member, guild: discord.Guild):
        data = self.get_data()
        user_id_str = str(member.id)
        
        user_stats = data.get(user_id_str, {
            "monthly_raids": 0,
            "monthly_points": 0,
            "monthly_rank": "#--",
            "alltime_raids": 0,
            "alltime_rank": "#--",
            "alltime_points": 0,
            "alltime_points_rank": "#--",
            "tryout_rating": "Unranked",
            "win_streak_current": 0,
            "win_streak_best": 0,
            "wins": 0,
            "losses": 0
        })

        guild_name = guild.name if guild else "Server"

        total_matches = user_stats["wins"] + user_stats["losses"]
        win_rate = int((user_stats["wins"] / total_matches * 100)) if total_matches > 0 else 0

        embed = discord.Embed(
            title=f"Stats — {member.display_name}",
            color=discord.Color.from_rgb(46, 204, 113)
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        embed.add_field(
            name="📅 Monthly MVP",
            value=f"Raids: `{user_stats['monthly_raids']}`\nPoints: `{user_stats['monthly_points']}`\nRank: `{user_stats['monthly_rank']}`",
            inline=False
        )

        embed.add_field(
            name="👑 All-Time Legends",
            value=f"Raids: `{user_stats['alltime_raids']}`\nRank: `{user_stats['alltime_rank']}`",
            inline=False
        )

        embed.add_field(
            name="⭐ All-Time Points",
            value=f"Points: `{user_stats['alltime_points']}`\nRank: `{user_stats['alltime_points_rank']}`",
            inline=False
        )

        embed.add_field(
            name="🎯 Tryout Rating",
            value=f"`{user_stats['tryout_rating']}`",
            inline=False
        )

        embed.add_field(
            name="🔥 Server Win Streak",
            value=f"Current: `{user_stats['win_streak_current']}`\nBest: `{user_stats['win_streak_best']}`",
            inline=False
        )

        embed.add_field(
            name="🌍 Global Win Rate (per server)",
            value=f"{guild_name}\n— {user_stats['wins']}W/{user_stats['losses']}L ({win_rate}%)\n\nOverall: {user_stats['wins']}W/{user_stats['losses']}L ({win_rate}%) across 1 server(s)",
            inline=False
        )

        embed.set_footer(text=f"{guild_name} | بطاقة إحصائيات العضو", icon_url=guild.icon.url if guild.icon else None)

        if isinstance(destination, discord.Interaction):
            await destination.response.send_message(embed=embed, ephemeral=False)
        else:
            await destination.send(embed=embed)

    # 1. أمر عرض بطاقة الإحصائيات عبر !id
    @commands.command(name="id", description="عرض بطاقة الإحصائيات عبر !id")
    async def prefix_id(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        await self.send_id_card(ctx, member, ctx.guild)

    # 2. أمر عرض بطاقة الإحصائيات عبر سلاش /id
    @app_commands.command(name="id", description="عرض بطاقة إحصائيات العضو الشخصية.")
    @app_commands.describe(member="اختر العضو لعرض بطاقته (اختياري)")
    async def slash_id(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        await self.send_id_card(interaction, member, interaction.guild)

    # دالة تنفيذ وتحديث الإحصائيات (مشتركة للسلاش والـ Prefix)
    async def process_add_stats(
        self, 
        ctx_or_interaction, 
        member: discord.Member, 
        monthly_raids: int = None, 
        monthly_points: int = None, 
        wins: int = None, 
        losses: int = None, 
        win_streak: int = None
    ):
        # التحقق من الصلاحيات (أونر البوت أو أدمن بالسيرفر)
        user_obj = ctx_or_interaction.user if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.author
        if user_obj.id != OWNER_ID and not user_obj.guild_permissions.administrator:
            msg = "عذراً، هذا الأمر مخصص للإدارة والأونر حصراً!"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(msg)
            return

        data = self.get_data()
        user_id_str = str(member.id)

        if user_id_str not in data:
            data[user_id_str] = {
                "monthly_raids": 0, "monthly_points": 0, "monthly_rank": "#1",
                "alltime_raids": 0, "alltime_rank": "#1", "alltime_points": 0,
                "alltime_points_rank": "#1", "tryout_rating": "Pro",
                "win_streak_current": 0, "win_streak_best": 0, "wins": 0, "losses": 0
            }

        if monthly_raids is not None:
            data[user_id_str]["monthly_raids"] += monthly_raids
            data[user_id_str]["alltime_raids"] += monthly_raids
        if monthly_points is not None:
            data[user_id_str]["monthly_points"] += monthly_points
            data[user_id_str]["alltime_points"] += monthly_points
        if wins is not None:
            data[user_id_str]["wins"] += wins
        if losses is not None:
            data[user_id_str]["losses"] += losses
        if win_streak is not None:
            data[user_id_str]["win_streak_current"] = win_streak
            if win_streak > data[user_id_str]["win_streak_best"]:
                data[user_id_str]["win_streak_best"] = win_streak

        self.save_data(data)

        success_msg = f"✅ **تم تحديث إحصائيات اللاعب {member.mention} بنجاح!**\n**تم كملت**"
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(success_msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(success_msg)

    # 3. أمر الـ Prefix لتحديث الإحصائيات (!add_stats @user raids points wins losses streak)
    @commands.command(name="add_stats", description="تعديل إحصائيات العضو عبر !add_stats")
    async def prefix_add_stats(
        self, 
        ctx, 
        member: discord.Member, 
        monthly_raids: int = None, 
        monthly_points: int = None, 
        wins: int = None, 
        losses: int = None, 
        win_streak: int = None
    ):
        await self.process_add_stats(ctx, member, monthly_raids, monthly_points, wins, losses, win_streak)

    # 4. أمر السلاش لتحديث الإحصائيات (/add_stats)
    @app_commands.command(
        name="add_stats",
        description="تحديث أو إضافة إحصائيات ونقاط ورايدات لعضو معين."
    )
    @app_commands.describe(
        member="العضو المراد تعديل إحصائياته",
        monthly_raids="عدد الـ Raids المراد إضافتها",
        monthly_points="عدد النقاط المراد إضافتها",
        wins="عدد الانتصارات W الإضافية",
        losses="عدد الخسائر L الإضافية",
        win_streak="الـ Win Streak الحالي"
    )
    async def slash_add_stats(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member, 
        monthly_raids: int = None, 
        monthly_points: int = None, 
        wins: int = None, 
        losses: int = None, 
        win_streak: int = None
    ):
        await self.process_add_stats(interaction, member, monthly_raids, monthly_points, wins, losses, win_streak)

async def setup(bot):
    await bot.add_cog(MemberStats(bot))
