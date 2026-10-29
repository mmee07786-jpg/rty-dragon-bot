const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

// قاموس لحفظ تحذيرات الأعضاء لكل سيرفر {guild_id: {user_id: count}}
const serverWarnings = {};

module.exports = {
    warnCommand: new SlashCommandBuilder()
        .setName('warn')
        .setDescription('تحذير عضو، وعند وصوله 5 تحذيرات يتم طرده تلقائياً')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد تحذيره')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers),

    clearWarningsCommand: new SlashCommandBuilder()
        .setName('clear_warnings')
        .setDescription('إزالة وتصفير تحذيرات العضو')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد تصفير تحذيراته')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers),

    banCommand: new SlashCommandBuilder()
        .setName('ban')
        .setDescription('حظر عضو من السيرفر نهائياً')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد حظره')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.BanMembers),

    unbanCommand: new SlashCommandBuilder()
        .setName('unban')
        .setDescription('رفع الحظر عن عضو باستخدام الآيدي (ID)')
        .addStringOption(option =>
            option.setName('user_id')
                .setDescription('آيدي المستخدم المراد رفع الحظر عنه')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.BanMembers),

    kickCommand: new SlashCommandBuilder()
        .setName('kick')
        .setDescription('طرد عضو من السيرفر')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد طرده')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers),

    timeoutCommand: new SlashCommandBuilder()
        .setName('timeout')
        .setDescription('إسكات عضو مؤقتاً (تايم أوت)')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد إعطاؤه تايم أوت')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('time_input')
                .setDescription('الوقت (مثال: 5 أو 10m أو 1h أو 1d)')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers),

    untimeoutCommand: new SlashCommandBuilder()
        .setName('untimeout')
        .setDescription('إزالة التايم أوت عن العضو')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد إزالة التايم أوت عنه')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers),

    muteCommand: new SlashCommandBuilder()
        .setName('mute')
        .setDescription('كتم العضو صوتياً (Server Mute)')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد كتمه صوتياً')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.MuteMembers),

    unmuteCommand: new SlashCommandBuilder()
        .setName('unmute')
        .setDescription('إلغاء الكتم الصوتي عن العضو')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد إلغاء الكتم عنه')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب'))
        .setDefaultMemberPermissions(PermissionFlagsBits.MuteMembers),

    async handleWarn(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        const userId = member.id;

        if (!serverWarnings[guildId]) serverWarnings[guildId] = {};
        if (!serverWarnings[guildId][userId]) serverWarnings[guildId][userId] = 0;

        serverWarnings[guildId][userId] += 1;
        const warnCount = serverWarnings[guildId][userId];

        if (warnCount >= 5) {
            try {
                await member.kick(`تخطي الحد الأقصى للتحذيرات (5 تحذيرات). آخر سبب: ${reason}`);
                serverWarnings[guildId][userId] = 0;
                await interaction.followup.send(`⚠️ | العضو ${member} وصل إلى **5 تحذيرات** وتم طرده تلقائياً من السيرفر! 👢`);
            } catch (e) {
                await interaction.followup.send(`وصل العضو 5 تحذيرات لكن فشل طرده بسبب صلاحيات البوت: \`${e.message}\``);
            }
        } else {
            await interaction.followup.send(`⚠️ | تم تحذير العضو ${member} بنجاح.\nعدد تحذيراته الحالية: **${warnCount}/5**\nالسبب: ${reason}`);
        }
    },

    async handleClearWarnings(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const member = interaction.options.getMember('member');
        const userId = member.id;

        if (serverWarnings[guildId] && serverWarnings[guildId][userId]) {
            serverWarnings[guildId][userId] = 0;
            await interaction.followup.send(`✅ | تم تصفير وإزالة جميع تحذيرات العضو ${member} بنجاح.`);
        } else {
            await interaction.followup.send({ content: `ℹ️ | العضو ${member} ليس لديه تحذيرات مسجلة أصلاً.`, ephemeral: true });
        }
    },

    async handleBan(interaction) {
        await interaction.deferReply();
        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        try {
            await member.ban({ reason });
            await interaction.followup.send(`تم حظر العضو ${member} بنجاح 🚷 (السبب: ${reason})`);
        } catch (e) {
            await interaction.followup.send({ content: `فشل الحظر: تأكد أن رتبة البوت أعلى من العضو المستهدف. ❌`, ephemeral: true });
        }
    },

    async handleUnban(interaction) {
        await interaction.deferReply();
        const userId = interaction.options.getString('user_id');
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        try {
            const user = await interaction.client.users.fetch(userId);
            await interaction.guild.members.unban(user, reason);
            await interaction.followup.send(`✅ | تم رفع الحظر عن العضو \`${user.tag}\` بنجاح.`);
        } catch (e) {
            await interaction.followup.send({ content: `❌ | فشل رفع الحظر، تأكد من صحة الآيدي (ID) أو صلاحيات البوت: \`${e.message}\``, ephemeral: true });
        }
    },

    async handleKick(interaction) {
        await interaction.deferReply();
        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        try {
            await member.kick(reason);
            await interaction.followup.send(`تم طرد العضو ${member} بنجاح 👢 (السبب: ${reason})`);
        } catch (e) {
            await interaction.followup.send({ content: `فشل الطرد: تأكد من صلاحيات البوت. ❌`, ephemeral: true });
        }
    },

    async handleTimeout(interaction) {
        await interaction.deferReply();
        const member = interaction.options.getMember('member');
        let timeInput = interaction.options.getString('time_input').toLowerCase().trim();
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        try {
            let minutes = 0;
            if (/^\d+$/.test(timeInput)) {
                minutes = parseInt(timeInput);
            } else if (timeInput.endsWith('m')) {
                minutes = parseInt(timeInput.slice(0, -1));
            } else if (timeInput.endsWith('h')) {
                minutes = parseInt(timeInput.slice(0, -1)) * 60;
            } else if (timeInput.endsWith('d')) {
                minutes = parseInt(timeInput.slice(0, -1)) * 1440;
            } else {
                await interaction.followup.send({ content: "صيغة الوقت غير صحيحة! استعمل m للدقائق أو h للساعات أو d للأيام ❌", ephemeral: true });
                return;
            }

            const duration = minutes * 60 * 1000;
            await member.timeout(duration, reason);
            await interaction.followup.send(`تم إعطاء تايم أوت للعضو ${member} لمدة \`${minutes} دقائق\` ✅`);
        } catch (e) {
            await interaction.followup.send({ content: `حدث خطأ: \`${e.message}\``, ephemeral: true });
        }
    },

    async handleUntimeout(interaction) {
        await interaction.deferReply();
        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        try {
            await member.timeout(null, reason);
            await interaction.followup.send(`✅ | تم إزالة التايم أوت عن العضو ${member} بنجاح.`);
        } catch (e) {
            await interaction.followup.send({ content: `❌ | حدث خطأ أثناء إزالة التايم أوت: \`${e.message}\``, ephemeral: true });
        }
    },

    async handleMute(interaction) {
        await interaction.deferReply();
        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        try {
            if (member.voice.channel) {
                await member.edit({ mute: true, reason });
                await interaction.followup.send(`🔇 | تم كتم العضو ${member} صوتياً بنجاح.`);
            } else {
                await interaction.followup.send({ content: `⚠️ | العضو ${member} ليس متصلاً بأي روم صوتي حالياً.`, ephemeral: true });
            }
        } catch (e) {
            await interaction.followup.send({ content: `❌ | فشل كتم العضو صوتياً: \`${e.message}\``, ephemeral: true });
        }
    },

    async handleUnmute(interaction) {
        await interaction.deferReply();
        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "لا يوجد سبب";
        try {
            if (member.voice.channel) {
                await member.edit({ mute: false, reason });
                await interaction.followup.send(`🔊 | تم رفع الكتم الصوتي عن العضو ${member} بنجاح.`);
            } else {
                await interaction.followup.send({ content: `⚠️ | العضو ${member} ليس متصلاً بأي روم صوتي حالياً.`, ephemeral: true });
            }
        } catch (e) {
            await interaction.followup.send({ content: `❌ | فشل رفع الكتم الصوتي: \`${e.message}\``, ephemeral: true });
        }
    }
};
