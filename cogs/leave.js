const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../leave_data.json');

function loadLeaveData() {
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

function saveLeaveData(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ بيانات المغادرة:", error);
    }
}

function getGuildLeaveData(guildId) {
    const data = loadLeaveData();
    if (!data[guildId]) {
        data[guildId] = {
            channel_id: null,
            message: "مع السلامة {member}، ننتظر عودتك يوماً ما.",
            image_url: null
        };
    }
    return data[guildId];
}

function updateGuildLeaveData(guildId, guildData) {
    const data = loadLeaveData();
    data[guildId] = guildData;
    saveLeaveData(data);
}

module.exports = {
    leaveSetupCommand: new SlashCommandBuilder()
        .setName('leave_setup')
        .setDescription('تعيين روم رسائل المغادرة لهذا السيرفر')
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('روم المغادرة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    leaveMessageCommand: new SlashCommandBuilder()
        .setName('leave_message')
        .setDescription('تعديل رسالة المغادرة لهذا السيرفر')
        .addStringOption(option =>
            option.setName('message')
                .setDescription('الرسالة الجديدة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    leaveImageCommand: new SlashCommandBuilder()
        .setName('leave_image')
        .setDescription('تعديل صورة المغادرة لهذا السيرفر')
        .addStringOption(option =>
            option.setName('image_url')
                .setDescription('رابط الصورة')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    testLeaveCommand: new SlashCommandBuilder()
        .setName('test_leave')
        .setDescription('تجربة رسالة المغادرة لنفسك')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleLeaveSetup(interaction) {
        const guildId = interaction.guildId;
        const channel = interaction.options.getChannel('channel');

        const guildData = getGuildLeaveData(guildId);
        guildData.channel_id = channel.id;
        updateGuildLeaveData(guildId, guildData);

        await interaction.reply({ content: `✅ تم ضبط روم المغادرة بنجاح في هذا السيرفر: ${channel}`, ephemeral: true });
    },

    async handleLeaveMessage(interaction) {
        const guildId = interaction.guildId;
        const messageText = interaction.options.getString('message');

        const guildData = getGuildLeaveData(guildId);
        guildData.message = messageText;
        updateGuildLeaveData(guildId, guildData);

        await interaction.reply({ content: "✅ تم تحديث رسالة المغادرة في هذا السيرفر بنجاح!", ephemeral: true });
    },

    async handleLeaveImage(interaction) {
        const guildId = interaction.guildId;
        const imageUrl = interaction.options.getString('image_url');

        const guildData = getGuildLeaveData(guildId);
        guildData.image_url = imageUrl;
        updateGuildLeaveData(guildId, guildData);

        await interaction.reply({ content: "✅ تم تحديث صورة المغادرة في هذا السيرفر بنجاح!", ephemeral: true });
    },

    async handleTestLeave(interaction) {
        const guildId = interaction.guildId;
        const guildData = getGuildLeaveData(guildId);

        const formattedMsg = guildData.message.replace(/\{member\}/g, interaction.user.toString());
        const embed = new EmbedBuilder()
            .setDescription(formattedMsg)
            .setColor(0xFF0000);

        if (guildData.image_url) {
            embed.setImage(guildData.image_url);
        }

        await interaction.reply({ embeds: [embed], ephemeral: true });
    },

    async handleMemberRemove(member) {
        const guildId = member.guild.id;
        const guildData = getGuildLeaveData(guildId);

        const channelId = guildData.channel_id;
        if (!channelId) return;

        let channel = member.guild.channels.cache.get(channelId);
        if (!channel) {
            try {
                channel = await member.guild.channels.fetch(channelId);
            } catch (e) {
                return;
            }
        }

        if (channel) {
            const formattedMsg = guildData.message.replace(/\{member\}/g, member.toString());
            const embed = new EmbedBuilder()
                .setDescription(formattedMsg)
                .setColor(0xFF0000);

            if (guildData.image_url) {
                embed.setImage(guildData.image_url);
            }

            try {
                await channel.send({ embeds: [embed] });
            } catch (e) {}
        }
    }
};
