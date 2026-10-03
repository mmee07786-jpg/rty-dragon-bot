import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime, timezone, timedelta

OWNER_ID = 1107355943408259112  # أونر البوت الأساسي
STATS_FILE = "stats.json"
RAID_DATA_FILE = "raid_data.json"
ROLES_CONFIG_FILE = "raid_roles.json"

class MemberStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_files()
        self.check_inactive_streaks.start()

    def cog_unload(self):
        self.check_inactive_streaks.cancel()

    def load_files(self):
        if not os.path.exists(STATS_FILE):
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        if not os.path.exists(ROLES_CONFIG_FILE):
            with open(ROLES_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"raid_roles": {}, "top_roles": []}, f, ensure_ascii=False, indent=4)

    def get_stats_data(self):
        if not os.path.exists(STATS_FILE):
            return {}
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}

    def save_stats_data(self, data):
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_raid_data(self):
        if not os.path.exists(RAID_DATA_FILE):
            return {}
        with open(RAID_DATA_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}

    def get_config_data(self):
        if not os.path.exists(ROLES_CONFIG_FILE):
            return {"raid_roles": {}, "top_roles": []}
        with open(ROLES_CONFIG_FILE, "r", encoding="utf-8") as f:
            try: 
                data = json.load(f)
                if "raid_roles" not in data: data["raid_roles"] = {}
                if "top_roles" not in data: data["top_roles"] = []
                return data
            except: return {"raid_roles": {}, "top_roles": []}

    def save_config_data(self, data):
        with open(ROLES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"📊 | نظام إحصائيات ورتب الرايدات والتوبات جاهز للعمل بنجاح.")

    async def check_and_apply_raid_roles(self, guild: discord.Guild, member: discord.Member, total_raids: int):
        config = self.get_config_data()
        gid_str = str(guild.id)
        server_raid_roles = config["raid_roles"].get(gid_str, {})
        if not server_raid_roles: return

        sorted_thresholds = sorted([int(k) for k in server_raid_roles.keys()])
        for req_raids in sorted_thresholds:
            role_id = int(server_raid_roles[str(req_raids)])
            role = guild.get_role(role_id)
            if not role: continue

            if total_raids >= req_raids:
                if role not in member.roles:
                    try: await member.add_roles(role, reason=f"الوصول إلى {total_raids} رايد")
                    except Exception as e: print(f"⚠️ خطأ منح رتبة رايد: {e}")

    async def update_top_roles_for_guild(self, guild: discord.Guild):
        config = self.get_config_data()
        gid_str = str(guild.id)
        top_roles_config = config["top_roles"]
        guild_top_configs = [r for r in top_roles_config if r.get("guild_id") == guild.id]
        if not guild_top_configs: return

        stats_data = self.get_stats_data()
        raid_data = self.get_raid_data()

        member_raids_map = {}
        server_raid_store = raid_data.get(gid_str, {}).get("raider_stats", {})
        
        all_user_ids = set(list(stats_data.keys()) + list(server_raid_store.keys()))
        for uid_str in all_user_ids:
            try: uid = int(uid_str)
            except: continue
            
            file_raids = server_raid_store.get(uid_str, 0)
            u_stats = stats_data.get(uid_str, {})
            alltime_r = max(u_stats.get("alltime_raids", 0), file_raids)
            if alltime_r > 0: member_raids_map[uid] = alltime_r

        sorted_members = sorted(member_raids_map.items(), key=lambda x: x[1], reverse=True)
        all_managed_role_ids = set(r["role_id"] for r in guild_top_configs)

        for index, (uid, raids) in enumerate(sorted_members):
            rank = index + 1
            member = guild.get_member(uid)
            if not member: continue

            deserved_role_id = None
            for cfg in guild_top_configs:
                if cfg["min_rank"] <= rank <= cfg["max_rank"]:
                    deserved_role_id = cfg["role_id"]
                    break

            for r_id in all_managed_role_ids:
                role_obj = guild.get_role(r_id)
                if not role_obj: continue

                if r_id == deserved_role_id:
                    if role_obj not in member.roles:
                        try: await member.add_roles(role_obj, reason=f"التوب التلقائي: المركز #{rank}")
                        except: pass
                else:
                    if role_obj in member.roles:
                        try: await member.remove_roles(role_obj, reason=f"خروج من نطاق التوب")
                        except: pass

    @tasks.loop(hours=24)
    async def check_inactive_streaks(self):
        try:
            stats_data = self.get_stats_data()
            now = datetime.now(timezone.utc)
            updated = False
            for user_id, u_data in stats_data.items():
                last_raid_str = u_data.get("last_raid_time")
                if last_raid_str and u_data.get("win_streak_current", 0) > 0:
                    last_time = datetime.fromisoformat(last_raid_str)
                    if now - last_time > timedelta(hours=24):
                        u_data["win_streak_current"] = 0
                        updated = True
            if updated: self.save_stats_data(stats_data)

            for guild in self.bot.guilds:
                await self.update_top_roles_for_guild(guild)
        except Exception as e:
            print(f"⚠️ خطأ في مهمة الخلفية: {e}")

    @check_inactive_streaks.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def send_id_card(self, destination, member: discord.Member, guild: discord.Guild):
        stats_data = self.get_stats_data()
        raid_data = self.get_raid_data()
        user_id_str = str(member.id)
        gid_str = str(guild.id) if guild else None

        raids_from_raidfile = 0
        if gid_str and gid_str in raid_data:
            raids_from_raidfile = raid_data[gid_str].get("raider_stats", {}).get(user_id_str, 0)

        user_stats = stats_data.get(user_id_str, {
            "monthly_points": 0, "monthly_rank": "#--", "alltime_rank": "#--",
            "alltime_points": 0, "alltime_points_rank": "#--", "tryout_rating": "Unranked",
            "win_streak_current": 0, "win_streak_best": 0, "wins": 0, "losses": 0
        })

        total_raids = max(user_stats.get("alltime_raids", 0), raids_from_raidfile)
        monthly_raids = max(user_stats.get("monthly_raids", 0), raids_from_raidfile)
        guild_name = guild.name if guild else "Server"
        total_matches = user_stats["wins"] + user_stats["losses"]
        win_rate = int((user_stats["wins"] / total_matches * 100)) if total_matches > 0 else 0

        embed = discord.Embed(title=f"Stats — {member.display_name}", color=discord.Color.from_rgb(46, 204, 113))
        if member.avatar: embed.set_thumbnail(url=member.avatar.url)

        embed.add_field(name="📅 Monthly MVP", value=f"Raids: `{monthly_raids}`\nPoints: `{user_stats['monthly_points']}`\nRank: `{user_stats['monthly_rank']}`", inline=False)
        embed.add_field(name="👑 All-Time Legends", value=f"Raids: `{total_raids}`\nRank: `{user_stats['alltime_rank']}`", inline=False)
        embed.add_field(name="⭐ All-Time Points", value=f"Points: `{user_stats['alltime_points']}`\nRank: `{user_stats['alltime_points_rank']}`", inline=False)
        embed.add_field(name="🎯 Tryout Rating", value=f"{user_stats['tryout_rating']}", inline=False)
        embed.add_field(name="🔥 Server Win Streak", value=f"Current: `{user_stats['win_streak_current']}`\nBest: `{user_stats['win_streak_best']}`", inline=False)
        embed.add_field(name="🌍 Global Win Rate", value=f"{guild_name}\n— {user_stats['wins']}W/{user_stats['losses']}L ({win_rate}%)", inline=False)

        if isinstance(destination, discord.Interaction):
            await destination.response.send_message(embed=embed, ephemeral=False)
        else: await destination.send(embed=embed)

    @app_commands.command(name="id", description="عرض بطاقة إحصائيات العضو الشخصية.")
    async def slash_id(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None: member = interaction.user
        await self.send_id_card(interaction, member, interaction.guild)

    @app_commands.command(name="set-raid-role", description="ربط عدد رايدات برتبة تلقائية")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raid_role(self, interaction: discord.Interaction, raids_count: int, role: discord.Role):
        config = self.get_config_data()
        gid_str = str(interaction.guild_id)
        config["raid_roles"].setdefault(gid_str, {})
        config["raid_roles"][gid_str][str(raids_count)] = role.id
        self.save_config_data(config)
        await interaction.response.send_message(f"✅ | تم ربط `{raids_count} Raids` بالرتبة {role.mention}", ephemeral=True)

    @app_commands.command(name="remove-raid-role", description="إزالة رتبة رايد تلقائية")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_raid_role(self, interaction: discord.Interaction, raids_count: int):
        config = self.get_config_data()
        gid_str = str(interaction.guild_id)
        if gid_str in config["raid_roles"] and str(raids_count) in config["raid_roles"][gid_str]:
            del config["raid_roles"][gid_str][str(raids_count)]
            self.save_config_data(config)
            await interaction.response.send_message(f"✅ | تم إزالة رتبة عدد الرايدات `{raids_count}`.", ephemeral=True)
        else: await interaction.response.send_message(f"❌ | لا توجد رتبة مسجلة للعدد `{raids_count}`.", ephemeral=True)

    @app_commands.command(name="raid-roles-list", description="عرض رتب الرايدات التراكمية")
    async def raid_roles_list(self, interaction: discord.Interaction):
        config = self.get_config_data()
        gid_str = str(interaction.guild_id)
        roles_map = config["raid_roles"].get(gid_str, {})
        if not roles_map:
            await interaction.response.send_message("❌ | لم يتم تحديد أي رتب تراكمية للرايدات!", ephemeral=True)
            return

        desc = "🛡️ **قائمة رتب الرايدات التراكمية:**\n\n"
        for r_count, r_id in sorted(roles_map.items(), key=lambda x: int(x[0])):
            r_obj = interaction.guild.get_role(int(r_id))
            desc += f"• `{r_count} Raids` ──> {r_obj.mention if r_obj else f'<@&{r_id}>'}\n"
        await interaction.response.send_message(embed=discord.Embed(title="🎖️ Raid Ranks", description=desc, color=discord.Color.blue()), ephemeral=False)

    @app_commands.command(name="set-top-role", description="تحديد رتبة لنطاق توبات معين")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(min_rank="المركز البدائي", max_rank="المركز النهائي", role="الرتبة الخاصة بهذا النطاق")
    async def set_top_role(self, interaction: discord.Interaction, min_rank: int, max_rank: int, role: discord.Role):
        config = self.get_config_data()
        config["top_roles"] = [r for r in config["top_roles"] if not (r["guild_id"] == interaction.guild_id and (r["min_rank"] == min_rank and r["max_rank"] == max_rank))]
        
        config["top_roles"].append({
            "guild_id": interaction.guild_id,
            "min_rank": min_rank,
            "max_rank": max_rank,
            "role_id": role.id
        })
        self.save_config_data(config)
        await interaction.response.send_message(f"✅ | تم تعيين رتبة {role.mention} لنطاق التوب من المركز **#{min_rank}** إلى **#{max_rank}** بنجاح!", ephemeral=True)
        await self.update_top_roles_for_guild(interaction.guild)

    @app_commands.command(name="remove-top-role", description="إزالة رتبة توب مخصصة")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(min_rank="المركز البدائي للنطاق المراد حذفه")
    async def remove_top_role(self, interaction: discord.Interaction, min_rank: int):
        config = self.get_config_data()
        initial_len = len(config["top_roles"])
        config["top_roles"] = [r for r in config["top_roles"] if not (r["guild_id"] == interaction.guild_id and r="min_rank" == min_rank)]
        
        if len(config["top_roles"]) < initial_len:
            self.save_config_data(config)
            await interaction.response.send_message(f"✅ | تم إزالة إعداد التوب الذي يبدأ من المركز #{min_rank}.", ephemeral=True)
            await self.update_top_roles_for_guild(interaction.guild)
        else:
            await interaction.response.send_message(f"❌ | لم يتم العثور على رتبة توب تبدأ من المركز #{min_rank}.", ephemeral=True)

    @app_commands.command(name="top-roles-list", description="عرض قائمة رتب التوبات الحالية بالسيرفر")
    async def top_roles_list(self, interaction: discord.Interaction):
        config = self.get_config_data()
        guild_top_configs = [r for r in config["top_roles"] if r["guild_id"] == interaction.guild_id]
        if not guild_top_configs:
            await interaction.response.send_message("❌ | لم يتم تحديد أي رتب توبات ديناميكية حتى الآن!", ephemeral=True)
            return

        desc = "👑 **قائمة رتب التوبات الديناميكية:**\n\n"
        for cfg in sorted(guild_top_configs, key=lambda x: x["min_rank"]):
            r_obj = interaction.guild.get_role(cfg["role_id"])
            r_mention = r_obj.mention if r_obj else f"<@&{cfg['role_id']}>"
            desc += f"• **Top {cfg['min_rank']} to {cfg['max_rank']}** ──> {r_mention}\n"
        
        await interaction.response.send_message(embed=discord.Embed(title="🏆 Dynamic Top Roles", description=desc, color=discord.Color.gold()), ephemeral=False)

    @app_commands.command(name="update-top-roles", description="إعادة تحديث وتوزيع رتب التوبات يدوياً الآن")
    @app_commands.checks.has_permissions(administrator=True)
    async def update_top_roles_manual(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.update_top_roles_for_guild(interaction.guild)
        await interaction.followup.send("✅ | تم إعادة فحص وتحديث جميع رتب التوبات في السيرفر بنجاح!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MemberStats(bot))
