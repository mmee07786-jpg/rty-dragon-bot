import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import io
from PIL import Image, ImageDraw, ImageFont

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

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_text_image(self, text):
        img = Image.new('RGB', (400, 120), color=(30, 30, 35))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default(size=40)
        except:
            font = ImageFont.load_default()
        
        bbox = d.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        d.text(((400 - w) / 2, (120 - h) / 2), text, fill=(255, 255, 255), font=font)
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(buffer, filename="challenge.png")

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
        words = ["itzF18", "Discord", "Railway", "Python", "Gaming", "Vortex", "Sniper"]
        target_word = random.choice(words)
        
        file = self.create_text_image(target_word)
        await ctx.send("⚡ | أسرع واكتب الكلمة الموجودة في الصورة التالية:", file=file)
        
        def check(m):
            return m.channel == ctx.channel and m.content == target_word and not m.author.bot

        try:
            msg = await self.bot.wait_for('message', timeout=15.0, check=check)
            await ctx.send(f"🏆 | كفو {msg.author.mention}! كان الأسرع وكتب الكلمة بشكل صحيح وفاز!")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ | انتهى الوقت! الكلمة كانت: `{target_word}`")

    @commands.command(name="علم", aliases=["أعلام", "flags"])
    async def flags(self, ctx):
        flag_list = [
            {"image": "https://flagcdn.com/w320/jp.png", "name": "اليابان"},
            {"image": "https://flagcdn.com/w320/br.png", "name": "البرازيل"},
            {"image": "https://flagcdn.com/w320/iq.png", "name": "العراق"},
            {"image": "https://flagcdn.com/w320/is.png", "name": "ايسلندا"}
        ]
        selected = random.choice(flag_list)
        embed = discord.Embed(title="🌍 | ما هي الدولة التي يتبع لها هذا العلم؟", color=0x3498db)
        embed.set_image(url=selected["image"])
        
        await ctx.send(embed=embed)
        
        def check(m):
            return m.channel == ctx.channel and not m.author.bot and selected['name'] in m.content

        try:
            msg = await self.bot.wait_for('message', timeout=20.0, check=check)
            await ctx.send(f"🎉 | بطل يا {msg.author.mention}! تخمينك صح (**{selected['name']}**) 🏆")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ | انتهى الوقت! الإجابة الصحيحة كانت: **{selected['name']}**")

    @commands.command(name="لغز", aliases=["puzzle"])
    async def puzzle(self, ctx):
        puzzles = [
            {"q": "ما هو الشيء الذي أبيض من السعف وأسود من الليل، يؤكل في النهار ويحرم في الليل؟", "a": "الشاي"},
            {"q": "شيء يقرصك ولا تراه، فما هو؟", "a": "البرد"},
            {"q": "له عين ولا يرى، فما هو؟", "a": "الإبرة"}
        ]
        p = random.choice(puzzles)
        await ctx.send(f"🧩 | **حل اللغز التالي:**\n> **{p['q']}**\n*(أمامكم 20 ثانية للإجابة!)*")

        def check(m):
            return m.channel == ctx.channel and not m.author.bot and p['a'] in m.content

        try:
            msg = await self.bot.wait_for('message', timeout=20.0, check=check)
            await ctx.send(f"🎯 | عقريد يا {msg.author.mention}! الإجابة صحيحة (**{p['a']}**) 🧠")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ | انتهى الوقت! الإجابة الصحيحة كانت: **{p['a']}**")

    @commands.command(name="رياضيات", aliases=["math"])
    async def math_game(self, ctx):
        n1 = random.randint(1, 20)
        n2 = random.randint(1, 20)
        op = random.choice(["+", "-", "*"])
        
        if op == "+":
            ans = n1 + n2
        elif op == "-":
            ans = n1 - n2
        else:
            ans = n1 * n2

        await ctx.send(f"🧮 | أسرع واحسب النتيجة:\n# `{n1} {op} {n2} = ?`")

        def check(m):
            return m.channel == ctx.channel and not m.author.bot and m.content == str(ans)

        try:
            msg = await self.bot.wait_for('message', timeout=15.0, check=check)
            await ctx.send(f"⚡ | كفو {msg.author.mention}! الناتج صحيح (**{ans}**) وفزت بالتحدي 🏆")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ | انتهى الوقت! الناتج الصحيح هو: **{ans}**")

    @commands.command(name="سؤال", aliases=["question"])
    async def question(self, ctx):
        questions = [
            "ما هي عاصمة فرنسا؟",
            "كم عدد سور القرآن الكريم؟",
            "ما هو أكبر كوكب في المجموعة الشمسية؟"
        ]
        answers = ["باريس", "114", "المشتري"]
        idx = random.randint(0, len(questions) - 1)
        
        await ctx.send(f"❓ | **السؤال:** {questions[idx]}")

        def check(m):
            return m.channel == ctx.channel and not m.author.bot and answers[idx] in m.content

        try:
            msg = await self.bot.wait_for('message', timeout=20.0, check=check)
            await ctx.send(f"✨ | إجابة صحيحة يا {msg.author.mention} (**{answers[idx]}**) 🌟")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ | انتهى الوقت! الإجابة الصحيحة كانت: **{answers[idx]}**")

async def setup(bot):
    await bot.add_cog(Game(bot))

