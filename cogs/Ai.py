import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import aiohttp
import io

# 🔴 ضع مفتاح الـ API الخاص بـ Gemini هنا
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

genai.configure(api_key=GEMINI_API_KEY)

# إعداد نموذج الدردشة
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="You are a smart, friendly AI assistant on Discord. You must always reply in the exact same language the user writes to you in (Arabic, English, or any other language)."
)

class AIStudio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_sessions = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.bot.user in message.mentions:
            user_message = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            
            if not user_message:
                return

            async with message.channel.typing():
                try:
                    user_id = message.author.id
                    if user_id not in self.chat_sessions:
                        self.chat_sessions[user_id] = model.start_chat(history=[])
                    
                    chat = self.chat_sessions[user_id]
                    response = chat.send_message(user_message)
                    reply_text = response.text

                    if len(reply_text) > 2000:
                        for i in range(0, len(reply_text), 2000):
                            await message.reply(reply_text[i:i+2000])
                    else:
                        await message.reply(reply_text)

                except Exception as e:
                    await message.reply(f"❌ | حدث خطأ أثناء الاتصال بعقل الذكاء الاصطناعي: `{e}`")

    @app_commands.command(name="image", description="توليد صورة بالذكاء الاصطناعي بناءً على وصفك (يدعم الإنجليزية والروسية وغيرها أفضل شي)")
    async def image(self, interaction: discord.Interaction, *, prompt: str):
        await interaction.response.defer()

        # نستخدم خدمة Pollinations AI المجانية والسريعة لتوليد الصور عبر واجهة برمجية مباشرة
        image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ | عذراً، فشل توليد الصورة. حاول مرة أخرى بوصف مختلف.", ephemeral=True)
                    return
                
                image_data = await resp.read()

        file = discord.File(io.BytesIO(image_data), filename="generated_image.png")
        
        embed = discord.Embed(
            title="🎨 | AI Image Generation",
            description=f"**Prompt:** `{prompt}`\n**Requested by:** {interaction.user.mention}",
            color=0x9b59b6
        )
        embed.set_image(url="attachment://generated_image.png")

        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(name="clear-ai", description="مسح ذاكرة محادثتك السابقة مع الذكاء الاصطناعي")
    async def clear_ai(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]
            await interaction.response.send_message("🧹 | تم مسح ذاكرتك السابقة بنجاح، لنبدأ محادثة جديدة!", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ | ليس لديك محادثة سابقة مخزنة أساساً.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIStudio(bot))
