import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

# --- 1. قائمة الألعاب الرئيسية مع الأزرار ---
class GamesMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="قائمة الألعاب", style=discord.ButtonStyle.primary, emoji="🎮")
    async def games_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎮 | ألعاب سيرفر itzF18 المتاحة",
            description=(
                "اختر اللعبة التي تعجبك من الأوامر التالية:\n\n"
                "🎯 **/roulette** - لعبة الروليت (تنتظر 15 ثانية، 4 لاعبين والخاسر ينطرد)\n"
                "⚡ **/reflex** - لعبة الزر السريع وتغيير اللون\n"
                "🐺 **/mafia** - توزيع أدوار المافيا السريعة\n"
                "✂️ **/rps** - حجر، ورقة، مقص\n"
                "❌ **/tictactoe** - لعبة إكس أو (Tic Tac Toe)\n"
                "❓ **/wouldyourather** - لعبة لو خيروك\n"
                "⌨️ **/fasttype** - أسرع شخص يكتب الكلمة بدقة\n"
                "🌍 **/flags** - تحدي تخمين الأعلام بنقاط مضاعفة"
            ),
            color=0x000000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# --- 2. واجهة الانضمام للروليت ---
class RouletteJoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.players = []

    @discord.ui.button(label="انضمام للروليت 🎯", style=discord.ButtonStyle.danger, emoji="🔫")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            await interaction.response.send_message("لقد انضممت مسبقاً إلى هذه اللعبة! ⚠️", ephemeral=True)
        else:
            self.players.append(interaction.user)
            await interaction.response.send_message(f"✅ | تم انضمامك بنجاح للروليت! (المشاركون حتى الآن: {len(self.players)})", ephemeral=True)


# --- 3. واجهة لعبة الزر السريع (Reflex) ---
class ReflexButton(discord.ui.Button):
    def __init__(self, label, is_target: bool):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.is_target = is_target

    async def callback(self, interaction: discord.Interaction):
        view: ReflexView = self.view
        if view.is_ended:
            await interaction.response.send_message("انتهت اللعبة بالفعل!", ephemeral=True)
            return

        view.is_ended = True
        if self.is_target:
            view.winner = interaction.user
            await interaction.response.edit_message(content=f"🎉 كفو عليك يا {interaction.user.mention}! سرعة بديهة أسطورية وفزت بالتحدي! ⚡", view=None)
        else:
            await interaction.response.edit_message(content=f"❌ أكلت هوا يا {interaction.user.mention}! ضغطت على الزر الخطأ! 💀", view=None)
        view.stop()

class ReflexView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=5.0)
        self.winner = None
        self.is_ended = False
        self.target_index = random.randint(0, 3)
        self.buttons_list = []
        
        for i in range(4):
            is_target = (i == self.target_index)
            btn = ReflexButton(label=f"زر {i+1}", is_target=is_target)
            self.buttons_list.append(btn)
            self.add_item(btn)

    async def on_timeout(self):
        if not self.is_ended:
            self.is_ended = True
            for child in self.children:
                child.disabled = True
            try:
                if self.message:
                    await self.message.edit(content="⏱️ انتهى الوقت! محد ضغط على الزر المطلوب! 🥱", view=self)
            except:
                pass


# --- ملف الألعاب الرئيسي (Cog) الشامل ---
class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # قائمة الألعاب
    @app_commands.command(name="games", description="عرض قائمة الألعاب التفاعلية في البوت")
    async def games_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 | مركز ألعاب itzF18",
            description="اضغط على الزر بالأسفل لاستعراض قائمة الألعاب المتاحة وتحدي أعضاء السيرفر!",
            color=0x000000
        )
        await interaction.response.send_message(embed=embed, view=GamesMenu())

    # لعبة الروليت (15 ثانية، 4 لاعبين، طرد الخاسر)
    @app_commands.command(name="roulette", description="لعبة الروليت: تنەتي 15 ثانية، تشترط 4 لاعبين، والخاسر ينطرد!")
    @app_commands.checks.has_permissions(kick_members=True)
    async def roulette(self, interaction: discord.Interaction):
        view = RouletteJoinView()
        
        embed = discord.Embed(
            title="🎯 | لعبة الروليت الروسية (طرد)",
            description="بدأت لعبة الروليت! أمامكم **15 ثانية** للضغط على الزر أدناه والانضمام.\n\n⚠️ **شروط اللعبة:** يجب أن يشارك 4 أعضاء على الأقل، والخاسر سيتم طرده من السيرفر فوراً!",
            color=0xff0000
        )
        
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        await asyncio.sleep(15)

        for child in view.children:
            child.disabled = True
        
        players = view.players

        if len(players) < 4:
            embed.description = f"❌ | تم إلغاء الروليت لعدم اكتمال العدد! (المشاركون: {len(players)}/4)"
            await message.edit(embed=embed, view=view)
            return

        victim = random.choice(players)

        embed.description = f"🎲 | انتهى الوقت!\n\n💀 الضحية التي وقع عليها الاختيار وتم طردها هي: **{victim.mention}** 🚀"
        await message.edit(embed=embed, view=view)

        try:
            await victim.kick(reason="خسر في لعبة الروليت الروسية 🎯")
            await interaction.followup.send(f"✅ | تم طرد {victim.mention} بنجاح من السيرفر.")
        except discord.Forbidden:
            await interaction.followup.send(f"❌ | عذراً، لا أملك صلاحية طرد {victim.mention} (رتبته أعلى أو أفتقر لصلاحيات Kick).")
        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء محاولة الطرد: {e}")

    # لعبة الزر السريع (Reflex)
    @app_commands.command(name="reflex", description="لعبة تفاعلية: ينتظر 3 ثانية ويتغير لون زر واحد فجأة ليتم الضغط عليه")
    async def reflex(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚡ **جاري الاستعداد للتحدي... حضر أصابعك!** 🕹️")
        await asyncio.sleep(random.uniform(2.0, 3.0))

        view = ReflexView()
        target_btn = view.buttons_list[view.target_index]
        target_btn.style = discord.ButtonStyle.success
        target_btn.label = "اضغطني بسرعة! 🔥"

        try:
            message = await interaction.followup.send("🚨 **تغير لون الزر! أسرع ضغطة تفوز!** 🏃‍♂️💨", view=view)
            view.message = message
        except Exception as e:
            print(f"خطأ في إرسال اللعبة: {e}")

    # لعبة حجر ورقة مقص
    @app_commands.command(name="rps", description="لعبة حجرة، ورقة، مقص")
    @app_commands.choices(choice=[
        app_commands.Choice(name="حجرة 🪨", value="rock"),
        app_commands.Choice(name="ورقة 📄", value="paper"),
        app_commands.Choice(name="مقص ✂️", value="scissors")
    ])
    async def rps(self, interaction: discord.Interaction, choice: str):
        bot_choice = random.choice(["rock", "paper", "scissors"])
        choices_ar = {"rock": "حجرة 🪨", "paper": "ورقة 📄", "scissors": "مقص ✂️"}
        
        if choice == bot_choice:
            result = "🤝 تعادلنا!"
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "🎉 مبروك، أنت الفائز! 🏆"
        else:
            result = "🤖 هاردلك، البوت فاز عليك!"

        await interaction.response.send_message(f"اختيارك: **{choices_ar[choice]}**\nاختيار البوت: **{choices_ar[bot_choice]}**\n\n**النتيجة:** {result}")

    # لعبة لو خيروك
    @app_commands.command(name="wouldyourather", description="لعبة لو خيروك بين شيئين")
    async def wouldyourather(self, interaction: discord.Interaction):
        questions = [
            "تفضل تكون طائر وتطير وين ما تريد لو تقدر تختفي متى ما بغيت؟",
            "تعيش بدون إنترنت أسبوع لو بدون أكل تحبه شهر؟",
            "تصير أذكى شخص بالعالم لو أغنى شخص بالعالم؟",
            "تعيش بعالم زومبي لو تعيش بعالم فضاء خارجي؟"
        ]
        q = random.choice(questions)
        embed = discord.Embed(title="🤔 | لو خيروك", description=f"**{q}**", color=0x000000)
        await interaction.response.send_message(embed=embed)

    # لعبة المافيا
    @app_commands.command(name="mafia", description="توزيع أدوار المافيا السريعة بين الأعضاء")
    async def mafia(self, interaction: discord.Interaction):
        roles = ["مافيا 🦹‍♂️", "شرطي 👮‍♂️", "دكتور 💉", "مواطن بريء 🧑"]
        role = random.choice(roles)
        await interaction.response.send_message(f"🕵️‍♂️ | {interaction.user.mention} دورك في لعبة المافيا هو: **{role}**", ephemeral=True)

    # لعبة أسرع (سرعة الكتابة)
    @app_commands.command(name="fasttype", description="أسرع شخص يكتب الكلمة التي يظهرها البوت يفوز!")
    async def fasttype(self, interaction: discord.Interaction):
        words = ["itzF18", "Discord", "Railway", "Python", "Gaming", "Vortex"]
        target_word = random.choice(words)
        
        await interaction.response.send_message(f"⚡ | أسرع وكتب هذه الكلمة بدقة: `✨ {target_word} ✨`")
        
        def check(m):
            return m.channel == interaction.channel and m.content == target_word and not m.author.bot

        try:
            msg = await self.bot.wait_for('message', timeout=15.0, check=check)
            await interaction.followup.send(f"🏆 | كفو {msg.author.mention}! كان الأسرع وكتب الكلمة بشكل صحيح وفاز بالترتيب!")
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ | انتهى الوقت! محد كتب الكلمة بالسرعة المطلوبة.")

    # لعبة الأعلام
    @app_commands.command(name="flags", description="تحدي تخمين علم الدولة (كلما صعب العلم زادت الجائزة)")
    async def flags(self, interaction: discord.Interaction):
        flag_list = [
            {"flag": "🇯🇵", "name": "اليابان", "reward": "50 نقطة"},
            {"flag": "🇧🇷", "name": "البرازيل", "reward": "50 نقطة"},
            {"flag": "🇮🇶", "name": "العراق", "reward": "30 نقطة"},
            {"flag": "🇮🇸", "name": "ايسلندا", "reward": "150 نقطة (جائزة مضاعفة!)"},
            {"flag": "🇧🇹", "name": "بوتان", "reward": "200 نقطة (جائزة مضاعفة كبرى!)"}
        ]
        
        selected = random.choice(flag_list)
        
        await interaction.response.send_message(f"🌍 | ما هي الدولة التي تتبع هذا العلم؟\n# {selected['flag']}\n*(الجائزة: {selected['reward']}! أسرع بالإجابة)*")
        
        def check(m):
            return m.channel == interaction.channel and not m.author.bot and selected['name'] in m.content

        try:
            msg = await self.bot.wait_for('message', timeout=20.0, check=check)
            await interaction.followup.send(f"🎉 | بطل يا {msg.author.mention}! تخمينك صح (**{selected['name']}**) وفزت بـ **{selected['reward']}** 🏆")
        except asyncio.TimeoutError:
            await interaction.followup.send(f"⏰ | انتهى الوقت! الإجابة الصحيحة كانت: **{selected['name']}**")

    # لعبة إكس أو
    @app_commands.command(name="tictactoe", description="معلومات لعبة إكس أو في السيرفر")
    async def tictactoe(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❌ | لعبة إكس أو (Tic Tac Toe)",
            description="قريباً سيتم تفعيل نظام أزرار إكس أو التفاعلي الكامل بين شخصين! تابع التحديثات 🚀",
            color=0x000000
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Games(bot))
