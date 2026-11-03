const { SlashCommandBuilder, PermissionFlagsBits, ActionRowBuilder, StringSelectMenuBuilder, ButtonBuilder, ButtonStyle, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');

const OWNER_ID = "1107355943408259112";
const BACKUP_FILE = path.join(__dirname, '../server_backup.json');

class ServerSelectView extends ActionRowBuilder {
    constructor(bot, authorId) {
        super();
        this.bot = bot;
        this.authorId = authorId;
        const options = [];
        bot.guilds.cache.forEach(guild => {
            const name = guild.name.length > 97 ? guild.name.substring(0, 97) + "..." : guild.name;
            options.push({ label: name, value: guild.id });
        });
        const selectMenu = new StringSelectMenuBuilder()
            .setCustomId('server_select')
            .setPlaceholder('اختر السيرفر المراد نسخ محتواه...')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(options.slice(0, 25));
        this.addComponents(selectMenu);
    }
}

class ConfirmView extends ActionRowBuilder {
    constructor(authorId) {
        super();
        this.authorId = authorId;
        const confirmBtn = new ButtonBuilder().setCustomId('confirm_btn').setLabel('موافقة').setEmoji('✅').setStyle(ButtonStyle.Success);
        const cancelBtn = new ButtonBuilder().setCustomId('cancel_btn').setLabel('إلغاء').setEmoji('❌').setStyle(ButtonStyle.Danger);
        this.addComponents(confirmBtn, cancelBtn);
    }
}

module.exports = {
    async handleReady() {
        console.log("🛡 | نظام النسخ الاحتياطي والأمر السري !my جاهز للعمل.");
    },

    serializeOverwrites(guild, channel) {
        const overwritesData = {};
        channel.permissionOverwrites.cache.forEach(overwrite => {
            const targetId = overwrite.id;
            let targetType = null;
            let targetName = "";
            const role = guild.roles.cache.get(targetId);
            if (role) {
                targetType = "role";
                targetName = role.name;
            } else {
                const member = guild.members.cache.get(targetId);
                if (member) {
                    targetType = "member";
                    targetName = member.user.username;
                } else {
                    return;
                }
            }
            overwritesData[targetId] = {
                name: targetName,
                type: targetType,
                allow: overwrite.allow.bitfield.toString(),
                deny: overwrite.deny.bitfield.toString()
            };
        });
        return overwritesData;
    },

    applyOverwrites(guild, channelData) {
        const overwrites = {};
        const roleMap = new Map();
        guild.roles.cache.forEach(role => roleMap.set(role.name.trim().toLowerCase(), role));

        const overwritesObj = channelData.overwrites || {};
        for (const [targetIdStr, owData] of Object.entries(overwritesObj)) {
            try {
                let target = null;
                const targetType = owData.type;
                const targetName = (owData.name || "").trim().toLowerCase();
                if (targetType === "role") {
                    target = guild.roles.cache.get(targetIdStr) || roleMap.get(targetName);
                } else if (targetType === "member") {
                    target = guild.members.cache.get(targetIdStr);
                }
                if (target) {
                    overwrites[target.id] = {
                        id: target.id,
                        type: targetType === "role" ? 0 : 1,
                        allow: owData.allow,
                        deny: owData.deny
                    };
                }
            } catch (e) {}
        }
        return Object.values(overwrites);
    },

    async handleMyCommand(message) {
        if (message.author.id !== OWNER_ID) return;
        try { await message.delete(); } catch (e) {}

        const view = new ServerSelectView(message.client, message.author.id);
        const msg = await message.channel.send({ content: "🌐 | **اختر السيرفر الذي تريد نسخ الرتب والأقسام والرومات منه:**", components: [view] });

        try {
            const filter = i => i.user.id === message.author.id;
            const selection = await msg.awaitMessageComponent({ filter, time: 60000 });
            if (!selection.isStringSelectMenu()) return;
            const selectedGuildId = selection.values[0];
            await selection.deferUpdate();

            const sourceGuild = message.client.guilds.cache.get(selectedGuildId);
            if (!sourceGuild) {
                await msg.edit({ content: "❌ لم يتم العثور على السيرفر المحدد.", components: [] });
                return;
            }

            const confirmView = new ConfirmView(message.author.id);
            await msg.edit({ content: `⚠️ | **تريد تسوي لصق هنا؟** (سيرفر المصدر: **${sourceGuild.name}**)`, components: [confirmView] });

            const confirmSelection = await msg.awaitMessageComponent({ filter, time: 60000 });
            if (confirmSelection.customId === 'cancel_btn') {
                await confirmSelection.deferUpdate();
                await msg.edit({ content: "❌ تم إلغاء عملية اللصق بناءً على رغبتك.", components: [] });
                return;
            }

            await confirmSelection.deferUpdate();
            const targetGuild = message.guild;
            await msg.edit({ content: `⏳ | **جاري نقل ولصق محتويات سيرفر (${sourceGuild.name})...**`, components: [] });

            const existingRoles = new Set(targetGuild.roles.cache.map(r => r.name.trim().toLowerCase()));
            for (const role of Array.from(sourceGuild.roles.cache.values()).reverse()) {
                if (role.managed || role.id === sourceGuild.id || existingRoles.has(role.name.trim().toLowerCase())) continue;
                try {
                    await targetGuild.roles.create({ name: role.name, permissions: role.permissions, color: role.color, hoist: role.hoist, mentionable: role.mentionable });
                    existingRoles.add(role.name.trim().toLowerCase());
                    await new Promise(res => setTimeout(res, 1200));
                } catch (e) {}
            }

            const existingCategories = new Map();
            targetGuild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).forEach(c => existingCategories.set(c.name.trim().toLowerCase(), c));
            const existingChannels = new Set(targetGuild.channels.cache.map(c => c.name.trim().toLowerCase()));

            for (const channel of sourceGuild.channels.cache.values()) {
                if (!channel.parent && (channel.type === ChannelType.GuildText || channel.type === ChannelType.GuildVoice)) {
                    if (existingChannels.has(channel.name.trim().toLowerCase())) continue;
                    try {
                        if (channel.type === ChannelType.GuildText) {
                            await targetGuild.channels.create({ name: channel.name, type: ChannelType.GuildText, topic: channel.topic, rateLimitPerUser: channel.rateLimitPerUser, nsfw: channel.nsfw });
                        } else {
                            await targetGuild.channels.create({ name: channel.name, type: ChannelType.GuildVoice, bitrate: channel.bitrate, userLimit: channel.userLimit });
                        }
                        existingChannels.add(channel.name.trim().toLowerCase());
                        await new Promise(res => setTimeout(res, 1200));
                    } catch (e) {}
                }
            }

            await message.channel.send(`✅ **تمت عملية نقل ولصق كافة الرتب والأقسام والرومات بنجاح!**`);
        } catch (e) {
            await message.channel.send(`❌ انتهى الوقت أو حدث خطأ: ${e.message}`);
        }
    },

    backupServerCommand: new SlashCommandBuilder()
        .setName('backup')
        .setDescription('أخذ نسخة احتياطية مطابقة للسيرفر')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    restoreServerCommand: new SlashCommandBuilder()
        .setName('restore')
        .setDescription('استعادة السيرفر من النسخة الاحتياطية')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleBackup(interaction) {
        // الاستجابة الفورية لمنع خطأ The application did not respond
        await interaction.deferReply({ ephemeral: false });
        const guild = interaction.guild;

        try {
            if (fs.existsSync(BACKUP_FILE)) fs.unlinkSync(BACKUP_FILE);

            const rolesData = [];
            Array.from(guild.roles.cache.values()).reverse().forEach(role => {
                if (!role.managed && role.id !== guild.id) {
                    rolesData.push({
                        name: role.name,
                        permissions: role.permissions.bitfield.toString(),
                        color: role.color,
                        hoist: role.hoist,
                        mentionable: role.mentionable,
                        position: role.position
                    });
                }
            });

            const categoriesData = [];
            const noCategoryChannels = [];

            guild.channels.cache.forEach(channel => {
                if (!channel.parent) {
                    if (channel.type === ChannelType.GuildText || channel.type === ChannelType.GuildVoice) {
                        noCategoryChannels.push({
                            name: channel.name,
                            type: channel.type === ChannelType.GuildText ? "text" : "voice",
                            topic: channel.topic,
                            slowmode: channel.rateLimitPerUser,
                            nsfw: channel.nsfw,
                            bitrate: channel.bitrate,
                            user_limit: channel.userLimit,
                            overwrites: module.exports.serializeOverwrites(guild, channel)
                        });
                    }
                }
            });

            if (noCategoryChannels.length > 0) {
                categoriesData.push({ name: "بدون قسم", channels: noCategoryChannels });
            }

            guild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).forEach(category => {
                const catChannels = [];
                category.children.cache.forEach(channel => {
                    if (channel.type === ChannelType.GuildText || channel.type === ChannelType.GuildVoice) {
                        catChannels.push({
                            name: channel.name,
                            type: channel.type === ChannelType.GuildText ? "text" : "voice",
                            topic: channel.topic,
                            slowmode: channel.rateLimitPerUser,
                            nsfw: channel.nsfw,
                            bitrate: channel.bitrate,
                            user_limit: channel.userLimit,
                            overwrites: module.exports.serializeOverwrites(guild, channel)
                        });
                    }
                });
                categoriesData.push({ name: category.name, overwrites: module.exports.serializeOverwrites(guild, category), channels: catChannels });
            });

            const backupDict = { guild_name: guild.name, roles: rolesData, categories: categoriesData };
            fs.writeFileSync(BACKUP_FILE, JSON.stringify(backupDict, null, 4), 'utf8');

            const totalChannels = categoriesData.reduce((acc, cat) => acc + cat.channels.length, 0);
            await interaction.editReply({
                content: `✅ **تمت عملية النسخ الاحتياطي بنجاح!**\n- الرتب: **${rolesData.length}**\n- الرومات والأقسام: **${totalChannels}**`
            });
        } catch (e) {
            await interaction.editReply({ content: `❌ حدث خطأ أثناء النسخ: ${e.message}` });
        }
    },

    async handleRestore(interaction) {
        if (!fs.existsSync(BACKUP_FILE)) {
            await interaction.reply({ content: "❌ لا توجد نسخة احتياطية محفوظة!", ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });
        const guild = interaction.guild;

        try {
            const backupData = JSON.parse(fs.readFileSync(BACKUP_FILE, 'utf8'));
            const existingRoleNames = new Set(guild.roles.cache.map(r => r.name.trim().toLowerCase()));

            for (const rData of backupData.roles) {
                if (!existingRoleNames.has(rData.name.trim().toLowerCase())) {
                    try {
                        await guild.roles.create({
                            name: rData.name,
                            permissions: BigInt(rData.permissions),
                            color: rData.color,
                            hoist: rData.hoist,
                            mentionable: rData.mentionable
                        });
                        existingRoleNames.add(rData.name.trim().toLowerCase());
                        await new Promise(res => setTimeout(res, 1000));
                    } catch (e) {}
                }
            }

            const existingCategories = new Map();
            guild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).forEach(c => existingCategories.set(c.name.trim().toLowerCase(), c));
            const existingChannels = new Set(guild.channels.cache.map(c => c.name.trim().toLowerCase()));

            for (const catData of backupData.categories) {
                let categoryObj = null;
                const catName = catData.name.trim();

                if (catName !== "بدون قسم") {
                    categoryObj = existingCategories.get(catName.toLowerCase());
                    if (!categoryObj) {
                        try {
                            categoryObj = await guild.channels.create({
                                name: catName,
                                type: ChannelType.GuildCategory,
                                permissionOverwrites: module.exports.applyOverwrites(guild, catData)
                            });
                            existingCategories.set(catName.toLowerCase(), categoryObj);
                            await new Promise(res => setTimeout(res, 1200));
                        } catch (e) { continue; }
                    }
                }

                for (const chData of catData.channels) {
                    if (!existingChannels.has(chData.name.trim().toLowerCase())) {
                        try {
                            await guild.channels.create({
                                name: chData.name,
                                type: chData.type === "text" ? ChannelType.GuildText : ChannelType.GuildVoice,
                                parent: categoryObj ? categoryObj.id : null,
                                topic: chData.topic,
                                rateLimitPerUser: chData.slowmode || 0,
                                nsfw: chData.nsfw || false,
                                bitrate: chData.bitrate || 64000,
                                userLimit: chData.user_limit || 0,
                                permissionOverwrites: module.exports.applyOverwrites(guild, chData)
                            });
                            existingChannels.add(chData.name.trim().toLowerCase());
                            await new Promise(res => setTimeout(res, 1000));
                        } catch (e) {}
                    }
                }
            }

            await interaction.editReply({ content: `✅ **تمت استعادة النسخة الاحتياطية بنجاح تام وبدون تكرار!**` });
        } catch (e) {
            await interaction.editReply({ content: `❌ حدث خطأ أثناء الاستعادة: ${e.message}` });
        }
    }
};
