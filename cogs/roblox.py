import discord
from discord.ext import commands
import aiohttp
import traceback

class RobloxChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="roblox", description="[الكلان] البحث عن حساب روبلوكس، عرض السكن كاملاً بدون خلفية، ومعرفة حالته")
    @discord.app_commands.describe(username="اكتب يوزر روبلوكس (Username الحقيقي بدقة)")
    async def roblox(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # 1. البحث عن الـ User عبر الـ POST request
                search_url = "https://users.roblox.com/v1/usernames/users"
                payload = {
                    "usernames": [username],
                    "excludeBannedUsers": True
                }
                
                async with session.post(search_url, json=payload) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(f"❌ | فشل الاتصال بروبلوكس (كود الخطأ: `{resp.status}`).", ephemeral=True)
                        return
                    
                    data = await resp.json()
                    users = data.get("data", [])
                    if not users:
                        await interaction.followup.send(f"❌ | لم يتم العثور على مستخدم روبلوكس بهذا اليوزر: `{username}`\n*(تأكد من كتابة اليوزر الرسمي الصحيح وليس اسم العرض)*", ephemeral=True)
                        return
                    
                    user_id = users[0]["id"]
                    display_name = users[0]["displayName"]
                    name = users[0]["name"]

                profile_url = f"https://www.roblox.com/users/{user_id}/profile"

                # 2. جلب معلومات الحساب الأساسية
                info_url = f"https://users.roblox.com/v1/users/{user_id}"
                async with session.get(info_url) as resp:
                    user_info = await resp.json()
                    created_at = user_info.get("created", "غير معروف")[:10]
                    description = user_info.get("description", "لا توجد نبذة شخصية.")
                    if len(description) > 120:
                        description = description[:120] + "..."

                # 3. جلب صورة السكن كاملة (Full Body Render) بصيغة PNG وبدون خلفية بيضاء إن أمكن عبر Thumbnail API
                # نستخدم endpoint الـ 420x420 للجسد الكامل
                thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
                async with session.get(thumb_url) as resp:
                    thumb_data = await resp.json()
                    skin_url = thumb_data["data"][0]["imageUrl"] if thumb_data.get("data") else None

                # 4. جلب حالة الحضور (Presence)
                presence_url = "https://presence.roblox.com/v1/presence/users"
                async with session.post(presence_url, json={"userIds": [user_id]}) as resp:
                    pres_data = await resp.json()
                    presence_list = pres_data.get("presences", [])
                    
                    game_status = "غير متصل 🔴"
                    place_info = "غير متوفر"
                    
                    if presence_list:
                        p = presence_list[0]
                        p_type = p.get("userPresenceType")
                        if p_type == 1:
                            game_status = "متصل بموقع روبلوكس 🟢"
                        elif p_type == 2:
                            game_status = "يلعب حالياً داخل لعبة 🎮"
                            last_location = p.get("lastLocation", "داخل خريطة روبلوكس")
                            place_info = f"العنوان / الخريطة: `{last_location}`"
                        elif p_type == 3:
                            game_status = "يعمل على Roblox Studio 💻"

                # تصميم الـ Embed الاحترافي مع عرض السكن كصورة رئيسية (Image) واضحة
                embed = discord.Embed(
                    title=f"🎮 | ملف لاعب Roblox: {name}",
                    url=profile_url,
                    description=f"**الاسم المعروض:** `{display_name}`\n**معرف الحساب (ID):** `{user_id}`\n**تاريخ الانضمام:** `{created_at}`\n\n**الحالة الآن:** {game_status}\n**مكان التواجد:**\n{place_info}",
                    color=discord.Color.from_rgb(30, 144, 255)
                )
                
                if description and description != "لا توجد نبذة شخصية.":
                    embed.add_field(name="📌 | النبذة الشخصية (Bio):", value=f"```{description}```", inline=False)
                    
                # وضع صورة السكن الكاملة بشكل بارز وكبير داخل الإمبد (Image عوضاً عن مجرد Thumbnail صغير)
                if skin_url:
                    embed.set_image(url=skin_url)

                embed.set_footer(text=f"طلب بواسطة {interaction.user.name} | ItzF18 Bot", icon_url=interaction.user.display_avatar.url)
                await interaction.followup.send(embed=embed)

            except Exception as e:
                print(f"Roblox API Error: {e}")
                traceback.print_exc()
                await interaction.followup.send("❌ | حدث خطأ برمجي داخلي أثناء جلب البيانات، راجع الـ Console.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RobloxChecker(bot))
