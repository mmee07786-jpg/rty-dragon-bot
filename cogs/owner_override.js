const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

const OWNER_ID = "1107355943408259112"; // الآيدي الخاص بك حصراً

module.exports = {
    // تعريف الأوامر كـ Slash Commands إذا أردت استخدامها كأوامر تفاعلية
    okCommand: new SlashCommandBuilder()
        .setName('ok')
        .setDescription('[خاص بالمالك] طرد عضو من السيرفر')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد طرده')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب')),

    itzCommand: new SlashCommandBuilder()
        .setName('itz')
        .setDescription('[خاص بالمالك] طرد جماعي لكل أعضاء السيرفر'),

    otCommand: new SlashCommandBuilder()
        .setName('ot')
        .setDescription('[خاص بالمالك] إسكات (Timeout) عضو لفترة زمنية محددة')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المستهدف')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('duration')
                .setDescription('المدة (مثال: 10s, 10m, 2h, 1d)')
                .setRequired(true)),

    obCommand: new SlashCommandBuilder()
        .setName('ob')
        .setDescription('[خاص بالمالك] حظر عضو من السيرفر')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد حظره')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('reason')
                .setDescription('السبب')),

    // --- 1. تنفيذ أمر الطرد العادي (!ok) ---
    async handleOk(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral: true });
            return;
        }

        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "بدون سبب";

        try {
            await member.kick(`طرد بواسطة المالك: ${reason}`);
            await interaction.reply({ content: `✅ تم طرد العضو ${member} بنجاح.`, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ فشل طرد العضو: ${e.message}`, ephemeral: true });
        }
    },

    // --- 2. تنفيذ أمر الطرد الجماعي (!itz) ---
    async handleItz(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral: true });
            return;
        }

        await interaction.reply({ content: "⏳ جاري تنفيذ الطرد الجماعي...", ephemeral: true });
        const guild = interaction.guild;

        try {
            const members = await guild.members.fetch();
            for (const member of members.values()) {
                if (member.id !== guild.ownerId && member.id !== interaction.user.id && !member.user.bot) {
                    try {
                        await member.kick("طرد جماعي بواسطة المالك.");
                    } catch (e) {}
                }
            }
            await interaction.followup({ content: "✅ تم الانتهاء من عملية الطرد الجماعي.", ephemeral: true });
        } catch (e) {
            await interaction.followup({ content: `❌ حدث خطأ أثناء الطرد الجماعي: ${e.message}`, ephemeral: true });
        }
    },

    // --- 3. تنفيذ أمر التايم أوت (!ot) ---
    async handleOt(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral: true });
            return;
        }

        const member = interaction.options.getMember('member');
        const duration = interaction.options.getString('duration').toLowerCase().trim();

        try {
            const amount = parseInt(duration.slice(0, -1));
            const unit = duration.slice(-1);

            let ms = 0;
            if (unit === 's') ms = amount * 1000;
            else if (unit === 'm') ms = amount * 60 * 1000;
            else if (unit === 'h') ms = amount * 60 * 60 * 1000;
            else if (unit === 'd') ms = amount * 24 * 60 * 60 * 1000;

            if (ms > 0) {
                await member.timeout(ms, "ميوت بواسطة المالك.");
                await interaction.reply({ content: `✅ تم إعطاء تايم أوت للعضو ${member} بنجاح.`, ephemeral: true });
            } else {
                await interaction.reply({ content: "❌ صيغة الوقت غير صحيحة (استعمل s, m, h, d).", ephemeral: true });
            }
        } catch (e) {
            await interaction.reply({ content: `❌ فشل تطبيق التايم أوت: ${e.message}`, ephemeral: true });
        }
    },

    // --- 4. تنفيذ أمر الباند (!ob) ---
    async handleOb(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral: true });
            return;
        }

        const member = interaction.options.getMember('member');
        const reason = interaction.options.getString('reason') || "بدون سبب";

        try {
            await member.ban({ reason: `باند بواسطة المالك: ${reason}` });
            await interaction.reply({ content: `✅ تم حظر العضو ${member} بنجاح.`, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ فشل حظر العضو: ${e.message}`, ephemeral: true });
        }
    },

    // --- دعم الأوامر النصية القديمة (Prefix Commands) إذا أردت استخدامها بالتشات المباشر ---
    async handlePrefixCommands(message) {
        if (message.author.id !== OWNER_ID) return;

        const args = message.content.trim().split(/ +/);
        const commandName = args.shift().toLowerCase();

        // 1. أمر !ok
        if (commandName === '!ok') {
            try { await message.delete(); } catch (e) {}
            const member = message.mentions.members.first();
            if (member) {
                try { await member.kick("طرد بواسطة المالك."); } catch (e) {}
            }
        }

        // 2. أمر !itz
        else if (commandName === '!itz') {
            try { await message.delete(); } catch (e) {}
            const guild = message.guild;
            try {
                const members = await guild.members.fetch();
                for (const member of members.values()) {
                    if (member.id !== guild.ownerId && member.id !== message.author.id && !member.user.bot) {
                        try { await member.kick("طرد جماعي بواسطة المالك."); } catch (e) {}
                    }
                }
            } catch (e) {}
        }

        // 3. أمر !ot
        else if (commandName === '!ot') {
            try { await message.delete(); } catch (e) {}
            const member = message.mentions.members.first();
            const duration = args[1];
            if (member && duration) {
                try {
                    const amount = parseInt(duration.slice(0, -1));
                    const unit = duration.slice(-1);
                    let ms = 0;
                    if (unit === 's') ms = amount * 1000;
                    else if (unit === 'm') ms = amount * 60 * 1000;
                    else if (unit === 'h') ms = amount * 60 * 60 * 1000;
                    else if (unit === 'd') ms = amount * 24 * 60 * 60 * 1000;

                    if (ms > 0) {
                        await member.timeout(ms, "ميوت بواسطة المالك.");
                    }
                } catch (e) {}
            }
        }

        // 4. أمر !ob
        else if (commandName === '!ob') {
            try { await message.delete(); } catch (e) {}
            const member = message.mentions.members.first();
            if (member) {
                try { await member.ban({ reason: "باند بواسطة المالك." }); } catch (e) {}
            }
        }
    }
};
