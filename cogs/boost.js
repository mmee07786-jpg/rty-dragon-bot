const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const BOOST_DATA_FILE = path.join(__dirname, '../boost_data.json');

// لمنع إرسال نفس إعلان البوست مرتين
const recentBoosts = new Set();

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

function buildBoostEmbed(gData, memberMention) {
    const formattedMsg = gData.message.replace(/\{member\}/g, memberMention);
    const embed = new EmbedBuilder()
        .setDescription(formattedMsg)
        .setColor(0x800080);

    if (gData.image_url && /^https?:\/\//i.test(gData.image_url)) {
        embed.setImage(gData.image_url);
    }
    return embed;
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

        await interaction.editReply({ content: `✅ تم ضبط روم إعلانات البوست في هذا السيرفر: ${channel}` });
    },

    async handleBoostMessage(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const guildId = interaction.guildId;
        const messageText = interaction.options.getString('message');

        const gData = getGuildBoost(guildId);
        gData.message = messageText;
        updateGuildBoost(guildId, gData);

        await interaction.editReply({ content: "✅ تم تحديث رسالة البوست في هذا السيرفر بنجاح!" });
    },

    async handleBoostImage(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const guildId = interaction.guildId;
        const imageUrl = interaction.options.getString('image_url').trim();

        if (!/^https?:\/\//i.test(imageUrl)) {
            await interaction.editReply({ content: "❌ الرابط لازم يبدأ بـ http أو https" });
            return;
        }

        const gData = getGuildBoost(guildId);
        gData.image_url = imageUrl;
        updateGuildBoost(guildId, gData);

        await interaction.editReply({ content: "✅ تم تحديث صورة البوست في هذا السيرفر بنجاح!" });
    },

    async handleTestBoost(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const gData = getGuildBoost(interaction.guildId);
        const embed = buildBoostEmbed(gData, interaction.user.toString());

        await interaction.editReply({ embeds: [embed] });
    },

    async handleMemberUpdate(before, after) {
        // العضو لازم يكون عنده بوست حالياً
        if (!after.premiumSinceTimestamp) return;

        // نعتبره بوست جديد فقط إذا بدأ قبل أقل من دقيقتين (هذا يمنع الإعلان عن البوستات القديمة)
        if (Date.now() - after.premiumSinceTimestamp > 2 * 60 * 1000) return;

        // إذا كنا نعرف حالته قبل وكان عنده بوست، ما نعلن مرة ثانية
        if (before && before.premiumSinceTimestamp) return;

        const key = `${after.guild.id}-${after.id}-${after.premiumSinceTimestamp}`;
        if (recentBoosts.has(key)) return;
        recentBoosts.add(key);
        setTimeout(() => recentBoosts.delete(key), 10 * 60 * 1000);

        const gData = getGuildBoost(after.guild.id);
        if (!gData.channel_id) return;

        const channel = after.guild.channels.cache.get(gData.channel_id)
            || await after.guild.channels.fetch(gData.channel_id).catch(() => null);
        if (!channel) return;

        const embed = buildBoostEmbed(gData, after.toString());
        await channel.send({ content: `${after}`, embeds: [embed] }).catch(e => {
            console.error("تعذر إرسال إعلان البوست:", e.message);
        });
    }
};
