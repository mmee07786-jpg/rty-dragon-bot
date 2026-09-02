import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

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
            await interaction.response.send_message(f"✅ | تم انضمامك بنجاح للروليت! (المشاركون: {len(self.players)})", ephemeral=True)

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

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # أمر السلاش الجديد لعرض قائمة الألعاب مع عدد الأشخاص المطلوبين
    @app_commands.command(name="games", description="عرض قائمة الألعاب الشاملة مع عدد الأشخاص المطلوب لكل لعبة")
    async def slash_games(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 | قائمة ألعاب السيرفر وعدد اللاعبين",
            description=(
                "أهلاً بك في قسم الألعاب! إليك كافة الألعاب المتوفرة وعدد الأشخاص المطلوبين لكل لعبة:\n\n"
                "🎯 **ألعاب جماعية (تتطلب عدد معين):**\n"
                "• `-روليت` (أو `-roulette`) ➜ تتطلب **4 لاعبين فما فوق** (تنتظر 15 ثانية والخاسر ينطرد).\n"
                "• `-مافيا` (أو `-mafia`) ➜ تتطلب **أكثر من شخصين** لتوزيع الأدوار.\n\n"
                "⚡ **ألعاب فردية / سرعة تفاعل (شخص واحد أو عدة أشخاص يتنافسون):**\n"
                "• `-زر` (أو `-reflex`) ➜ شخص أو أكثر (أسرع ضغطة تفوز).\n"
                "• `-أسرع` (أو `-fasttype`) ➜ شخص أو أكثر (أسرع شخص يكتب الكلمة).\n"
                "• `-أعلام` (أو `-flags`) ➜ شخص أو أكثر (تحدي تخمين أعلام الدول).\n"
                "• `-لوخيروك` (أو `-wouldyourather`) ➜ فردي أو جماعي (خيارات ممتعة).\n"
                "• `-مفرد`, `-سمعني`, `-حكمة`, `-سؤال`, `-لغز`, `-مضاد`, `-جمع`, `-عقاب`, `-ركب`, `-ماركات`, `-مشاهير`, `-كراسي`, `-كتتويت`, `-غميضة`, `-نكتة`, `-رياضيات` ➜ ألعاب تفاعلية فردية/جماعية.\n\n"
                "📌 ملاحظة: جميع الألعاب تعمل مباشرة بالبادئة `-` **بدون أي مسافة** (مثال: `-روليت`)."
            ),
            color=0x9b59b6
        )
        await interaction.response.send_message(embed=embed)

    @commands.command(name="game", aliases=["gameslist"])
    async def games_menu(self, ctx):
        menu_text = (
            "╭─〔 Games 〕─╮\n\n"
            "1 ➜ `-مفرد`\n"
            "2 ➜ `-سمعني`\n"
            "3 ➜ `-حكمة`\n"
            "4 ➜ `-لوخيروك`\n"
            "5 ➜ `-سؤال`\n"
            "6 ➜ `-لغز`\n"
            "7 ➜ `-روليت` (4 أشخاص فأكثر 🎯)\n"
            "8 ➜ `-مضاد`\n"
            "9 ➜ `-جمع`\n"
            "10 ➜ `-عقاب`\n"
            "11 ➜ `-ركب`\n"
            "12 ➜ `-المارد` (قيد الصيانة 🔧⏳)\n"
            "13 ➜ `-ماركات`\n"
            "14 ➜ `-مشاهير`\n"
            "15 ➜ `-كراسي`\n"
            "16 ➜ `-كتتويت`\n"
            "17 ➜ `-زر` (شخص أو أكثر ⚡)\n"
            "18 ➜ `-أسرع` (شخص أو أكثر ⌨️)\n"
            "19 ➜ `-أعلام` (شخص أو أكثر 🌍)\n"
            "20 ➜ `-غميضة`\n"
            "21 ➜ `-نكتة`\n"
            "22 ➜ `-مافيا` (جماعية 🕵️‍♂️)\n"
            "23 ➜ `-رياضيات`\n\n"
            "💡 (ملاحظة: استعمل `/games` لعرض التفاصيل الكاملة)\n"
            "╰────────────────╯"
        )
        await ctx.send(menu_text)

    @commands.command(name="روليت", aliases=["roulette"])
    async def roulette(self, ctx):
        view = RouletteJoinView()
        embed = discord.Embed(
            title="🎯 | لعبة الروليت الروسية (طرد)",
            description="بدأت لعبة الروليت! أمامكم **15 ثانية** للضغط على الزر أدناه والانضمام.\n\n⚠️ **شروط اللعبة:** يجب أن يشارك 4 أعضاء على الأقل، والخاسر سيتم طرده من السيرفر فوراً!",
            color=0xff0000
        )
        msg = await ctx.send(embed=embed, view=view)
        await asyncio.sleep(15)

        for child in view.children:
            child.disabled = True
        
        players = view.players
        if len(players) < 4:
            embed.description = f"❌ | تم إلغاء الروليت لعدم اكتمال العدد! (المشاركون: {len(players)}/4)"
            await msg.edit(embed=embed, view=view)
            return

        victim = random.choice(players)
        embed.description = f"🎲 | انتهى الوقت!\n\n💀 الضحية التي وقع عليها الاختيار وتم طردها هي: **{victim.mention}** 🚀"
        await msg.edit(embed=embed, view=view)

        try:
            await victim.kick(reason="خسر في لعبة الروليت الروسية 🎯")
            await ctx.send(f"✅ | تم طرد {victim.mention} بنجاح من السيرفر.")
        except:
            await ctx.send(f"❌ | عذراً، لا أملك صلاحية طرد {victim.mention}.")

    @commands.command(name="زر", aliases=["reflex"])
    async def reflex(self, ctx):
        await ctx.send("⚡ **جاري الاستعداد للتحدي... حضر أصابعك!** 🕹️")
        await asyncio.sleep(random.uniform(2.0, 3.0))

        view = ReflexView()
        target_btn = view.buttons_list[view.target_index]
        target_btn.style = discord.ButtonStyle.success
        target_btn.label = "اضغطني بسرعة! 🔥"

        try:
            message = await ctx.send("🚨 **تغير لون الزر! أسرع ضغطة تفوز!** 🏃‍♂️💨", view=view)
            view.message = message
        except Exception as e:
            print(f"خطأ: {e}")

    @commands.command(name="لوخيروك", aliases=["wouldyourather"])
    async def wouldyourather(self, ctx):
        questions = [
            "تفضل تكون طائر وتطير وين ما تريد لو تقدر تختفي متى ما بغيت؟",
            "تعيش بدون إنترنت أسبوع لو بدون أكل تحبه شهر؟",
            "تصير أذكى شخص بالعالم لو أغنى شخص بالعالم؟",
            "تعيش بعالم زومبي لو تعيش بعالم فضاء خارجي؟"
        ]
        q = random.choice(questions)
        embed = discord.Embed(title="🤔 | لو خيروك", description=f"**{q}**", color=0x000000)
        await ctx.send(embed=embed)

    @commands.command(name="مافيا", aliases=["mafia"])
    async def mafia(self, ctx):
        roles = ["مافيا 🦹‍♂️", "شرطي 👮‍♂️", "دكتور 💉", "مواطن بريء 🧑"]
        role = random.choice(roles)
        await ctx.send(f"🕵️‍♂️ | {ctx.author.mention} دورك في لعبة المافيا هو: **{role}**")

    @commands.command(name="أسرع", aliases=["fasttype"])
    async def fasttype(self, ctx):
        words = ["itzF18", "Discord", "Railway", "Python", "Gaming", "Vortex"]
        target_word = random.choice(words)
        await ctx.send(f"⚡ | أسرع وكتب هذه الكلمة بدقة: `✨ {target_word} ✨`")
        
        def check(m):
            return m.channel == ctx.channel and m.content == target_word and not m.author.bot

        try:
            msg = await self.bot.wait_for('message', timeout=15.0, check=check)
            await ctx.send(f"🏆 | كفو {msg.author.mention}! كان الأسرع وكتب الكلمة بشكل صحيح وفاز!")
        except asyncio.TimeoutError:
            await ctx.send("⏰ | انتهى الوقت! محد كتب الكلمة بالسرعة المطلوبة.")

    @commands.command(name="أعلام", aliases=["flags"])
    async def flags(self, ctx):
        flag_list = [
            {"flag": "🇯🇵", "name": "اليابان", "reward": "50 نقطة"},
            {"flag": "🇧🇷", "name": "البرازيل", "reward": "50 نقطة"},
            {"flag": "🇮🇶", "name": "العراق", "reward": "30 نقطة"},
            {"flag": "🇮🇸", "name": "ايسلندا", "reward": "150 نقطة (جائزة مضاعفة!)"}
        ]
        selected = random.choice(flag_list)
        await ctx.send(f"🌍 | ما هي الدولة التي تتبع هذا العلم؟\n# {selected['flag']}\n*(الجائزة: {selected['reward']}! أسرع بالإجابة)*")
        
        def check(m):
            return m.channel == ctx.channel and not m.author.bot and selected['name'] in m.content

        try:
            msg = await self.bot.wait_for('message', timeout=20.0, check=check)
            await ctx.send(f"🎉 | بطل يا {msg.author.mention}! تخمينك صح (**{selected['name']}**) وفزت بـ **{selected['reward']}** 🏆")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ | انتهى الوقت! الإجابة الصحيحة كانت: **{selected['name']}**")

async def setup(bot):
    await bot.add_cog(Games(bot))
