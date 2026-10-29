const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const BOOST_DATA_FILE = path.join(__dirname, '../boost_data.json');

function loadBoostData() {
    if (fs.existsSync(BOOST_DATA_FILE)) {
        try {
            const data = fs.readFileSync(BOOST_DATA_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return {};
        }
    }
    return {};
}

function saveBoostData(data) {
    try {
        fs.writeFileSync(BOOST_DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ بيانات البوست:", error);
    }
}

function getGuildBoost(guildId) {
    const data = loadBoostData();
    if (!data[guildId]) {
        data[guildId] = {
            channel_id: null,
            message: "عاشت ايدك {member} على دعمك للسيرفر وعمل Boost!",
            image_url: null
        };
    }
    return data[guildId];
}

function updateGuildBoost(guildId, guildData) {
    const data = loadBoostData();
    data[guildId] = guildData;
    saveBoostData(data);
}

module.exports = {
    boostSetupCommand: new SlashCommandBuilder()
        .setName('boost_setup')
        .setDescription('تعيين روم إعلانات بوست السيرفر لهذا السيرفر')
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('روم الإعلانات')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    boostMessageCommand: new SlashCommandBuilder()
        .setName('boost_message')
        .setDescription('تعديل رسالة البوست (استخدم {member} للمنشن)')
        .addStringOption(option =>
            option.setName('message')
                .setDescription('الرسالة الجديدة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    boostImageCommand: new SlashCommandBuilder()
        .setName('boost_image')
        .setDescription('تعديل صورة البوست')
        .addStringOption(option =>
            option.setName('image_url')
                .setDescription('رابط الصورة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    testBoostCommand: new SlashCommandBuilder()
        .setName('test_boost')
        .setDescription('تجربة رسالة البوست لنفسك')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleBoostSetup(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const guildId = interaction.guildId;
        const channel = interaction.options.getChannel('channel');
        
        const gData = getGuildBoost(guildId);
        gData.channel_id = channel.id;
        updateGuildBoost(guildId, gData);

        await interaction.followup.send({ content: `✅ تم ضبط روم إعلانات البوست في هذا السيرفر: ${channel}`, ephemeral: true });
    },

    async handleBoostMessage(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const guildId = interaction.guildId;
        const messageText = interaction.options.getString('message');

        const gData = getGuildBoost(guildId);
        gData.message = messageText;
        updateGuildBoost(guildId, gData);

        await interaction.followup.send({ content: "✅ تم تحديث رسالة البوست في هذا السيرفر بنجاح!", ephemeral: true });
    },

    async handleBoostImage(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const guildId = interaction.guildId;
        const imageUrl = interaction.options.getString('image_url');

        const gData = getGuildBoost(guildId);
        gData.image_url = imageUrl;
        updateGuildBoost(guildId, gData);

        await interaction.followup.send({ content: "✅ تم تحديث صورة البوست في هذا السيرفر بنجاح!", ephemeral: true });
    },

    async handleTestBoost(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const guildId = interaction.guildId;
        const gData = getGuildBoost(guildId);

        const formattedMsg = gData.message.replace(/\{member\}/g, interaction.user.toString());
        const embed = new EmbedBuilder()
            .setDescription(formattedMsg)
            .setColor(0x800080);

        if (gData.image_url) {
            embed.setImage(gData.image_url);
        }

        await interaction.followup.send({ embeds: [embed], ephemeral: true });
    },

    async handleMemberUpdate(before, after) {
        const guildId = after.guild.id;
        const gData = getGuildBoost(guildId);

        if (!gData.channel_id) return;

        if (before.premiumSince === null && after.premiumSince !== null) {
            const channel = after.guild.channels.cache.get(gData.channel_id);
            if (channel) {
                const formattedMsg = gData.message.replace(/\{member\}/g, after.toString());
                const embed = new EmbedBuilder()
                    .setDescription(formattedMsg)
                    .setColor(0x800080);

                if (gData.image_url) {
                    embed.setImage(gData.image_url);
                }

                await channel.send({ content: `${after}`, embeds: [embed] }).catch(() => {});
            }
        }
    }
};
