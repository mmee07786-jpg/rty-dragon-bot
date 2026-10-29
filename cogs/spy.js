const { 
    SlashCommandBuilder, 
    PermissionFlagsBits, 
    EmbedBuilder, 
    ActionRowBuilder, 
    StringSelectMenuBuilder, 
    ButtonBuilder, 
    ButtonStyle 
} = require('discord.js');
const { GoogleGenAI } = require('@google/genai');

const OWNER_ID = "1107355943408259112";
const MEMORY_TIMEOUT = 3600 * 1000; // بالمللي ثانية

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
let ai = null;
if (GEMINI_API_KEY) {
    ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });
}

const MODELS_FALLBACK = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.5-pro"
];

// ذاكرة المستخدمين المؤقتة
const userMemory = new Map();

module.exports = {
    serversCommand: new SlashCommandBuilder()
        .setName('servers')
        .setDescription('[خاص بالمالك] لوحة سيطرة واستخبارات itzF18'),

    async handleReady(client) {
        console.log("🚀 | Cog Spy شغال بنجاح.");
    },

    // 1. أمر عرض السيرفرات (!سيرفر أو !servers)
    async handleServersCommand(message, client) {
        if (message.author.id !== OWNER_ID) return;

        if (client.guilds.cache.size === 0) {
            await message.channel.send("عيوني فهد، أنا لست منضماً إلى أي سيرفر حالياً.");
            return;
        }

        const guilds = Array.from(client.guilds.cache.values()).slice(0, 25);
        const options = guilds.map(g => ({
            label: g.name.substring(0, 100),
            value: g.id,
            description: `الأعضاء: ${g.memberCount}`
        }));

        const selectMenu = new StringSelectMenuBuilder()
            .setCustomId("spy_server_select")
            .setPlaceholder("اختر السيرفر لعرض تقرير التجسس الشامل...")
            .addOptions(options);

        const row = new ActionRowBuilder().addComponents(selectMenu);

        const embed = new EmbedBuilder()
            .setTitle("🕵️‍♂️ لوحة سيطرة واستخبارات itzF18")
            .setDescription("اختر السيرفر المطلوب ليصلك تقرير التجسس ورسائل القنوات مباشرة إلى **رسائلك الخاصة (DM)**:")
            .setColor(0x2b2d31);

        const sentMsg = await message.channel.send({ embeds: [embed], components: [row] });
        setTimeout(() => sentMsg.delete().catch(() => {}), 180 * 1000);
    },

    // معالجة تفاعلات القوائم والأزرار (Interactions)
    async handleInteraction(interaction, client) {
        if (!interaction.isStringSelectMenu() && !interaction.isButton()) return;

        const customId = interaction.customId;

        // اختيار السيرفر
        if (customId === "spy_server_select") {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، ما عندك هيك صلاحية أنطيك هاي المعلومات.. هذي تخص فهد وبس!", ephemeral: true });
                return;
            }

            await interaction.deferReply({ ephemeral: true });
            const guildId = interaction.values[0];
            const guild = client.guilds.cache.get(guildId);

            if (!guild) {
                await interaction.followup({ content: "❌ عذراً فهد، لم يتم العثور على السيرفر المطلوب.", ephemeral: true });
                return;
            }

            const createdAt = guild.createdAt;
            const ageDays = Math.floor((Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24));
            const years = Math.floor(ageDays / 365);
            const months = Math.floor((ageDays % 365) / 30);
            const days = (ageDays % 365) % 30;
            const ageStr = years > 0 ? `${years} سنة، ${months} شهر، ${days} يوم` : `${months} شهر، ${days} يوم`;

            const rolesList = Array.from(guild.roles.cache.values())
                .filter(r => r.name !== "@everyone")
                .reverse()
                .map(r => r.name);
            
            const formattedRoles = [];
            for (let i = 0; i < rolesList.length; i += 5) {
                formattedRoles.push(rolesList.slice(i, i + 5).join(" | "));
            }
            const rolesStr = formattedRoles.slice(0, 10).join("\n") || "لا توجد رتب";

            const vanityUrl = guild.vanityURLCode || "لا يوجد";

            let totalPosts = 0;
            try {
                guild.channels.cache.forEach(ch => {
                    if (ch.threads) totalPosts += ch.threads.cache.size;
                });
            } catch (e) {}

            let lastBan = "لا توجد حالات باند حديثة";
            let lastRoleAdded = "لا توجد بيانات رتب جديدة";
            let lastAuditAction = "لا توجد تعديلات حديثة";
            try {
                const auditLogs = await guild.fetchAuditLogs({ limit: 5 });
                auditLogs.entries.forEach(entry => {
                    if (entry.action === 22) {
                        lastBan = `تم باند لـ ${entry.target?.tag || 'عضو'} بواسطة ${entry.executor?.tag}`;
                    } else if (entry.action === 30) {
                        lastRoleAdded = `رتبة جديدة: ${entry.target?.name} بواسطة ${entry.executor?.tag}`;
                    } else if ([10, 20].includes(entry.action)) {
                        lastAuditAction = `تعديل بواسطة ${entry.executor?.tag}`;
                    }
                });
            } catch (e) {}

            const botsCount = guild.members.cache.filter(m => m.user.bot).size;
            const humansCount = guild.memberCount - botsCount;
            const adminSuspects = guild.members.cache.filter(m => m.permissions.has(PermissionFlagsBits.Administrator) && !m.user.bot).size;

            let lastPoster = "غير معروف";
            let lastPostContent = "لا توجد رسائل حديثة";
            let lastMentionText = "لا توجد إشارات سابقة للجميع.";
            try {
                for (const channel of guild.channels.cache.values()) {
                    if (channel.isTextBased()) {
                        const messages = await channel.messages.fetch({ limit: 10 }).catch(() => null);
                        if (messages) {
                            for (const msg of messages.values()) {
                                if (!msg.author.bot && lastPoster === "غير معروف") {
                                    lastPoster = `${msg.author.username} (<@${msg.author.id}>)`;
                                    lastPostContent = msg.content ? msg.content.substring(0, 100) : "[محتوى غير نصي]";
                                }
                                if (msg.content && (msg.content.includes("@everyone") || msg.content.includes("@here"))) {
                                    lastMentionText = `بواسطة <@${msg.author.id}>\nالرسالة: ${msg.content.substring(0, 150)}`;
                                    break;
                                }
                            }
                        }
                    }
                }
            } catch (e) {}

            let inviteLink = "غير متاح";
            try {
                for (const channel of guild.channels.cache.values()) {
                    if (channel.isTextBased() && channel.permissionsFor(guild.members.me).has(PermissionFlagsBits.CreateInstantInvite)) {
                        const invite = await channel.createInvite({ maxAge: 86400, maxUses: 0, unique: true });
                        inviteLink = invite.url;
                        break;
                    }
                }
            } catch (e) {}

            const infoText = 
                `🏰 **السيرفر:** ${guild.name} (\`${guild.id}\`)\n` +
                `👑 **صاحب السيرفر:** <@${guild.ownerId}>\n` +
                `👥 **الأعضاء:** ${guild.memberCount} (بشر: ${humansCount} | بوتات: ${botsCount})\n` +
                `⏳ **عمر السيرفر:** ${ageStr}\n` +
                `🔗 **الرابط:** ${inviteLink} | 🌐 **Vanity:** ${vanityUrl}\n` +
                `💬 **البوستات/الثريّدز:** ${totalPosts} | 🛡️ **الإداريين الكليين:** ${adminSuspects}\n` +
                `🚨 **سجل التجسس والعقوبات:**\n` +
                ` - آخر باند: \`${lastBan}\`\n` +
                ` - آخر رتبة مضافة: \`${lastRoleAdded}\`\n` +
                ` - آخر إجراء: \`${lastAuditAction}\`\n` +
                `👤 **آخر متفاعل:** ${lastPoster} -> \`${lastPostContent}\`\n` +
                `🔔 **آخر إشارة Everyone:**\n${lastMentionText}\n` +
                `📋 **الرتب المتساوية والموزعة:**\n${rolesStr}`;

            const extraRow = new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId(`spy_channels_${guild.id}`).setLabel("📂 عرض كافة الرومات بدون استثناء").setStyle(ButtonStyle.Primary),
                new ButtonBuilder().setCustomId(`spy_leave_${guild.id}`).setLabel("مغادرة السيرفر").setStyle(ButtonStyle.Danger)
            );

            try {
                await interaction.user.send({ content: infoText, components: [extraRow] });
                await interaction.followup.send({ content: "✅ تم إرسال تقرير السيرفر إلى رسائلك الخاصة (DM) بنجاح!", ephemeral: true });
            } catch (e) {
                await interaction.followup.send({ content: `❌ حدث خطأ، لم أستطع مراسلتك بالخاص: ${e.message}`, ephemeral: true });
            }
        }

        // عرض الرومات
        else if (customId.startsWith("spy_channels_")) {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، هذا الأمر خاص بفهد فقط!", ephemeral: true });
                return;
            }

            await interaction.deferReply({ ephemeral: true });
            const guildId = customId.split("_")[2];
            const guild = client.guilds.cache.get(guildId);

            if (!guild) {
                await interaction.followup.send({ content: "❌ السيرفر غير موجود.", ephemeral: true });
                return;
            }

            const allChannels = Array.from(guild.channels.cache.filter(c => c.isTextBased()).values());
            if (allChannels.length === 0) {
                await interaction.followup.send({ content: "❌ لا توجد أي قنوات نصية في هذا السيرفر.", ephemeral: true });
                return;
            }

            const options = allChannels.slice(0, 25).map(ch => ({
                label: ch.name.substring(0, 100),
                value: ch.id,
                description: `القسم: ${ch.parent?.name ? ch.parent.name.substring(0, 50) : 'بدون قسم'}`
            }));

            const select = new StringSelectMenuBuilder()
                .setCustomId(`spy_ch_select_${guildId}`)
                .setPlaceholder("اختر الروم لعرض رسائلها في الخاص...")
                .addOptions(options);

            const components = [new ActionRowBuilder().addComponents(select)];

            try {
                await interaction.user.send({
                    content: `📁 تم العثور على **${allChannels.length}** قناة/روم في السيرفر.\nاختر الروم المطلوبة لترسل لك رسائلها بالخاص:`,
                    components: components
                });
                await interaction.followup.send({ content: "✅ تم إرسال قائمة الرومات إلى رسائلك الخاصة (DM)!", ephemeral: true });
            } catch (e) {
                await interaction.followup.send({ content: `❌ عذراً، لم أستطع إرسال القائمة للخاص: ${e.message}`, ephemeral: true });
            }
        }

        // اختيار روم محددة لعرض الرسائل
        else if (customId.startsWith("spy_ch_select_")) {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، هذا مخصص لفهد فقط!", ephemeral: true });
                return;
            }

            await interaction.deferReply({ ephemeral: true });
            const channelId = interaction.values[0];
            const channel = client.channels.cache.get(channelId);

            if (!channel) {
                await interaction.followup.send({ content: "❌ لم يتم العثور على الروم المطلوب.", ephemeral: true });
                return;
            }

            const messagesLog = [];
            try {
                const now = Date.now();
                const afterTime = now - (10 * 24 * 60 * 60 * 1000);
                const beforeTime = now - (3 * 60 * 1000);

                const messages = await channel.messages.fetch({ limit: 100 });
                for (const msg of messages.values()) {
                    if (msg.author.bot) continue;
                    if (msg.createdTimestamp >= afterTime && msg.createdTimestamp <= beforeTime) {
                        const authorName = msg.webhookId ? `[WebHook] ${msg.author.username}` : msg.author.username;
                        const dateObj = new Date(msg.createdTimestamp);
                        const hourStr = String(dateObj.getUTCHours()).padStart(2, '0');
                        const dayStr = String(dateObj.getUTCDate()).padStart(2, '0');
                        const content = msg.content ? msg.content : "[محتوى ميديا / امبد]";
                        messagesLog.push(`${authorName} ( س ${hourStr} - يوم ${dayStr} ) : ${content}\n`);
                    }
                }
            } catch (e) {
                await interaction.followup.send({ content: `❌ عذراً، لا أملك صلاحية قراءة هذه الروم: ${e.message}`, ephemeral: true });
                return;
            }

            if (messagesLog.length === 0) {
                await interaction.followup.send({ content: `❌ لا توجد رسائل مطابقة في روم (#${channel.name}).`, ephemeral: true });
                return;
            }

            const chunks = [];
            let currentChunk = `📜 **سجل رسائل روم (#${channel.name}):**\n\n`;
            for (const line of messagesLog) {
                if (currentChunk.length + line.length > 1900) {
                    chunks.push(currentChunk);
                    currentChunk = line;
                } else {
                    currentChunk += line;
                }
            }
            if (currentChunk) chunks.push(currentChunk);

            try {
                for (const chunk of chunks) {
                    await interaction.user.send({ content: chunk });
                }
                await interaction.followup.send({ content: `✅ تم جلب رسائل روم (#${channel.name}) وإرسالها إلى **خاصك (DM)** بنجاح!`, ephemeral: true });
            } catch (e) {
                await interaction.followup.send({ content: `❌ حدث خطأ أثناء إرسال الرسائل للخاص: ${e.message}`, ephemeral: true });
            }
        }

        // مغادرة السيرفر
        else if (customId.startsWith("spy_leave_")) {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، هذا الزر مخصص للأونر فقط!", ephemeral: true });
                return;
            }

            await interaction.deferReply({ ephemeral: true });
            const guildId = customId.split("_")[2];
            const guild = client.guilds.cache.get(guildId);

            if (guild) {
                const name = guild.name;
                try {
                    await guild.leave();
                    await interaction.user.send({ content: `✅ تم مغادرة السيرفر (**${name}**) بنجاح.` });
                    await interaction.followup.send({ content: `✅ تم مغادرة السيرفر وإعلامك بالخاص.`, ephemeral: true });
                } catch (e) {
                    await interaction.followup.send({ content: `❌ حدث خطأ أثناء المغادرة: ${e.message}`, ephemeral: true });
                }
            } else {
                await interaction.followup.send({ content: "❌ السيرفر غير موجود.", ephemeral: true });
            }
        }
    },

    // 2. معالجة الذكاء الاصطناعي والرسائل
    async handleMessage(message, client) {
        if (message.author.bot) return;

        // التحقق: إذا كان في الخاص يرد مباشرة، وإذا كان في سيرفر يتطلب المنشن
        const isDM = !message.guild;
        const isMentioned = message.mentions.has(client.user) && !message.mentions.everyone;

        if (isDM || isMentioned) {
            let cleanPrompt = message.content
                .replace(new RegExp(`<@!?${client.user.id}>`, 'g'), "")
                .trim();

            let imageBuffer = null;
            if (message.attachments.size > 0) {
                for (const att of message.attachments.values()) {
                    if (att.contentType && att.contentType.includes("image")) {
                        try {
                            const response = await fetch(att.url);
                            const arrayBuf = await response.arrayBuffer();
                            imageBuffer = Buffer.from(arrayBuf);
                            break;
                        } catch (e) {
                            console.log(`⚠️ خطأ بتحميل الصورة: ${e.message}`);
                        }
                    }
                }
            }

            if (!cleanPrompt && !imageBuffer) {
                await message.reply("هلا بيك فهد! وياك، شكو ماكو؟");
                return;
            }

            const userId = message.author.id;
            const currentTime = Date.now();

            if (userMemory.has(userId)) {
                if (currentTime - userMemory.get(userId).time > MEMORY_TIMEOUT) {
                    userMemory.delete(userId);
                }
            }

            if (!userMemory.has(userId)) {
                userMemory.set(userId, { history: [], time: currentTime });
            } else {
                userMemory.get(userId).time = currentTime;
            }

            const systemInstruction = (
                "أنت ذكاء اصطناعي تتصرف بصفتك ذكر واسمك (itzF18). " +
                "تحدث دائماً بصيغة المذكر (مثلاً: سعيد، موجود، شفت، فكرت). " +
                "قاعدة اللغات واللهجات (مهمة جداً): يجب أن تتكيف تلقائياً مع لغة واللهجة التي يكلمك بها المستخدم. إذا كتب لك باللغة الإنجليزية رد باللغة الإنجليزية، وإذا كتب بلغة أخرى رد بها، وإذا كتب باللهجة العراقية أو العربية رد بنفس اللهجة واللغة تماماً وبشكل طبيعي. " +
                "قواعدك الأخلاقية والصارمة جداً: ممنوع نهائياً استخدام أي ألفاظ بذيئة، أو شتائم، أو سب بالدين، أو كلام خارج عن الأدب؛ كن محترماً ونظيفاً في كلامك دائماً. " +
                "قواعدك في الاسلوب: خذ كل كلمة يقولها فهد أو المستخدم أو اليوزر المذكور (<@1107355943408259112>) بكل جدية وتجاوب معها بدقة، واجعل ردودك قصيرة وعادية مثل البشر في الشات. " +
                "إذا سألك شخص غير فهد عن معلومات السيرفرات أو الأسرار، ارفض تماماً وتمنع بحجة (ما عندي هاي الصلاحية أو مو من اختصاصي - أو ما يعادلها باللغة التي يخاطبك بها). " +
                "الشخص الذي قام بصنعك وبرمجتك وتطويرك هو فهد (itzF18), اذكرها فقط إذا سألك أحد وبدون تكرار مزعج."
            );

            let replyText = null;
            let success = false;

            const userContentParts = [];
            if (imageBuffer) {
                userContentParts.push({
                    inlineData: {
                        data: imageBuffer.toString("base64"),
                        mimeType: "image/png"
                    }
                });
            }
            if (cleanPrompt) {
                userContentParts.push(cleanPrompt);
            } else {
                userContentParts.push("ما رأيك بهذه الصورة؟ / What do you think about this image?");
            }

            const memoryObj = userMemory.get(userId);

            for (const modelName of MODELS_FALLBACK) {
                try {
                    if (!ai) break;
                    
                    const chat = ai.chats.create({
                        model: modelName,
                        config: {
                            systemInstruction: systemInstruction
                        },
                        history: memoryObj.history
                    });

                    const result = await chat.sendMessage({ message: userContentParts });
                    if (result && result.text) {
                        replyText = result.text.trim();
                        
                        memoryObj.history.push({ role: 'user', parts: [{ text: cleanPrompt || "Image attachment" }] });
                        memoryObj.history.push({ role: 'model', parts: [{ text: replyText }] });

                        success = true;
                        break;
                    }
                } catch (e) {
                    console.log(`⚠️ خطأ بالموديل ${modelName}: ${e.message}`);
                    continue;
                }
            }

            if (success && replyText) {
                if (replyText.length > 2000) {
                    replyText = replyText.substring(0, 1997) + "...";
                }
                await message.reply(replyText);
            } else {
                await message.reply("عيوني فهد، صار ضغط خفيف، احاجيني مرة ثانية!");
            }
        }
    }
};
