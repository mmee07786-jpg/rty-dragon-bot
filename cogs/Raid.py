import discord
from discord.ext import commands
from discord.app_commands import Transform
from discord import app_commands
import json
import os
import asyncio

DATA_FILE = "raid_data.json"

BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&"
EMBED_COLOR = 0x8B0000

def load_raid_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raider_stats": {}, "win_streak": 0}

def save_raid_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class RaidStartModal(discord.ui.Modal, title="Raid Start & Announcement"):
    server_link = discord.ui.TextInput(
        label="Enemy Server Invite Link",
        placeholder="",
        style=discord.TextStyle.short,
        required=False,
        default=""
    )
    difficulty = discord.ui.TextInput(
        label="Difficulty",
        placeholder="e.g., Hard / Extreme",
        style=discord.TextStyle.short,
        required=True
    )
    targets = discord.ui.TextInput(
        label="Targets / Matchup",
        placeholder="VLX X TAL",
        style=discord.TextStyle.short,
        required=True,
        default="VLX X TAL"
    )
    counts = discord.ui.TextInput(
        label="Our Count & Their Count",
        placeholder="e.g., 8 vs 5",
        style=discord.TextStyle.short,
        required=True,
        default="? vs ?"
    )
    region = discord.ui.TextInput(
        label="Region",
        placeholder="EU / ME",
        style=discord.TextStyle.short,
        required=True,
        default="EU"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Broadcasting raid notification with @here and DMs...", ephemeral=True)

        embed = discord.Embed(
            title="**VLX Clan Raid Notification**",
            color=EMBED_COLOR
        )
        embed.add_field(name="Difficulty", value=f"`{self.difficulty.value}`", inline=False)
        embed.add_field(name="Targets", value=f"`{self.targets.value}`", inline=False)
        embed.add_field(name="Our Count & Their Count", value=f"`{self.counts.value}`", inline=False)
        embed.add_field(name="Region", value=f"`{self.region.value}`", inline=False)
        
        instructions = (
            "→ Click **Join** below to enter the server\n"
            "→ Follow callouts from raid leadership\n"
            "→ Stay until the raid is concluded"
        )
        embed.add_field(name="Instructions", value=instructions, inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Initiated by {interaction.user.name} | VLX Clan")

        class RaidView(discord.ui.View):
            def __init__(self, link):
                super().__init__(timeout=None)
                if link and link.strip() != "":
                    self.add_item(discord.ui.Button(label="Join", style=discord.ButtonStyle.link, url=link))

        view = RaidView(self.server_link.value)

        await interaction.channel.send(content="@here **New Raid Notification:**", embed=embed, view=view if self.server_link.value and self.server_link.value.strip() != "" else None)

        try:
            members = [m for m in interaction.guild.members if not m.bot]
            for member in members:
                try:
                    await member.send(content="**Raid Notification Direct Message:**", embed=embed, view=view if self.server_link.value and self.server_link.value.strip() != "" else None)
                    await asyncio.sleep(0.8)
                except Exception:
                    continue
        except Exception as e:
            print(f"Error sending DM: {e}")

class RaidEndModal(discord.ui.Modal, title="Conclude Raid & Record Results"):
    duration = discord.ui.TextInput(
        label="Raid Duration",
        placeholder="e.g., 1:11:40",
        style=discord.TextStyle.short,
        required=True
    )
    result_status = discord.ui.TextInput(
        label="Raid Result",
        placeholder="VICTORY",
        style=discord.TextStyle.short,
        required=True,
        default="VICTORY"
    )
    win_reason = discord.ui.TextInput(
        label="Reason / Operation Status",
        placeholder="e.g., Operation successful.",
        style=discord.TextStyle.short,
        required=True,
        default="Operation successful."
    )
    participants_input = discord.ui.TextInput(
        label="Mention participants here",
        placeholder="@User1 @User2 @User3 ...",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = load_raid_data()
        
        participants = []
        words = self.participants_input.value.split()
        for w in words:
            cleaned = w.replace("<@", "").replace(">", "").replace("!", "")
            if cleaned.isdigit():
                user_id = int(cleaned)
                member = interaction.guild.get_member(user_id)
                if not member:
                    try:
                        member = await interaction.guild.fetch_member(user_id)
                    except Exception:
                        member = None
                
                if member and member not in participants and not member.bot:
                    participants.append(member)

        if not participants:
            await interaction.followup.send("No valid participants found from the provided inputs!", ephemeral=True)
            return

        if "raider_stats" not in data:
            data["raider_stats"] = {}

        raider_mentions_list = []
        for member in participants:
            m_id = str(member.id)
            if m_id not in data["raider_stats"]:
                data["raider_stats"][m_id] = 0
            data["raider_stats"][m_id] += 1
            total_rp = data["raider_stats"][m_id]
            
            raider_mentions_list.append(f"<@{m_id}> ({total_rp} RP)")

        data["win_streak"] = data.get("win_streak", 0) + 1
        current_streak = data["win_streak"]
        save_raid_data(data)

        raider_text = ", ".join(raider_mentions_list)

        chunks = []
        current_chunk = ""
        for mention in raider_mentions_list:
            temp = current_chunk + (", " if current_chunk else "") + mention
            if len(temp) > 1024:
                chunks.append(current_chunk)
                current_chunk = mention
            else:
                current_chunk = temp
        if current_chunk:
            chunks.append(current_chunk)

        embed = discord.Embed(
            title="RAID CONCLUDED",
            description=f"`{self.win_reason.value}`",
            color=EMBED_COLOR
        )
        embed.add_field(name="Result", value=f"`{self.result_status.value}`", inline=False)
        embed.add_field(name="Duration", value=f"`{self.duration.value}`", inline=False)
        embed.add_field(name="Total Raiders", value=f"`{len(participants)}`", inline=False)
        
        for idx, chunk in enumerate(chunks):
            field_name = f"Raider List ({idx+1})" if len(chunks) > 1 else "Raider List"
            embed.add_field(name=field_name, value=chunk, inline=False)

        embed.add_field(name="Win Streak", value=f"`{current_streak} in a row`", inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="**Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("Results recorded and report published successfully!", ephemeral=True)

class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid-start", description="Start a raid with announcement and banner")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_start(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidStartModal())

    @app_commands.command(name="raid-end", description="Conclude the raid and record results")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_end(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaidEndModal())

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
