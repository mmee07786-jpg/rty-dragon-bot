const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

const DAY = 24 * 60 * 60 * 1000;
const BULK_DAYS = 14;   // حد ديسكورد للحذف الجماعي (ثابت ولا يتغير)
const MAX_DAYS = 30;    // أقصى عمر للرسائل اللي نحذفها

module.exports = {
    clearCommand: new SlashCommandBuilder()
        .setName('clear')
        .setDescription('[ Admin Only ] حذف عدد محدد من الرسائل (من 1 إلى 1000، حتى 30 يوم)')
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

        const channel = interaction.channel;
        if (!channel || typeof channel.bulkDelete !== 'function') {
            await interaction.reply({ content: "❌ | هذا الأمر يشتغل بالقنوات النصية فقط!", ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });

        try {
            const now = Date.now();
            const bulkLimitTs = now - BULK_DAYS * DAY + 60 * 1000; // أحدث من 14 يوم = حذف جماعي
            const maxTs = now - MAX_DAYS * DAY;                    // أقدم من 30 يوم = نتوقف

            let remaining = amount;
            let deleted = 0;
            let lastId = null;
            let reachedEnd = false;
            let slowCount = 0; // عدد الرسائل (14-30 يوم) اللي انحذفت واحدة واحدة

            while (remaining > 0 && !reachedEnd) {
                const options = { limit: Math.min(remaining, 100) };
                if (lastId) options.before = lastId;

                const fetched = await channel.messages.fetch(options);
                if (fetched.size === 0) break;
                lastId = fetched.last().id;

                const eligible = fetched.filter(m => m.createdTimestamp > maxTs);
                if (eligible.size < fetched.size) reachedEnd = true; // وصلنا لرسائل أقدم من 30 يوم

                const recent = eligible.filter(m => m.createdTimestamp > bulkLimitTs);
                const older = eligible.filter(m => m.createdTimestamp <= bulkLimitTs);

                // 1) الحذف الجماعي للرسائل الحديثة
                if (recent.size > 0) {
                    const res = await channel.bulkDelete(recent, true);
                    deleted += res.size;
                }

                // 2) الحذف واحدة واحدة للرسائل من 14 إلى 30 يوم (أبطأ بسبب قيود ديسكورد)
                for (const msg of older.values()) {
                    try {
                        await msg.delete();
                        deleted++;
                        slowCount++;
                        if (slowCount % 20 === 0) {
                            await interaction.editReply({ content: `⏳ | جاري الحذف... تم حذف \`${deleted}\` رسالة حتى الآن.` }).catch(() => {});
                        }
                    } catch (e) {}
                }

                remaining -= eligible.size;
            }

            if (deleted === 0) {
                await interaction.editReply({ content: `❌ | ما لقيت رسائل أحدث من **${MAX_DAYS} يوم** يمكن حذفها!` });
                return;
            }

            await interaction.editReply({
                content: `✅ | تم مسح \`${deleted}\` رسالة بنجاح` + (reachedEnd ? ` (توقفت عند الرسائل الأقدم من ${MAX_DAYS} يوم).` : ".")
            });
        } catch (e) {
            console.error("خطأ في أمر clear:", e);
            await interaction.editReply({ content: `❌ | حدث خطأ أثناء الحذف: \`${e.message}\`` }).catch(() => {});
        }
    }
};
