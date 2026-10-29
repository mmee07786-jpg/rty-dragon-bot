const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

module.exports = {
    clearCommand: new SlashCommandBuilder()
        .setName('clear')
        .setDescription('[ Admin Only ] حذف عدد محدد من الرسائل الحديثة (من 1 إلى 1000)')
        .addIntegerOption(option =>
            option.setName('amount')
                .setDescription('عدد الرسائل المراد حذفها (بين 1 و 1000)')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages),

    async handleClear(interaction) {
        const amount = interaction.options.getInteger('amount');

        if (amount < 1 || amount > 1000) {
            await interaction.reply({ content: "❌ | يرجى إدخال عدد يتراوح بين **1** و **1000** رسالة فقط!", ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });
        await new Promise(resolve => setTimeout(resolve, 1000));

        try {
            // حساب تاريخ قبل 14 يوم حسب نظام ديسكورد لتجنب الخطأ 50034
            const fourteenDaysAgo = Date.now() - (14 * 24 * 60 * 60 * 1000);

            const fetchedMessages = await interaction.channel.messages.fetch({ limit: Math.min(amount + 10, 100) });
            const messagesToDelete = [];

            fetchedMessages.forEach(msg => {
                if (msg.createdTimestamp >= fourteenDaysAgo && messagesToDelete.length < amount) {
                    messagesToDelete.push(msg);
                }
            });

            if (messagesToDelete.length === 0) {
                await interaction.followup({ content: "❌ | عذراً، لا توجد رسائل **حديثة (أقل من 14 يوم)** يمكن حذفها ضمن هذا العدد!", ephemeral: true });
                return;
            }

            // حذف الرسائل دفعة واحدة (Bulk Delete للرسائل الأقل من 14 يوم)
            await interaction.channel.bulkDelete(messagesToDelete, true);

            await interaction.followup({ content: `✅ | تم مسح \`${messagesToDelete.length}\` رسالة حديثة بنجاح وتجاوز الرسائل القديمة تلقائياً!`, ephemeral: true });

        } catch (e) {
            await interaction.followup({ content: `❌ | حدث خطأ أثناء الحذف: \`${e.message}\``, ephemeral: true });
        }
    }
};
