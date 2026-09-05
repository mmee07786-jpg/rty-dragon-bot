class RaidEndModal(discord.ui.Modal, title="🏁 | Conclude Raid & Record Results"):
    raid_number = discord.ui.TextInput(
        label="Raid Number",
        placeholder="",
        style=discord.TextStyle.short,
        required=True,
        default=""
    )
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

    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        non_bots = [m for m in interaction.guild.members if not m.bot][:25]
        
        if not non_bots:
            await interaction.response.send_message("❌ | No members found in server!", ephemeral=True)
            return

        view = RaidSelectView(self.raid_number.value, self.duration.value, self.result_status.value, self.win_reason.value, non_bots, interaction.user)
        await interaction.response.send_message("👇 **اختر المشاركين في الريد من القائمة أدناه:**", view=view, ephemeral=True)

class RaidSelectView(discord.ui.View):
    def __init__(self, raid_number, duration, result_status, win_reason, members, author):
        super().__init__(timeout=180)
        self.raid_number = raid_number
        self.duration = duration
        self.result_status = result_status
        self.win_reason = win_reason
        self.author = author
        
        options = [
            discord.SelectOption(label=m.display_name[:50], value=str(m.id), description=f"User: {m.name}")
            for m in members
        ]
        
        self.select_menu = discord.ui.Select(
            placeholder="⭐ اختر المشاركين من القائمة...",
            min_values=1,
            max_values=len(options),
            options=options
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ | هذه القائمة ليست لك!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        data = load_raid_data()
        
        participants = []
        for uid_str in self.select_menu.values:
            member = interaction.guild.get_member(int(uid_str))
            if member and member not in participants:
                participants.append(member)

        if not participants:
            await interaction.followup.send("❌ | لم تقم بتحديد أي مشارك!", ephemeral=True)
            return

        if "raider_stats" not in data:
            data["raider_stats"] = {}

        raider_list_text = ""
        for member in participants:
            m_id = str(member.id)
            if m_id not in data["raider_stats"]:
                data["raider_stats"][m_id] = 0
            data["raider_stats"][m_id] += 1
            total_rp = data["raider_stats"][m_id]
            raider_list_text += f"★ <@{m_id}> — {total_rp} RP\n"

        data["win_streak"] = data.get("win_streak", 0) + 1
        current_streak = data["win_streak"]
        save_raid_data(data)

        chunks = []
        current_chunk = ""
        for line in raider_list_text.split("\n"):
            if len(current_chunk) + len(line) + 1 > 1024:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        embed = discord.Embed(
            title=f"〈★〉🏁 **RAID CONCLUDED #{self.raid_number}**",
            description=f"`{self.win_reason}`",
            color=EMBED_COLOR
        )
        embed.add_field(name="🔢 Raid Number", value=f"`#{self.raid_number}`", inline=False)
        embed.add_field(name="🏁 Result", value=f"`✅ {self.result_status}`", inline=False)
        embed.add_field(name="⏱️ Duration", value=f"`{self.duration}`", inline=False)
        embed.add_field(name="👥 Total Raiders", value=f"`{len(participants)}`", inline=False)
        
        for idx, chunk in enumerate(chunks):
            field_name = f"✅ Raider List ({idx+1})" if len(chunks) > 1 else "✅ Raider List"
            embed.add_field(name=field_name, value=chunk, inline=False)

        embed.add_field(name="🔥 Win Streak", value=f"`{current_streak} in a row`", inline=False)
        
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
            
        embed.set_footer(text=f"Raid Ended by {interaction.user.name} | VLX Clan")

        await interaction.channel.send(content="🏁 **Raid Final Report & Results:**", embed=embed)
        await interaction.followup.send("✅ | Results recorded and report published successfully!", ephemeral=True)
