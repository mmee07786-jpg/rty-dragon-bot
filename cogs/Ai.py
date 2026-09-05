import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import aiohttp
import io

# 🔴 ضع مفتاح الـ API الخاص بـ Gemini هنا
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

genai.configure(api_key=GEMINI_API_KEY)

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

    @app_commands.command(name="ai", description="تحدث مع الذكاء الاصطناعي بأي لغة تريدها")
    @app_commands.describe(prompt="اكتب سؤالك أو رسالتك هنا")
    async def ai_chat(self, interaction: discord.Interaction, *, prompt: str):
        await interaction.response.defer()
        
        try:
            user_id = interaction.user.id
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = model.start_chat(history=[])
            
            chat = self.chat_sessions[user_id]
            response = chat.send_message(prompt)
            reply_text = response.text

            # تنسيق الرد وإرساله
            if len(reply_text) > 2000:
                await interaction.followup.send(reply_text[:2000])
            else:
                await interaction.followup.send(reply_text)

        except Exception as e:
            await interaction.followup.send(f"❌ | حدث خطأ أثناء الاتصال بعقل الذكاء الاصطناعي: `{e}`", ephemeral=True)

    @app_commands.command(name="image", description="توليد صورة بالذكاء الاصطناعي بناءً على وصفك")
    @app_commands.describe(prompt="اكتب وصف الصورة باللغة الإنجليزية للحصول على أفضل نتيجة")
    async def image(self, interaction: discord.Interaction, *, prompt: str):
        await interaction.response.defer()

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
