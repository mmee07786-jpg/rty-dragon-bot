const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
    robloxCommand: new SlashCommandBuilder()
        .setName('roblox')
        .setDescription('[الكلان] البحث عن حساب روبلوكس ومعرفة حالته واللعبة التي يلعبها')
        .addStringOption(option =>
            option.setName('query')
                .setDescription('اكتب يوزر روبلوكس (Username) أو الـ ID الحقيقي مباشرة')
                .setRequired(true)),

    async handleRoblox(interaction) {
        await interaction.deferReply();
        const query = interaction.options.getString('query').trim();

        const headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json"
        };

        try {
            let userId = null;
            let name = "";
            let displayName = "";

            // التحقق إذا المدخل عبارة عن رقم (ID مباشرة) أو نص (Username)
            if (/^\d+$/.test(query)) {
                userId = parseInt(query, 10);
                const infoUrl = `https://users.roblox.com/v1/users/${userId}`;
                const resp = await fetch(infoUrl, { headers });
                
                if (!resp.ok) {
                    await interaction.followup({ content: `❌ | لم يتم العثور على مستخدم بهذا الـ ID: \`${query}\``, ephemeral: true });
                    return;
                }
                const userData = await resp.json();
                name = userData.name;
                displayName = userData.displayName;
            } else {
                // البحث عبر اليوزر
                const searchUrl = "https://users.roblox.com/v1/usernames/users";
                const payload = { usernames: [query], excludeBannedUsers: true };
                const resp = await fetch(searchUrl, {
                    method: "POST",
                    headers: headers,
                    body: JSON.stringify(payload)
                });

                if (!resp.ok) {
                    await interaction.followup({ content: `❌ | فشل الاتصال بروبلوكس (كود الخطأ: \`${resp.status}\`).`, ephemeral: true });
                    return;
                }

                const data = await resp.json();
                const users = data.data || [];
                if (users.length === 0) {
                    await interaction.followup({ content: `❌ | لم يتم العثور على مستخدم بهذا اليوزر: \`${query}\`\n*(تأكد من كتابة اليوزر الحقيقي وليس اسم العرض Display Name)*`, ephemeral: true });
                    return;
                }

                userId = users[0].id;
                displayName = users[0].displayName;
                name = users[0].name;
            }

            const profileUrl = `https://www.roblox.com/users/${userId}/profile`;

            // 2. جلب معلومات الحساب الأساسية
            const infoUrl = `https://users.roblox.com/v1/users/${userId}`;
            const infoResp = await fetch(infoUrl, { headers });
            const userInfo = await infoResp.json();
            const createdAt = (userInfo.created || "غير معروف").substring(0, 10);
            let description = userInfo.description || "لا توجد نبذة شخصية.";
            if (description.length > 120) {
                description = description.substring(0, 120) + "...";
            }

            // 3. جلب صورة السكن كاملة
            const thumbUrl = `https://thumbnails.roblox.com/v1/users/avatar?userIds=${userId}&size=420x420&format=Png&isCircular=false`;
            const thumbResp = await fetch(thumbUrl, { headers });
            const thumbData = await thumbResp.json();
            const skinUrl = thumbData.data?.[0]?.imageUrl || null;

            // 4. جلب حالة الحضور (Presence)
            const presenceUrl = "https://presence.roblox.com/v1/presence/users";
            const presenceResp = await fetch(presenceUrl, {
                method: "POST",
                headers: headers,
                body: JSON.stringify({ userIds: [userId] })
            });
            const presData = await presenceResp.json();
            const presenceList = presData.presences || [];

            let gameStatus = "غير متصل 🔴 (أو إعدادات الخصوصية مقفلة)";
            let placeInfo = "غير متوفر (تأكد من إعدادات الخصوصية للحساب)";

            if (presenceList.length > 0) {
                const p = presenceList[0];
                const pType = p.userPresenceType;
                // 0: Offline, 1: Online, 2: In Game, 3: In Studio
                if (pType === 1) {
                    gameStatus = "متصل بموقع روبلوكس 🟢";
                } else if (pType === 2) {
                    gameStatus = "يلعب حالياً داخل لعبة 🎮";
                    const lastLocation = p.lastLocation || "داخل خريطة روبلوكس";
                    placeInfo = `العنوان / الخريطة: \`${lastLocation}\``;
                } else if (pType === 3) {
                    gameStatus = "يعمل على Roblox Studio 💻";
                }
            }

            // تصميم الـ Embed
            const embed = new EmbedBuilder()
                .setTitle(`🎮 | ملف لاعب Roblox: ${name}`)
                .setURL(profileUrl)
                .setDescription(`**الاسم المعروض:** \`${displayName}\`\n**معرف الحساب (ID):** \`${userId}\`\n**تاريخ الانضمام:** \`${createdAt}\`\n\n**الحالة الآن:** ${gameStatus}\n**مكان التواجد:**\n${placeInfo}`)
                .setColor(0x1E90FF);

            if (description && description !== "لا توجد نبذة شخصية.") {
                embed.addFields({ name: "📌 | النبذة الشخصية (Bio):", value: `\`\`\`${description}\`\`\``, inline: false });
            }

            if (skinUrl) {
                embed.setImage(skinUrl);
            }

            embed.setFooter({ text: `طلب بواسطة ${interaction.user.username} | ItzF18 Bot`, iconURL: interaction.user.displayAvatarURL() });
            await interaction.followup({ embeds: [embed] });

        } catch (e) {
            console.log(`Roblox API Error: ${e.message}`);
            await interaction.followup({ content: "❌ | حدث خطأ برمجي داخلي أثناء جلب البيانات، راجع الـ Console.", ephemeral: true });
        }
    }
};
