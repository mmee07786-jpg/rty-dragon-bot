import discord
from discord.ext import commands
import aiohttp

class RobloxChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="roblox", description="[الكلان] البحث عن حساب روبلوكس ومعرفة حالته، اللعبة التي يلعبها، وحالته الحالية")
    @discord.app_commands.describe(username="اكتب اسم حساب روبلوكس (Username)")
    async def roblox(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            # 1. البحث عن الـ User ID باستخدام الـ Username
            search_url = "https://users.roblox.com/v1/users/search"
            params = {"keyword": username, "limit": 1}
            async with session.get(search_url, params=params) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ | حدث خطأ أثناء الاتصال بخوادم Roblox.", ephemeral=True)
                    return
                data = await resp.json()
                users = data.get("data", [])
                if not users:
                    await interaction.followup.send(f"❌ | لم يتم العثور على مستخدم روبلوكس بهذا الاسم: `{username}`", ephemeral=True)
                    return
                
                user_id = users[0]["id"]
                display_name = users[0]["displayName"]
                name = users[0]["name"]

            # 2. جلب معلومات الحساب الأساسية (تاريخ الإنشاء والنبذة)
            info_url = f"https://users.roblox.com/v1/users/{user_id}"
            async with session.get(info_url) as resp:
                user_info = await resp.json()
                created_at = user_info.get("created", "غير معروف")[:10]
                description = user_info.get("description", "لا توجد نبذة شخصية.")
                if len(description) > 120:
                    description = description[:120] + "..."

            # 3. جلب صورة الآفاتار (Avatar Headshot)
            thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
            async with session.get(thumb_url) as resp:
                thumb_data = await resp.json()
                avatar_url = thumb_data["data"][0]["imageUrl"] if thumb_data.get("data") else None

            # 4. جلب حالة الحضور (Presence API لمعرفة هل يلعب حالياً وبأي لعبة)
            presence_url = "https://presence.roblox.com/v1/presence/users"
            async with session.post(presence_url, json={"userIds": [user_id]}) as resp:
                pres_data = await resp.json()
                presence_list = pres_data.get("presences", [])
                
                game_status = "غير متصل 🔴"
                place_info = "غير متوفر"
                
                if presence_list:
                    p = presence_list[0]
                    p_type = p.get("userPresenceType")
                    # 0: Offline, 1: Online, 2: In Game, 3: In Studio
                    if p_type == 1:
                        game_status = "متصل بموقع روبلوكس 🟢"
                    elif p_type == 2:
                        game_status = "يلعب حالياً داخل لعبة 🎮"
                        last_location = p.get("lastLocation", "داخل خريطة روبلوكس")
                        place_info = f"العنوان / الخريطة: `{last_location}`\n*(ملاحظة: روبلوكس تحجب رابط السيرفر المباشر أمنياً، لكنه داخل اللعبة الآن)*"
                    elif p_type == 3:
                        game_status = "يعمل على Roblox Studio 💻"

        # تصميم الـ Embed الاحترافي
        embed = discord.Embed(
            title=f"🎮 | ملف لاعب Roblox: {name}",
            description=f"**الاسم المعروض:** `{display_name}`\n**معرف الحساب (ID):** `{user_id}`\n**تاريخ الانضمام لروبلوكس:** `{created_at}`\n\n**الحالة الآن:** {game_status}\n**مكان التواجد:**\n{place_info}",
            color=discord.Color.from_rgb(30, 144, 255)
        )
        
        if description and description != "لا توجد نبذة شخصية.":
            embed.add_field(name="📌 | النبذة الشخصية (Bio):", value=f"```{description}```", inline=False)
            
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.set_footer(text=f"طلب بواسطة {interaction.user.name} | ItzF18 Bot", icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RobloxChecker(bot))

