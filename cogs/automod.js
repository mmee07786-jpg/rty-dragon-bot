const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../data.json');

function loadData() {
    if (fs.existsSync(DATA_FILE)) {
        try {
            const data = fs.readFileSync(DATA_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return {};
        }
    }
    return {};
}

function saveData(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ البيانات:", error);
    }
}

class ModActionView extends ActionRowBuilder {
    constructor(member, offendingText) {
        super();
        this.member = member;
        this.offendingText = offendingText;

        const warnBtn = new ButtonBuilder()
            .setCustomId('automod_warn')
            .setLabel('⚠️ تحذير')
            .setStyle(ButtonStyle.Secondary);

        const kickBtn = new ButtonBuilder()
            .setCustomId('automod_kick')
            .setLabel('👢 طرد')
            .setStyle(ButtonStyle.Danger);

        const muteBtn = new ButtonBuilder()
            .setCustomId('automod_mute')
            .setLabel('⏳ ميوت 30 دقيقة')
            .setStyle(ButtonStyle.Primary);

        this.addComponents(warnBtn, kickBtn, muteBtn);
    }

    disableButtons() {
        this.components.forEach(component => component.setDisabled(true));
    }
}

// تخزين عدد المخالفات المؤقتة للجلسة الحالية لكل عضو (User ID -> Count)
const warningsCount = {};

module.exports = {
    setModChannelCommand: new SlashCommandBuilder()
        .setName('set_mod_channel')
        .setDescription('[خاص بالإدارة] تعيين روم تنبيهات المخالفات والكلمات الممنوعة')
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('روم الإدارة للتنبيهات')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    automodToggleCommand: new SlashCommandBuilder()
        .setName('automod_toggle')
        .setDescription('[خاص بالإدارة] تفعيل أو إلغاء تفعيل حماية الكلمات الممنوعة بالسيرفر')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    addBadwordCommand: new SlashCommandBuilder()
        .setName('add_badword')
        .setDescription('[خاص بالإدارة] إضافة كلمة ممنوعة لقائمة الحظر بالسيرفر')
        .addStringOption(option =>
            option.setName('word')
                .setDescription('الكلمة الممنوعة المراد إضافتها')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    removeBadwordCommand: new SlashCommandBuilder()
        .setName('remove_badword')
        .setDescription('[خاص بالإدارة] إزالة كلمة من قائمة الكلمات الممنوعة')
        .addStringOption(option =>
            option.setName('word')
                .setDescription('الكلمة المراد إزالتها')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleSetModChannel(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const channel = interaction.options.getChannel('channel');
        const data = loadData();

        if (!data.automod) data.automod = {};
        if (!data.automod[guildId]) data.automod[guildId] = { words: [], channel_id: null, enabled: true };

        data.automod[guildId].channel_id = channel.id;
        saveData(data);

        await interaction.followup.send(`✅ | تم بنجاح تعيين روم الإدارة للتنبيهات إلى: ${channel}`);
    },

    async handleAutomodToggle(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const data = loadData();

        if (!data.automod || !data.automod[guildId]) {
            await interaction.followup.send({ content: "❌ | نظام الحماية غير معدّ بعد في هذا السيرفر. استخدم أوامر الكلمات أولاً.", ephemeral: true });
            return;
        }

        const currentState = data.automod[guildId].enabled ?? true;
        const newState = !currentState;
        data.automod[guildId].enabled = newState;
        saveData(data);

        const statusText = newState ? "مفعل ✅" : "معطل (ملغي) ❌";
        await interaction.followup.send(`🛡️ | حالة نظام الحماية التلقائية الآن أصبحت: **{statusText}**`.replace('{statusText}', statusText));
    },

    async handleAddBadword(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const word = interaction.options.getString('word');
        const data = loadData();

        if (!data.automod) data.automod = {};
        if (!data.automod[guildId]) data.automod[guildId] = { words: [], channel_id: null, enabled: true };

        const cleanWord = word.toLowerCase();
        if (data.automod[guildId].words.includes(cleanWord)) {
            await interaction.followup.send({ content: `⚠️ | الكلمة **\`{word}\`** موجودة مسبقاً في قائمة الكلمات الممنوعة!`.replace('{word}', word), ephemeral: true });
            return;
        }

        data.automod[guildId].words.push(cleanWord);
        saveData(data);

        await interaction.followup.send(`✅ | تمت إضافة الكلمة **\`{word}\`** إلى قائمة الحظر بنجاح.`.replace('{word}', word));
    },

    async handleRemoveBadword(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const word = interaction.options.getString('word');
        const data = loadData();

        if (!data.automod || !data.automod[guildId] || !data.automod[guildId].words || data.automod[guildId].words.length === 0) {
            await interaction.followup.send({ content: "❌ | لا توجد كلمات ممنوعة مسجلة في هذا السيرفر أساساً!", ephemeral: true });
            return;
        }

        const cleanWord = word.toLowerCase();
        const index = data.automod[guildId].words.indexOf(cleanWord);
        if (index > -1) {
            data.automod[guildId].words.splice(index, 1);
            saveData(data);
            await interaction.followup.send(`🗑️ | تم إزالة الكلمة **\`{word}\`** من قائمة الحظر بنجاح.`.replace('{word}', word));
        } else {
            await interaction.followup.send({ content: `❌ | الكلمة **\`{word}\`** غير موجودة في قائمة الحظر.`.replace('{word}', word), ephemeral: true });
        }
    },

    async handleMessage(message) {
        if (message.author.bot || !message.guild) return;
        if (message.member && message.member.permissions.has(PermissionFlagsBits.Administrator)) return;

        const guildId = message.guild.id;
        const data = loadData();
        const automodData = data.automod?.[guildId] || {};

        if (automodData.enabled === false) return;

        const badWords = automodData.words || [];
        const modChannelId = automodData.channel_id;

        if (badWords.length === 0) return;

        const contentLower = message.content.toLowerCase();
        const triggeredWord = badWords.find(w => contentLower.includes(w));

        if (triggeredWord) {
            try {
                await message.delete();
            } catch (e) {}

            const userKey = `${guildId}-${message.author.id}`;
            warningsCount[userKey] = (warningsCount[userKey] || 0) + 1;
            const currentStrikes = warningsCount[userKey];

            if (currentStrikes < 3) {
                try {
                    const warningMsg = await message.channel.send(`⚠️ | ${message.author} احذر! لقد استخدمت كلمة ممنوعة (تنبيه رقم ${currentStrikes}/2).`);
                    setTimeout(async () => {
                        try { await warningMsg.delete(); } catch (e) {}
                    }, 5000);
                } catch (e) {}
                return;
            }

            warningsCount[userKey] = 0;

            if (modChannelId) {
                const modChannel = message.guild.channels.cache.get(modChannelId);
                if (modChannel) {
                    const embed = new EmbedBuilder()
                        .setTitle("🚨 تنبيه تكرار مخالفة الكلمات الممنوعة (المرة الثالثة)!")
                        .setDescription(
                            `• **العضو المخالف:** ${message.author} (\`${message.author.id}\`)\n` +
                            `• **الروم:** ${message.channel}\n` +
                            `• **الكلمة الممنوعة المستخدمة:** \`${triggeredWord}\`\n\n` +
                            `💬 **آخر رسالة نصية تسببت بالمخالفة:**\n> ${message.content}`
                        )
                        .setColor(0xFF0000)
                        .setFooter({ text: "تجاوز الحد المسموح للتنبيهات! اختر العقوبة المناسبة أدناه 👇" });

                    const view = new ModActionView(message.author, message.content);
                    await modChannel.send({ embeds: [embed], components: [view] });
                }
            }
        }
    },

    async handleButtonInteraction(interaction) {
        if (!interaction.isButton()) return;
        if (!['automod_warn', 'automod_kick', 'automod_mute'].includes(interaction.customId)) return;

        // استخراج العضو من الـ Embed أو افتراضياً
        const embed = interaction.message.embeds[0];
        if (!embed) return;

        // محاولة جلب العضو من محتوى الـ description عبر الـ mention
        const description = embed.description || "";
        const match = description.match(/<@!?(\d+)>/);
        if (!match) {
            await interaction.reply({ content: "❌ | لم يتم العثور على العضو المستهدف.", ephemeral: true });
            return;
        }

        const memberId = match[1];
        let member;
        try {
            member = await interaction.guild.members.fetch(memberId);
        } catch (e) {
            await interaction.reply({ content: "❌ | العضو غير موجود في السيرفر حالياً.", ephemeral: true });
            return;
        }

        // استخراج النص المخالف
        let offendingText = "استخدام كلمات ممنوعة متكررة";
        const textMatch = description.match(/>\s([\s\S]*)$/);
        if (textMatch) offendingText = textMatch[1].trim();

        if (interaction.customId === 'automod_warn') {
            await interaction.reply({ content: `✅ | تم إعطاء تحذير رسمي للعضو ${member} بواسطة ${interaction.user}.`, ephemeral: false });
        } else if (interaction.customId === 'automod_kick') {
            try {
                await member.kick(`استخدام كلمات ممنوعة متكررة: ${offendingText}`);
                await interaction.reply({ content: `👢 | تم طرد العضو ${member} بنجاح بواسطة ${interaction.user}.`, ephemeral: false });
            } catch (e) {
                await interaction.reply({ content: "❌ | لا أملك صلاحية طرد هذا العضو!", ephemeral: true });
                return;
            }
        } else if (interaction.customId === 'automod_mute') {
            try {
                const duration = 30 * 60 * 1000;
                await member.timeout(duration, `استخدام كلمات ممنوعة متكررة: ${offendingText}`);
                await interaction.reply({ content: `⏳ | تم إعطاء ميوت (Timeout) لمدة 30 دقيقة للعضو ${member} بواسطة ${interaction.user}.`, ephemeral: false });
            } catch (e) {
                await interaction.reply({ content: "❌ | لا أملك صلاحية عمل ميوت لهذا العضو!", ephemeral: true });
                return;
            }
        }

        // تعطيل الأزرار بعد الضغط
        const actionRow = new ActionRowBuilder();
        embed.components?.forEach(row => {
            row.components?.forEach(component => {
                const newButton = ButtonBuilder.from(component).setDisabled(true);
                actionRow.addComponents(newButton);
            });
        });

        // بدلاً من ذلك، ننشئ أزرار جديدة معطلة
        const disabledView = new ModActionView(member, offendingText);
        disabledView.disableButtons();

        await interaction.message.edit({ components: [disabledView] }).catch(() => {});
    }
};
