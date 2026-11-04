const { 
    SlashCommandBuilder, 
    EmbedBuilder, 
    ActionRowBuilder, 
    StringSelectMenuBuilder, 
    ButtonBuilder, 
    ButtonStyle,
    PermissionFlagsBits
} = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const OWNER_ID = "1107355943408259112";
const MEMORY_TIMEOUT = 3600 * 1000;

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
let genAI = null;
if (GEMINI_API_KEY) {
    genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
}

// موديل واحد مستقر فقط (محادثات نصية). الموديلات الأقدم (1.5 / 2.0 / 2.5)
// ألغاها غوغل بالكامل ("no longer available to new users"), فما فايدة من تجربتها.
const CHAT_MODEL = "gemini-3.8-flash";

const userMemory = new Map();

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
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
                await message.reply("هلا بيك فهد! وياك، شكو ماكو؟");
                return;
            }

            if (!genAI) {
                await message.reply("❌ عيوني فهد، مفتاح GEMINI_API_KEY غير معرف أو غير صحيح في إعدادات الاستضافة!");
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
                "الشخص الذي برمجك وصنعك هو فهد (itzF18)."
            );

            const memoryObj = userMemory.get(userId);
            let replyText = null;
            let busyError = false;

            // نحاول موديل واحد مستقر، مع إعادة محاولتين إذا كان "مزدحم مؤقتاً" (503)
            for (let attempt = 1; attempt <= 3; attempt++) {
                try {
                    const model = genAI.getGenerativeModel({
                        model: CHAT_MODEL,
                        systemInstruction: systemInstruction
                    });

                    const chat = model.startChat({ history: memoryObj.history });
                    const result = await chat.sendMessage(cleanPrompt);
                    const response = await result.response;
                    replyText = response.text().trim();

                    if (replyText) {
                        memoryObj.history.push({ role: 'user', parts: [{ text: cleanPrompt }] });
                        memoryObj.history.push({ role: 'model', parts: [{ text: replyText }] });
                    }
                    break;
                } catch (e) {
                    console.log(`⚠️ محاولة ${attempt} فشلت (${CHAT_MODEL}): ${e.message}`);
                    if (e.message && e.message.includes("503") && attempt < 3) {
                        busyError = true;
                        await sleep(1200 * attempt);
                        continue;
                    }
                    busyError = e.message && e.message.includes("503");
                    break;
                }
            }

            if (replyText) {
                if (replyText.length > 2000) {
                    replyText = replyText.substring(0, 1997) + "...";
                }
                await message.reply(replyText);
            } else if (busyError) {
                await message.reply("عيوني فهد، الخدمة مزدحمة حالياً من طرف غوغل، جرب بعد شوي. 🙏");
            } else {
                await message.reply("عيوني فهد، حدث خطأ في الاتصال بالذكاء الاصطناعي، تأكد من صحة المفتاح.");
            }
        }
    }
};
