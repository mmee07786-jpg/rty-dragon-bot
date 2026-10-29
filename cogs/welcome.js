const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const WELCOME_DATA_FILE = path.join(__dirname, '../welcome_data.json');

function loadWelcomeData() {
    if (fs.existsSync(WELCOME_DATA_FILE)) {
        try {
            const data = fs.readFileSync(WELCOME_DATA_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return {};
        }
    }
    return {};
}

function saveWelcomeData(data) {
    try {
        fs.writeFileSync(WELCOME_DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ بيانات الترحيب:", error);
    }
}

function getGuildWelcome(guildId) {
    const data = loadWelcomeData();
    if (!data[guildId]) {
        data[guildId] = {
            channel_id: null,
            message: "منورنا يا {member}, نتمنى لك أوقات ممتعة معنا.",
            image_url: null
        };
    }
    return data[guildId];
}

function updateGuildWelcome(guildId, guildData) {
    const data = loadWelcomeData();
    data[guildId] = guildData;
    saveWelcomeData(data);
}

module.exports = {
    welcomeSetupCommand: new SlashCommandBuilder()
        .setName('welcome_setup')
        .setDescription('تعيين روم الترحيب بالأعضاء الجدد لهذا السيرفر')
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('روم الترحيب')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    welcomeMessageCommand: new SlashCommandBuilder()
        .setName('welcome_message')
        .setDescription('تعديل رسالة الترحيب (استخدم {member} للمنشن)')
        .addStringOption(option =>
            option.setName('message')
                .setDescription('الرسالة الجديدة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    welcomeImageCommand: new SlashCommandBuilder()
        .setName('welcome_image')
        .setDescription('تعديل رابط صورة الترحيب')
        .addStringOption(option =>
            option.setName('image_url')
                .setDescription('رابط الصورة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    testWelcomeCommand: new SlashCommandBuilder()
        .setName('test_welcome')
        .setDescription('تجربة رسالة الترحيب لنفسك')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleWelcomeSetup(interaction) {
        const guildId = interaction.guildId;
        const channel = interaction.options.getChannel('channel');

        const gData = getGuildWelcome(guildId);
        gData.channel_id = channel.id;
        updateGuildWelcome(guildId, gData);

        await interaction.reply({ content: `✅ تم ضبط روم الترحيب بنجاح في هذا السيرفر: ${channel}`, ephemeral: true });
    },

    async handleWelcomeMessage(interaction) {
        const guildId = interaction.guildId;
        const messageText = interaction.options.getString('message');

        const gData = getGuildWelcome(guildId);
        gData.message = messageText;
        updateGuildWelcome(guildId, gData);

        await interaction.reply({ content: "✅ تم تحديث رسالة الترحيب في هذا السيرفر بنجاح!", ephemeral: true });
    },

    async handleWelcomeImage(interaction) {
        const guildId = interaction.guildId;
        const imageUrl = interaction.options.getString('image_url');

        const gData = getGuildWelcome(guildId);
        gData.image_url = imageUrl;
        updateGuildWelcome(guildId, gData);

        await interaction.reply({ content: "✅ تم تحديث صورة الترحيب في هذا السيرفر بنجاح!", ephemeral: true });
    },

    async handleTestWelcome(interaction) {
        const guildId = interaction.guildId;
        const gData = getGuildWelcome(guildId);

        const formattedMsg = gData.message.replace(/\{member\}/g, interaction.user.toString());
        const embed = new EmbedBuilder()
            .setDescription(formattedMsg)
            .setColor(0x00FF00);

        if (gData.image_url) {
            embed.setImage(gData.image_url);
        }

        await interaction.reply({ content: interaction.user.toString(), embeds: [embed], ephemeral: true });
    },

    async handleMemberJoin(member) {
        const guildId = member.guild.id;
        const gData = getGuildWelcome(guildId);

        if (!gData.channel_id) return;

        let channel = member.guild.channels.cache.get(gData.channel_id);
        if (!channel) {
            try {
                channel = await member.guild.channels.fetch(gData.channel_id);
            } catch (e) {
                return;
            }
        }

        if (channel) {
            const formattedMsg = gData.message.replace(/\{member\}/g, member.toString());
            const embed = new EmbedBuilder()
                .setDescription(formattedMsg)
                .setColor(0x00FF00);

            if (gData.image_url) {
                embed.setImage(gData.image_url);
            }

            try {
                await channel.send({ content: member.toString(), embeds: [embed] });
            } catch (e) {}
        }
    }
};
