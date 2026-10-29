const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../level_data.json');

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
        console.error("خطأ في حفظ بيانات التلفيل:", error);
    }
}

function getGuildSettings(guildId) {
    const data = loadData();
    if (!data.guilds) {
        data.guilds = {};
    }
    
    if (!data.guilds[guildId]) {
        data.guilds[guildId] = {
            leveling_status: false,
            levels: {},
            top_channel: null,
            top_message: "🔥 | هؤلاء هم الأبطال الأكثر تفاعلاً لهذا الأسبوع !",
            level_channel: null,
            custom_level_message: "🎉 مبروك {member}! صعدت إلى **Level {level}** 🚀",
            level_image_url: null
        };
        saveData(data);
    }
    return data.guilds[guildId];
}

function updateGuildSettings(guildId, guildData) {
    const data = loadData();
    if (!data.guilds) {
        data.guilds = {};
    }
    data.guilds[guildId] = guildData;
    saveData(data);
}

module.exports = {
    toggleLevelingCommand: new SlashCommandBuilder()
        .setName('toggle-leveling')
        .setDescription('[ خاص بالإدارة ] تفعيل أو إيقاف نظام التلفيل في هذا السيرفر فقط')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    rankCommand: new SlashCommandBuilder()
        .setName('rank')
        .setDescription('معرفة لفلك الحالي ونقاط الـ XP الخاصة بك في هذا السيرفر')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد فحص رانكه')),

    leaderboardCommand: new SlashCommandBuilder()
        .setName('leaderboard')
        .setDescription('عرض قائمة أفضل 10 أعضاء متفاعلين في هذا السيرفر'),

    setLevelChannelCommand: new SlashCommandBuilder()
        .setName('set-level-channel')
        .setDescription('[ خاص بالإدارة ] تحديد القناة المخصصة لإرسال إشعارات صعود الفلل لهذا السيرفر')
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('اختر القناة المخصصة للفلل')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    disableLevelChannelCommand: new SlashCommandBuilder()
        .setName('disable-level-channel')
        .setDescription('[ خاص بالإدارة ] إلغاء قناة التلفيل المخصصة لتظهر الرسائل في نفس روم الدردشة')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    setLevelMessageCommand: new SlashCommandBuilder()
        .setName('set-level-message')
        .setDescription('[ خاص بالإدارة ] تعديل رسالة التلفيل الخاصة بهذا السيرفر (استخدم {member} و {lvl})')
        .addStringOption(option =>
            option.setName('message')
                .setDescription('اكتب رسالة التلفيل الجديدة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    setLevelImageCommand: new SlashCommandBuilder()
        .setName('set-level-image')
        .setDescription('[ خاص بالإدارة ] تعيين رابط صورة إضافية تظهر مع رسالة صعود الفل')
        .addStringOption(option =>
            option.setName('image_url')
                .setDescription('رابط الصورة المباشر')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    setTopChannelCommand: new SlashCommandBuilder()
        .setName('set-top-channel')
        .setDescription('[ خاص بالإدارة ] تحديد قناة التوب الأسبوعي لهذا السيرفر')
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('اختر القناة المخصصة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    disableTopChannelCommand: new SlashCommandBuilder()
        .setName('disable-top-channel')
        .setDescription('[ خاص بالإدارة ] إلغاء تفعيل قناة التوبات الأسبوعية لهذا السيرفر')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    setTopMessageCommand: new SlashCommandBuilder()
        .setName('set-top-message')
        .setDescription('[ خاص بالإدارة ] تخصيص رسالة التوب الأسبوعي لهذا السيرفر')
        .addStringOption(option =>
            option.setName('message')
                .setDescription('اكتب نص الرسالة الجديد')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleMessage(message, client) {
        if (message.author.bot || !message.guild) return;

        const guildId = message.guild.id;
        const gSettings = getGuildSettings(guildId);

        if (!gSettings.leveling_status) return;

        const userId = message.author.id;
        if (!gSettings.levels) gSettings.levels = {};

        if (!gSettings.levels[userId]) {
            gSettings.levels[userId] = { xp: 0, level: 1 };
        }

        const xpGain = Math.floor(Math.random() * 11) + 15; // بين 15 و 25
        gSettings.levels[userId].xp += xpGain;

        const userData = gSettings.levels[userId];
        const xpNeeded = userData.level * 100;

        if (userData.xp >= xpNeeded) {
            userData.xp -= xpNeeded;
            userData.level += 1;
            const newLevel = userData.level;

            let targetChannel = message.channel;
            const levelChannelId = gSettings.level_channel;
            if (levelChannelId) {
                const customChannel = message.guild.channels.cache.get(levelChannelId);
                if (customChannel) {
                    targetChannel = customChannel;
                }
            }

            const msgTemplate = gSettings.custom_level_message || "🎉 مبروك {member}! صعدت إلى **Level {level}** 🚀";
            const finalMsg = msgTemplate
                .replace(/\{member\}/g, message.author.toString())
                .replace(/\{lvl\}/g, newLevel.toString())
                .replace(/\{level\}/g, newLevel.toString());

            try {
                const imageUrl = gSettings.level_image_url;
                if (imageUrl) {
                    const embed = new EmbedBuilder()
                        .setDescription(finalMsg)
                        .setImage(imageUrl)
                        .setColor(0x000000);
                    await targetChannel.send({ embeds: [embed] });
                } else {
                    await targetChannel.send({ content: finalMsg });
                }
            } catch (e) {}
        }

        updateGuildSettings(guildId, gSettings);
    },

    async handleToggleLeveling(interaction) {
        const guildId = interaction.guild.id;
        const gSettings = getGuildSettings(guildId);

        const currentStatus = gSettings.leveling_status || false;
        const newStatus = !currentStatus;
        gSettings.leveling_status = newStatus;
        updateGuildSettings(guildId, gSettings);

        if (newStatus) {
            await interaction.reply({ content: "✅ | تم **تفعيل** نظام التلفيل بنجاح في هذا السيرفر فقط!", ephemeral: true });
        } else {
            await interaction.reply({ content: "❌ | تم **إيقاف وتعطيل** نظام التلفيل في هذا السيرفر فقط!", ephemeral: true });
        }
    },

    async handleRank(interaction) {
        await interaction.deferReply({ ephemeral: false });

        const target = interaction.options.getUser('member') || interaction.user;
        const guildId = interaction.guild.id;
        const userId = target.id;

        const gSettings = getGuildSettings(guildId);
        const levelsData = gSettings.levels || {};

        let level = 1;
        let xp = 0;
        if (levelsData[userId]) {
            level = levelsData[userId].level;
            xp = levelsData[userId].xp;
        }

        const xpNeeded = level * 100;

        const embed = new EmbedBuilder()
            .setTitle(`📊 | إحصائيات الرانك لـ ${target.username}`)
            .setColor(0x000000)
            .setThumbnail(target.displayAvatarURL())
            .addFields(
                { name: "المستوى ( Level )", value: String(level), inline: true },
                { name: "النقاط ( XP )", value: `${xp} / ${xpNeeded}`, inline: true }
            );

        await interaction.followup({ embeds: [embed] });
    },

    async handleLeaderboard(interaction) {
        await interaction.deferReply({ ephemeral: false });
        const guildId = interaction.guild.id;

        const gSettings = getGuildSettings(guildId);
        const levelsData = gSettings.levels || {};

        if (Object.keys(levelsData).length === 0) {
            await interaction.followup.send("لا توجد بيانات تفاعل مسجلة في هذا السيرفر حتى الآن ! ❌");
            return;
        }

        const sortedUsers = Object.entries(levelsData)
            .sort((a, b) => (b[1].level - a[1].level) || (b[1].xp - a[1].xp))
            .slice(0, 10);

        let description = "";
        sortedUsers.forEach(([userId, data], index) => {
            description += `**#${index + 1}** | <@${userId}>\n ┗ Level: **${data.level}** | XP: **${data.xp}**\n\n`;
        });

        const embed = new EmbedBuilder()
            .setTitle("🏆 | قائمة أفضل 10 متفاعلين في السيرفر")
            .setDescription(description)
            .setColor(0x000000)
            .setFooter({ text: `Server: ${interaction.guild.name}` });

        await interaction.followup.send({ embeds: [embed] });
    },

    async handleSetLevelChannel(interaction) {
        const guildId = interaction.guild.id;
        const channel = interaction.options.getChannel('channel');
        const gSettings = getGuildSettings(guildId);

        gSettings.level_channel = channel.id;
        updateGuildSettings(guildId, gSettings);

        await interaction.reply({ content: `✅ | تم تعيين قناة إشعارات التلفيل في هذا السيرفر إلى ${channel} !`, ephemeral: true });
    },

    async handleDisableLevelChannel(interaction) {
        const guildId = interaction.guild.id;
        const gSettings = getGuildSettings(guildId);

        gSettings.level_channel = null;
        updateGuildSettings(guildId, gSettings);

        await interaction.reply({ content: "✅ | تم إلغاء قناة التلفيل المخصصة في هذا السيرفر. ستعود الرسائل في نفس روم الدردشة.", ephemeral: true });
    },

    async handleSetLevelMessage(interaction) {
        const guildId = interaction.guild.id;
        const messageText = interaction.options.getString('message');
        const gSettings = getGuildSettings(guildId);

        gSettings.custom_level_message = messageText;
        updateGuildSettings(guildId, gSettings);

        await interaction.reply({ content: `✅ | تم تحديث رسالة التلفيل في هذا السيرفر!\n📝 النص الجديد: \`${messageText}\``, ephemeral: true });
    },

    async handleSetLevelImage(interaction) {
        const guildId = interaction.guild.id;
        const imageUrl = interaction.options.getString('image_url');
        const gSettings = getGuildSettings(guildId);

        gSettings.level_image_url = imageUrl;
        updateGuildSettings(guildId, gSettings);

        await interaction.reply({ content: `✅ | تم تعيين صورة إشعارات التلفيل بنجاح!`, ephemeral: true });
    },

    async handleSetTopChannel(interaction) {
        const guildId = interaction.guild.id;
        const channel = interaction.options.getChannel('channel');
        const gSettings = getGuildSettings(guildId);

        gSettings.top_channel = channel.id;
        updateGuildSettings(guildId, gSettings);

        await interaction.reply({ content: `✅ | تم تعيين قناة التوبات الأسبوعية في هذا السيرفر إلى ${channel} !`, ephemeral: true });
    },

    async handleDisableTopChannel(interaction) {
        const guildId = interaction.guild.id;
        const gSettings = getGuildSettings(guildId);

        gSettings.top_channel = null;
        updateGuildSettings(guildId, gSettings);

        await interaction.reply({ content: "✅ | تم إلغاء تفعيل قناة التوبات الأسبوعية لهذا السيرفر.", ephemeral: true });
    },

    async handleSetTopMessage(interaction) {
        const guildId = interaction.guild.id;
        const messageText = interaction.options.getString('message');
        const gSettings = getGuildSettings(guildId);

        gSettings.top_message = messageText;
        updateGuildSettings(guildId, gSettings);

        await interaction.reply({ content: `✅ | تم حفظ رسالة التوب الجديدة لهذا السيرفر بنجاح !`, ephemeral: true });
    },

    // دالة حلقة التوب الأسبوعي التي تعمل كل 168 ساعة (7 أيام)
    startWeeklyLoop(client) {
        setInterval(async () => {
            const data = loadData();
            const guildsData = data.guilds || {};

            for (const [guildId, gSettings] of Object.entries(guildsData)) {
                if (!gSettings.leveling_status) continue;

                const guild = client.guilds.cache.get(guildId);
                if (!guild) continue;

                const levelsData = gSettings.levels || {};
                const topChannelId = gSettings.top_channel;
                const topMsg = gSettings.top_message || "🔥 | هؤلاء هم الأبطال الأكثر تفاعلاً لهذا الأسبوع !";

                if (Object.keys(levelsData).length > 0 && topChannelId) {
                    const topUserId = Object.keys(levelsData).reduce((maxId, currentId) => {
                        const current = levelsData[currentId];
                        const max = levelsData[maxId];
                        if (current.level > max.level || (current.level === max.level && current.xp > max.xp)) {
                            return currentId;
                        }
                        return maxId;
                    });

                    const topMember = await guild.members.fetch(topUserId).catch(() => null);
                    if (topMember) {
                        const channel = guild.channels.cache.get(topChannelId);
                        if (channel) {
                            const embed = new EmbedBuilder()
                                .setTitle("👑 | التوب الأسبوعي للمتفاعلين")
                                .setDescription(`${topMsg}\n\n🏆 المركز الأول لهذا الأسبوع: ${topMember} 🎯`)
                                .setColor(0x000000)
                                .setThumbnail(topMember.displayAvatarURL());
                            
                            await channel.send({ embeds: [embed] }).catch(() => {});
                        }
                    }

                    gSettings.levels = {};
                    updateGuildSettings(guildId, gSettings);
                }
            }
        }, 168 * 60 * 60 * 1000);
    }
};
