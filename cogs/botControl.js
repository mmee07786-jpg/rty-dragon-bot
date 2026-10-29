const { 
    EmbedBuilder, 
    ActionRowBuilder, 
    StringSelectMenuBuilder,
    ButtonBuilder,
    ButtonStyle
} = require('discord.js');
const fs = require('fs');
const path = require('path');

const OWNER_ID = "1107355943408259112";
const CONTROL_FILE = path.join(__dirname, '../bot_control.json');

function loadControlData() {
    if (fs.existsSync(CONTROL_FILE)) {
        try {
            return JSON.parse(fs.readFileSync(CONTROL_FILE, 'utf8'));
        } catch (e) {
            return { disabled_guilds: [] };
        }
    }
    return { disabled_guilds: [] };
}

function saveControlData(data) {
    fs.writeFileSync(CONTROL_FILE, JSON.stringify(data, null, 4), 'utf8');
}

module.exports = {
    isGuildDisabled(guildId) {
        if (!guildId) return false;
        const data = loadControlData();
        return data.disabled_guilds.includes(guildId);
    },

    async handleJJCommand(message, client) {
        if (message.author.id !== OWNER_ID) return;

        if (client.guilds.cache.size === 0) {
            await message.channel.send("عيوني فهد، أنا لست منضماً إلى أي سيرفر حالياً.");
            return;
        }

        const guilds = Array.from(client.guilds.cache.values()).slice(0, 25);
        const data = loadControlData();

        const options = guilds.map(g => {
            const isDisabled = data.disabled_guilds.includes(g.id);
            return {
                label: g.name.substring(0, 100),
                value: g.id,
                description: isDisabled ? "🔴 البوت متوقف حالياً في هذا السيرفر" : "🟢 البوت يعمل بشكل طبيعي",
                emoji: isDisabled ? "🔴" : "🟢"
            };
        });

        const selectMenu = new StringSelectMenuBuilder()
            .setCustomId("bot_control_guild_select")
            .setPlaceholder("اختر السيرفر للتحكم بحالة عمل البوت فيه...")
            .addOptions(options);

        const row = new ActionRowBuilder().addComponents(selectMenu);

        const embed = new EmbedBuilder()
            .setTitle("🛑 | لوحة التحكم الطارئة بإيقاف/تشغيل البوت")
            .setDescription("اختر السيرفر من القائمة أدناه لتعطيل البوت فيه بالكامل أو إرجاع عمله:")
            .setColor(0xFF0000);

        const sentMsg = await message.channel.send({ embeds: [embed], components: [row] });
        setTimeout(() => sentMsg.delete().catch(() => {}), 180 * 1000);
    },

    async handleInteraction(interaction, client) {
        if (!interaction.isStringSelectMenu() && !interaction.isButton()) return;

        if (interaction.customId === "bot_control_guild_select") {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، هذا الأمر خاص بفهد فقط!", ephemeral: true });
                return;
            }

            // منع انتهاء مهلة ديسكورد عبر استخدام deferReply فوراً
            await interaction.deferReply({ ephemeral: true });

            const guildId = interaction.values[0];
            const guild = client.guilds.cache.get(guildId);
            if (!guild) {
                await interaction.followup({ content: "❌ | السيرفر غير موجود.", ephemeral: true });
                return;
            }

            const data = loadControlData();
            const isDisabled = data.disabled_guilds.includes(guildId);

            const statusText = isDisabled ? "متوقف حالياً 🔴" : "يعمل حالياً 🟢";
            const actionText = isDisabled ? "هل تريد إعادة تشغيل البوت في هذا السيرفر؟" : "هل تريد إيقاف البوت تماماً عن العمل في هذا السيرفر؟";

            const row = new ActionRowBuilder().addComponents(
                new ButtonBuilder()
                    .setCustomId(`bot_toggle_${guildId}`)
                    .setLabel(isDisabled ? "تفعيل البوت 🟢" : "إيقاف البوت 🔴")
                    .setStyle(isDisabled ? ButtonStyle.Success : ButtonStyle.Danger)
            );

            await interaction.followup({
                content: `🏰 **السيرفر:** ${guild.name}\n📊 **الحالة الحالية:** ${statusText}\n\n${actionText}`,
                components: [row],
                ephemeral: true
            });
        }

        else if (interaction.customId.startsWith("bot_toggle_")) {
            if (interaction.user.id !== OWNER_ID) {
                await interaction.reply({ content: "عذراً، هذا الأمر خاص بفهد فقط!", ephemeral: true });
                return;
            }

            await interaction.deferUpdate(); // تحديث فوري للأزرار بدون أخطاء

            const guildId = interaction.customId.split("_")[2];
            const data = loadControlData();
            let isDisabled = data.disabled_guilds.includes(guildId);

            if (isDisabled) {
                data.disabled_guilds = data.disabled_guilds.filter(id => id !== guildId);
                saveControlData(data);
                await interaction.editReply({ content: "✅ | تم إعادة تفعيل البوت بنجاح في هذا السيرفر وعاد للعمل!", components: [] });
            } else {
                data.disabled_guilds.push(guildId);
                saveControlData(data);
                await interaction.editReply({ content: "🛑 | تم إيقاف البوت تماماً في هذا السيرفر ولن يستجيب لأي أمر أو رسالة بعد الآن!", components: [] });
            }
        }
    }
};
