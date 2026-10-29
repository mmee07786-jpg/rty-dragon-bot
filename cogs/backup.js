const { SlashCommandBuilder, PermissionFlagsBits, ActionRowBuilder, StringSelectMenuBuilder, ButtonBuilder, ButtonStyle, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');

const OWNER_ID = "1107355943408259112"; // آونر البوت الأساسي (فهد)
const BACKUP_FILE = path.join(__dirname, '../server_backup.json');

// --- القائمة المنسدلة لاختيار السيرفر المصدر ---
class ServerSelectView extends ActionRowBuilder {
    constructor(bot, authorId) {
        super();
        this.bot = bot;
        this.authorId = authorId;
        this.selectedGuildId = null;

        const options = [];
        bot.guilds.cache.forEach(guild => {
            const name = guild.name.length > 97 ? guild.name.substring(0, 97) + "..." : guild.name;
            options.push({
                label: name,
                value: guild.id
            });
        });

        const selectMenu = new StringSelectMenuBuilder()
            .setCustomId('server_select')
            .setPlaceholder('اختر السيرفر المراد نسخ محتواه...')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(options.slice(0, 25)); // ديسكورد يسمح بـ 25 خيار كحد أقصى

        this.addComponents(selectMenu);
    }
}

class ConfirmView extends ActionRowBuilder {
    constructor(authorId) {
        super();
        this.authorId = authorId;
        this.value = null;

        const confirmBtn = new ButtonBuilder()
            .setCustomId('confirm_btn')
            .setLabel('موافقة')
            .setEmoji('✅')
            .setStyle(ButtonStyle.Success);

        const cancelBtn = new ButtonBuilder()
            .setCustomId('cancel_btn')
            .setLabel('إلغاء')
            .setEmoji('❌')
            .setStyle(ButtonStyle.Danger);

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

            const allowVal = overwrite.allow.bitfield.toString();
            const denyVal = overwrite.deny.bitfield.toString();

            overwritesData[targetId] = {
                name: targetName,
                type: targetType,
                allow: allowVal,
                deny: denyVal
            };
        });
        return overwritesData;
    },

    applyOverwrites(guild, channelData) {
        const overwrites = {};
        const roleMap = new Map();
        guild.roles.cache.forEach(role => {
            roleMap.set(role.name.trim().toLowerCase(), role);
        });

        const overwritesObj = channelData.overwrites || {};
        for (const [targetIdStr, owData] of Object.entries(overwritesObj)) {
            try {
                let target = null;
                const targetType = owData.type;
                const targetName = (owData.name || "").trim().toLowerCase();

                if (targetType === "role") {
                    target = guild.roles.cache.get(targetIdStr);
                    if (!target && roleMap.has(targetName)) {
                        target = roleMap.get(targetName);
                    }
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
            } catch (e) {
                console.log(`⚠️ خطأ في تطبيق صلاحيات الروم: ${e.message}`);
            }
        }
        return Object.values(overwrites);
    },

    // --- الأمر الخاص بك للنسخ المباشر بين السيرفرات (!my) ---
    async handleMyCommand(message) {
        if (message.author.id !== OWNER_ID) return;

        try {
            await message.delete();
        } catch (e) {}

        const view = new ServerSelectView(message.client, message.author.id);
        const msg = await message.channel.send({
            content: "🌐 | **اختر السيرفر الذي تريد نسخ الرتب والأقسام والرومات منه:**",
            components: [view]
        });

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
            await msg.edit({
                content: `⚠️ | **تريد تسوي لصق هنا؟** (سيرفر المصدر: **${sourceGuild.name}**)`,
                components: [confirmView]
            });

            const confirmSelection = await msg.awaitMessageComponent({ filter, time: 60000 });
            if (confirmSelection.customId === 'cancel_btn') {
                await confirmSelection.deferUpdate();
                await msg.edit({ content: "❌ تم إلغاء عملية اللصق بناءً على رغبتك.", components: [] });
                return;
            }

            await confirmSelection.deferUpdate();
            const targetGuild = message.guild;
            await msg.edit({ content: `⏳ | **تم تأكيد الموافقة! جاري نقل ولصق محتويات سيرفر (${sourceGuild.name}) بكل هدوء وبدون أي مشاكل...**`, components: [] });

            // 1. نسخ ونقل الرتب
            const existingRoles = new Set(targetGuild.roles.cache.map(r => r.name.trim().toLowerCase()));
            const rolesArray = Array.from(sourceGuild.roles.cache.values()).reverse();
            for (const role of rolesArray) {
                if (role.managed || role.id === sourceGuild.id) continue;
                if (existingRoles.has(role.name.trim().toLowerCase())) continue;
                try {
                    await targetGuild.roles.create({
                        name: role.name,
                        permissions: role.permissions,
                        color: role.color,
                        hoist: role.hoist,
                        mentionable: role.mentionable,
                        reason: "نسخ مباشر بواسطة المالك"
                    });
                    existingRoles.add(role.name.trim().toLowerCase());
                    await new Promise(res => setTimeout(res, 1200));
                } catch (e) {
                    console.log(`⚠️ خطأ في إنشاء رتبة: ${e.message}`);
                }
            }

            // 2. نسخ ونقل الأقسام والرومات
            const existingCategories = new Map();
            targetGuild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).forEach(c => {
                existingCategories.set(c.name.trim().toLowerCase(), c);
            });
            const existingChannels = new Set(targetGuild.channels.cache.map(c => c.name.trim().toLowerCase()));

            // الرومات التي بدون قسم
            for (const channel of sourceGuild.channels.cache.values()) {
                if (channel.parent) continue;
                if (channel.type === ChannelType.GuildText || channel.type === ChannelType.GuildVoice) {
                    if (existingChannels.has(channel.name.trim().toLowerCase())) continue;
                    try {
                        if (channel.type === ChannelType.GuildText) {
                            await targetGuild.channels.create({
                                name: channel.name,
                                type: ChannelType.GuildText,
                                topic: channel.topic,
                                rateLimitPerUser: channel.rateLimitPerUser,
                                nsfw: channel.nsfw
                            });
                        } else if (channel.type === ChannelType.GuildVoice) {
                            await targetGuild.channels.create({
                                name: channel.name,
                                type: ChannelType.GuildVoice,
                                bitrate: channel.bitrate,
                                userLimit: channel.userLimit
                            });
                        }
                        existingChannels.add(channel.name.trim().toLowerCase());
                        await new Promise(res => setTimeout(res, 1200));
                    } catch (e) {
                        console.log(`⚠️ خطأ بروم: ${e.message}`);
                    }
                }
            }

            // الأقسام وما بداخلها
            for (const category of sourceGuild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).values()) {
                const catName = category.name.trim();
                let catObj = null;

                if (existingCategories.has(catName.toLowerCase())) {
                    catObj = existingCategories.get(catName.toLowerCase());
                } else {
                    try {
                        catObj = await targetGuild.channels.create({
                            name: catName,
                            type: ChannelType.GuildCategory
                        });
                        existingCategories.set(catName.toLowerCase(), catObj);
                        await new Promise(res => setTimeout(res, 1500));
                    } catch (e) {
                        console.log(`⚠️ خطأ بإنشاء القسم: ${e.message}`);
                        continue;
                    }
                }

                for (const channel of category.children.cache.values()) {
                    const chName = channel.name.trim();
                    if (existingChannels.has(chName.toLowerCase())) continue;
                    try {
                        if (channel.type === ChannelType.GuildText) {
                            await targetGuild.channels.create({
                                name: chName,
                                type: ChannelType.GuildText,
                                parent: catObj.id,
                                topic: channel.topic,
                                rateLimitPerUser: channel.rateLimitPerUser,
                                nsfw: channel.nsfw
                            });
                        } else if (channel.type === ChannelType.GuildVoice) {
                            await targetGuild.channels.create({
                                name: chName,
                                type: ChannelType.GuildVoice,
                                parent: catObj.id,
                                bitrate: channel.bitrate,
                                userLimit: channel.userLimit
                            });
                        }
                        existingChannels.add(chName.toLowerCase());
                        await new Promise(res => setTimeout(res, 1200));
                    } catch (e) {
                        console.log(`⚠️ خطأ بروم داخل القسم: ${e.message}`);
                    }
                }
            }

            await message.channel.send(`✅ **تمت عملية نقل ولصق كافة الرتب والأقسام والرومات بنجاح تام وبدون مشاكل!**`);

        } catch (e) {
            await message.channel.send(`❌ انتهى الوقت أو حدث خطأ أثناء عملية اللصق: ${e.message}`);
        }
    },

    backupServerCommand: new SlashCommandBuilder()
        .setName('backup')
        .setDescription('أخذ نسخة احتياطية مطابقة 100% وتحديثها مع إرسال إشعار للأونر.')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    restoreServerCommand: new SlashCommandBuilder()
        .setName('restore')
        .setDescription('استعادة السيرفر مع منع تكرار الرتب والرومات والأقسام نهائياً.')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleBackup(interaction) {
        await interaction.reply({ content: "⏳ جاري إنشاء النسخة الاحتياطية الشاملة لكافة تفاصيل السيرفر...", ephemeral: false });
        const guild = interaction.guild;

        try {
            if (fs.existsSync(BACKUP_FILE)) {
                fs.unlinkSync(BACKUP_FILE);
            }

            const rolesData = [];
            const sortedRoles = Array.from(guild.roles.cache.values()).reverse();
            for (const role of sortedRoles) {
                if (role.managed || role.id === guild.id) continue;
                rolesData.push({
                    id: role.id,
                    name: role.name,
                    permissions: role.permissions.bitfield.toString(),
                    color: role.color,
                    hoist: role.hoist,
                    mentionable: role.mentionable,
                    position: role.position
                });
            }

            const categoriesData = [];
            const noCategoryChannels = [];

            guild.channels.cache.forEach(channel => {
                if (!channel.parent) {
                    if (channel.type === ChannelType.GuildText) {
                        noCategoryChannels.push({
                            name: channel.name,
                            type: "text",
                            topic: channel.topic,
                            slowmode: channel.rateLimitPerUser,
                            nsfw: channel.nsfw,
                            overwrites: this.serializeOverwrites(guild, channel)
                        });
                    } else if (channel.type === ChannelType.GuildVoice) {
                        noCategoryChannels.push({
                            name: channel.name,
                            type: "voice",
                            bitrate: channel.bitrate,
                            user_limit: channel.userLimit,
                            overwrites: this.serializeOverwrites(guild, channel)
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
                    if (channel.type === ChannelType.GuildText) {
                        catChannels.push({
                            name: channel.name,
                            type: "text",
                            topic: channel.topic,
                            slowmode: channel.rateLimitPerUser,
                            nsfw: channel.nsfw,
                            overwrites: this.serializeOverwrites(guild, channel)
                        });
                    } else if (channel.type === ChannelType.GuildVoice) {
                        catChannels.push({
                            name: channel.name,
                            type: "voice",
                            bitrate: channel.bitrate,
                            user_limit: channel.userLimit,
                            overwrites: this.serializeOverwrites(guild, channel)
                        });
                    }
                });

                categoriesData.push({
                    name: category.name,
                    overwrites: this.serializeOverwrites(guild, category),
                    channels: catChannels
                });
            });

            const backupDict = {
                guild_name: guild.name,
                roles: rolesData,
                categories: categoriesData
            };

            fs.writeFileSync(BACKUP_FILE, JSON.stringify(backupDict, null, 4), 'utf8');

            const totalChannels = categoriesData.reduce((acc, cat) => acc + cat.channels.length, 0);
            const serverOwner = await guild.fetchOwner().catch(() => null);
            const ownerMention = serverOwner ? `<@${serverOwner.id}>` : "الأونر";

            await interaction.editReply({
                content: (
                    `✅ **تمت عملية النسخ الاحتياطي وتحديث الملف بنجاح!** ${ownerMention}\n` +
                    `- عدد الرتب المحفوظة: **${rolesData.length}**\n` +
                    `- عدد الرومات والأقسام المحفوظة: **{totalChannels}** (مع صلاحياتها بالكامل).\n\n` +
                    `**تم كملت**`
                ).replace('{totalChannels}', totalChannels)
            });

        } catch (e) {
            await interaction.editReply({ content: `❌ حدث خطأ أثناء إنشاء النسخة: ${e.message}` });
        }
    },

    async handleRestore(interaction) {
        if (!fs.existsSync(BACKUP_FILE)) {
            await interaction.reply({ content: "❌ عذراً، لا توجد أي نسخة احتياطية محفوظة حالياً! يرجى عمل `/backup` أولاً.", ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });
        const guild = interaction.guild;

        try {
            const rawData = fs.readFileSync(BACKUP_FILE, 'utf8');
            const backupData = JSON.parse(rawData);

            const existingRoleNames = new Set(guild.roles.cache.map(r => r.name.trim().toLowerCase()));

            for (const rData of backupData.roles) {
                const rName = rData.name.trim();
                if (existingRoleNames.has(rName.toLowerCase())) continue;
                try {
                    await guild.roles.create({
                        name: rName,
                        permissions: BigInt(rData.permissions),
                        color: rData.color,
                        hoist: rData.hoist,
                        mentionable: rData.mentionable,
                        reason: "استعادة النسخة الاحتياطية بدون تكرار"
                    });
                    existingRoleNames.add(rName.toLowerCase());
                    await new Promise(res => setTimeout(res, 1200));
                } catch (e) {
                    console.log(`⚠️ خطأ بإنشاء رتبة ${rName}: ${e.message}`);
                }
            }

            const existingCategories = new Map();
            guild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).forEach(c => {
                existingCategories.set(c.name.trim().toLowerCase(), c);
            });
            const existingChannels = new Set(guild.channels.cache.map(c => c.name.trim().toLowerCase()));

            for (const catData of backupData.categories) {
                let categoryObj = null;
                const catName = catData.name.trim();

                if (catName !== "بدون قسم") {
                    if (existingCategories.has(catName.toLowerCase())) {
                        categoryObj = existingCategories.get(catName.toLowerCase());
                    } else {
                        try {
                            const catOverwrites = this.applyOverwrites(guild, catData);
                            categoryObj = await guild.channels.create({
                                name: catName,
                                type: ChannelType.GuildCategory,
                                permissionOverwrites: catOverwrites
                            });
                            existingCategories.set(catName.toLowerCase(), categoryObj);
                            await new Promise(res => setTimeout(res, 1500));
                        } catch (e) {
                            console.log(`⚠️ خطأ بإنشاء القسم ${catName}: ${e.message}`);
                            continue;
                        }
                    }
                }

                for (const chData of catData.channels) {
                    const chName = chData.name.trim();
                    if (existingChannels.has(chName.toLowerCase())) continue;

                    try {
                        const chOverwrites = this.applyOverwrites(guild, chData);
                        if (chData.type === "text") {
                            await guild.channels.create({
                                name: chName,
                                type: ChannelType.GuildText,
                                parent: categoryObj ? categoryObj.id : null,
                                topic: chData.topic,
                                rateLimitPerUser: chData.slowmode || 0,
                                nsfw: chData.nsfw || false,
                                permissionOverwrites: chOverwrites
                            });
                        } else if (chData.type === "voice") {
                            await guild.channels.create({
                                name: chName,
                                type: ChannelType.GuildVoice,
                                parent: categoryObj ? categoryObj.id : null,
                                bitrate: chData.bitrate || 64000,
                                userLimit: chData.user_limit || 0,
                                permissionOverwrites: chOverwrites
                            });
                        }
                        existingChannels.add(chName.toLowerCase());
                        await new Promise(res => setTimeout(res, 1200));
                    } catch (e) {
                        console.log(`⚠️ خطأ بإنشاء الروم ${chName}: ${e.message}`);
                    }
                }
            }

            await interaction.followup.send({
                content: (
                    `✅ **تمت استعادة العناصر الجديدة فقط دون أي تكرار للرتب أو الرومات أو الأقسام!**\n\n` +
                    `**تم كملت**`
                ),
                ephemeral: true
            });

        } catch (e) {
            await interaction.followup.send({ content: `❌ حدث خطأ غير متوقع أثناء الاستعادة: ${e.message}`, ephemeral: true });
        }
    }
};
