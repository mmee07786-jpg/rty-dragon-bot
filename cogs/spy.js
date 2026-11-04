const { 
    SlashCommandBuilder, 
    EmbedBuilder, 
    ActionRowBuilder, 
    StringSelectMenuBuilder, 
    ButtonBuilder, 
    ButtonStyle,
    PermissionFlagsBits
} = require('discord.js');

const OWNER_ID = "1107355943408259112";
const MEMORY_TIMEOUT = 3600 * 1000;

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

// Node 18+ عنده fetch جاهز. إذا نسخة أقدم، نحاول node-fetch كبديل.
let fetchFn = (typeof fetch === 'function') ? fetch : null;
if (!fetchFn) {
    try { fetchFn = require('node-fetch'); } catch (e) { fetchFn = null; }
}

const userMemory = new Map();

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// بدل ما نخمن أسماء موديلات غوغل (تتغير وتُلغى باستمرار)، نسأل غوغل مباشرة
// عن قائمة الموديلات الشغالة فعلياً بهذا المفتاح، ونختار 3 منها ونتناوب بينها.
let modelPoolCache = { models: [], ts: 0 };
const MODEL_POOL_TTL = 60 * 60 * 1000; // ساعة
let rrIndex = 0;

// موديلات ثبت إنها ميتة نهائياً (404 "no longer available") بهذا التشغيل، نتجنبها بالمرات الجاية
const deadModels = new Set();

async function getModelPool() {
    const now = Date.now();
    const cachedAlive = modelPoolCache.models.filter(m => !deadModels.has(m));
    if (cachedAlive.length > 0 && (now - modelPoolCache.ts) < MODEL_POOL_TTL) {
        return cachedAlive;
    }
    if (!fetchFn || !GEMINI_API_KEY) return modelPoolCache.models; // آخر قائمة معروفة إن وجدت

    try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_API_KEY}`;
        const res = await fetchFn(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const usable = (data.models || [])
            .filter(m => Array.isArray(m.supportedGenerationMethods) && m.supportedGenerationMethods.includes("generateContent"))
            .filter(m => !/embedding|vision|aqa|tts|image-generation/i.test(m.name))
            .map(m => m.name.replace(/^models\//, ""));

        // نفضّل موديلات flash (أسرع وأرخص) بالأول، وبعدها الباقي
        const flashFirst = [
            ...usable.filter(n => /flash/i.test(n)),
            ...usable.filter(n => !/flash/i.test(n))
        ];

        const pool = [...new Set(flashFirst)].filter(n => !deadModels.has(n)).slice(0, 3);
        if (pool.length > 0) {
            modelPoolCache = { models: pool, ts: now };
            console.log(`ℹ️ موديلات الذكاء الاصطناعي الشغالة حالياً: ${pool.join(", ")}`);
        }
        return modelPoolCache.models.length > 0 ? modelPoolCache.models : usable.slice(0, 3);
    } catch (e) {
        console.log(`⚠️ تعذر جلب قائمة الموديلات من غوغل: ${e.message}`);
        return modelPoolCache.models; // آخر قائمة معروفة إن وجدت، وإلا فاضية
    }
}

// نداء مباشر لـ REST API (بدل مكتبة @google/generative-ai) لتفادي مشاكل apiVersion
async function callGemini(modelName, systemInstruction, history, userText) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${GEMINI_API_KEY}`;
    const body = {
        systemInstruction: { parts: [{ text: systemInstruction }] },
        contents: [...history, { role: "user", parts: [{ text: userText }] }]
    };

    const res = await fetchFn(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!res.ok) {
        const errText = await res.text().catch(() => "");
        const err = new Error(`HTTP ${res.status} :: ${errText.slice(0, 200)}`);
        err.status = res.status;
        throw err;
    }

    const data = await res.json();
    const text = data?.candidates?.[0]?.content?.parts?.map(p => p.text || "").join("") || "";
    if (!text) throw new Error("NO_CONTENT");
    return text;
}

module.exports = {
    serversCommand: new SlashCommandBuilder()
        .setName('spy')
        .setDescription('[خاص بالمالك] اختيار سيرفر: جلب رابط الدعوة أو مغادرته'),

    async handleReady(client) {
        console.log("🚀 | Cog Spy شغال بنجاح.");
    },

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
            .setPlaceholder("اختر السيرفر...")
            .addOptions(options);

        const row = new ActionRowBuilder().addComponents(selectMenu);

        const embed = new EmbedBuilder()
            .setTitle("🏰 | اختيار سيرفر")
            .setDescription("اختر السيرفر من القائمة أدناه للحصول على رابط دعوته أو مغادرته:")
            .setColor(0x2b2d31);

        const sentMsg = await message.channel.send({ embeds: [embed], components: [row] });
        setTimeout(() => sentMsg.delete().catch(() => {}), 180 * 1000);
    },

    async handleInteraction(interaction, client) {
        if (!interaction.isStringSelectMenu() && !interaction.isButton()) return;
        const customId = interaction.customId;

        if (customId === "spy_server_select") {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، هذا الأمر خاص بفهد فقط!", ephemeral: true });
                return;
            }

            await interaction.deferReply({ ephemeral: true });
            const guildId = interaction.values[0];
            const guild = client.guilds.cache.get(guildId);

            if (!guild) {
                await interaction.editReply({ content: "❌ لم يتم العثور على السيرفر المطلوب." });
                return;
            }

            let inviteLink = "تعذر إنشاء رابط دعوة (تحقق من صلاحية البوت: Create Invite)";
            try {
                for (const channel of guild.channels.cache.values()) {
                    if (channel.isTextBased() && channel.permissionsFor(guild.members.me)?.has(PermissionFlagsBits.CreateInstantInvite)) {
                        const invite = await channel.createInvite({ maxAge: 86400, maxUses: 0, unique: true });
                        inviteLink = invite.url;
                        break;
                    }
                }
            } catch (e) {
                console.log(`⚠️ تعذر إنشاء رابط دعوة: ${e.message}`);
            }

            const embed = new EmbedBuilder()
                .setTitle(`🏰 ${guild.name}`)
                .setDescription(
                    `👥 **الأعضاء:** ${guild.memberCount}\n` +
                    `🔗 **رابط الدعوة:** ${inviteLink}`
                )
                .setColor(0x2b2d31);

            const row = new ActionRowBuilder().addComponents(
                new ButtonBuilder()
                    .setCustomId(`spy_leave_${guild.id}`)
                    .setLabel("مغادرة السيرفر")
                    .setStyle(ButtonStyle.Danger)
            );

            await interaction.editReply({ embeds: [embed], components: [row] });
        }

        else if (customId.startsWith("spy_leave_")) {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، هذا الزر مخصص للأونر فقط!", ephemeral: true });
                return;
            }

            await interaction.deferReply({ ephemeral: true });
            const guildId = customId.split("_")[2];
            const guild = client.guilds.cache.get(guildId);

            if (!guild) {
                await interaction.editReply({ content: "❌ السيرفر غير موجود." });
                return;
            }

            const name = guild.name;
            try {
                await guild.leave();
                await interaction.editReply({ content: `✅ تم مغادرة السيرفر (**${name}**) بنجاح.` });
            } catch (e) {
                await interaction.editReply({ content: `❌ حدث خطأ أثناء المغادرة: ${e.message}` });
            }
        }
    },

    async handleMessage(message, client) {
        if (message.author.bot) return;

        const isDM = !message.guild;
        const isMentioned = message.mentions.has(client.user) && !message.mentions.everyone;

        if (isDM || isMentioned) {
            let cleanPrompt = message.content
                .replace(new RegExp(`<@!?${client.user.id}>`, 'g'), "")
                .trim();

            if (!cleanPrompt) {
                await message.reply("هلا بيك! شكو ماكو؟");
                return;
            }

            if (!GEMINI_API_KEY || !fetchFn) {
                await message.reply("❌ مفتاح GEMINI_API_KEY غير معرف في إعدادات الاستضافة (أو fetch غير متوفر)!");
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
                "تحدث دائماً بصيغة المذكر. " +
                "تفاعل باللهجة العراقية أو العربية أو الإنجليزية حسب لغة المستخدم. " +
                "ممنوع استخدام أي ألفاظ بذيئة أو شتائم. " +
                "لا تذكر اسمك (itzF18) ولا اسم من برمجك (فهد) إطلاقاً في ردودك العادية، ولا تفتتح أو تختم أي رد بذكرهم. " +
                "اذكر فقط إذا سألك الشخص بشكل مباشر وصريح من أنت أو من برمجك/صنعك (مثل: منو انت؟ شنو اسمك؟ منو صنعك؟ منو برمجك؟)، وبهذي الحالة فقط قول إن اسمك itzF18 وإن اللي برمجك وصنعك هو فهد."
            );

            const memoryObj = userMemory.get(userId);
            let replyText = null;
            let busyError = false;

            const pool = await getModelPool();
            if (pool.length === 0) {
                await message.reply("❌ تعذر جلب قائمة الموديلات المتوفرة من غوغل حالياً (تأكد من صحة المفتاح أو الاتصال).");
                return;
            }

            // نبدأ من موديل مختلف كل رسالة (تناوب/Round-robin) بدل ما نحمّل نفس الموديل دائماً
            const startIdx = rrIndex % pool.length;
            rrIndex++;
            const orderedModels = [...pool.slice(startIdx), ...pool.slice(0, startIdx)];

            for (let i = 0; i < orderedModels.length; i++) {
                const modelName = orderedModels[i];
                try {
                    const text = await callGemini(modelName, systemInstruction, memoryObj.history, cleanPrompt);
                    replyText = text.trim();

                    if (replyText) {
                        memoryObj.history.push({ role: 'user', parts: [{ text: cleanPrompt }] });
                        memoryObj.history.push({ role: 'model', parts: [{ text: replyText }] });
                    }
                    break;
                } catch (e) {
                    console.log(`⚠️ فشل الموديل ${modelName}: ${e.message}`);
                    if (e.status === 503 || e.status === 429) busyError = true;
                    if (e.status === 404 && /no longer available/i.test(e.message)) {
                        deadModels.add(modelName); // نشيله نهائياً لبقية الجلسة
                    }
                    // تأخير بسيط قبل تجربة الموديل التالي، حتى ما يكون الطلب كله أسرع من اللزوم
                    if (i < orderedModels.length - 1) await sleep(400);
                    continue;
                }
            }

            if (replyText) {
                if (replyText.length > 2000) {
                    replyText = replyText.substring(0, 1997) + "...";
                }
                await message.reply(replyText);
            } else if (busyError) {
                await message.reply("الخدمة مزدحمة حالياً من طرف غوغل، جرب بعد شوي. 🙏");
            } else {
                await message.reply("حدث خطأ في الاتصال بالذكاء الاصطناعي، تأكد من صحة المفتاح.");
            }
        }
    }
};
