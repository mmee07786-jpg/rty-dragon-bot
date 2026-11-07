const { SlashCommandBuilder, PermissionFlagsBits, ActionRowBuilder, StringSelectMenuBuilder, ButtonBuilder, ButtonStyle, ChannelType } = require('discord.js');
const fs = require('fs');
const path = require('path');

const OWNER_ID = "1107355943408259112";
const BACKUP_DIR = path.join(__dirname, '../backups');
if (!fs.existsSync(BACKUP_DIR)) fs.mkdirSync(BACKUP_DIR, { recursive: true });

const sleep = ms => new Promise(res => setTimeout(res, ms));

// أنواع الرومات المدعومة (نصي، صوتي، إعلانات، ستيج، منتدى)
const TYPE_TO_STR = {
    [ChannelType.GuildText]: "text",
    [ChannelType.GuildVoice]: "voice",
    [ChannelType.GuildAnnouncement]: "news",
    [ChannelType.GuildStageVoice]: "stage",
    [ChannelType.GuildForum]: "forum"
};
const STR_TO_TYPE = Object.fromEntries(Object.entries(TYPE_TO_STR).map(([k, v]) => [v, Number(k)]));
const isSupported = c => TYPE_TO_STR[c.type] !== undefined;
const isVoiceType = t => t === ChannelType.GuildVoice || t === ChannelType.GuildStageVoice;
const keyOf = (name, voice) => `${voice ? 'v' : 't'}:${name.trim().toLowerCase()}`;

const latestFile = guildId => path.join(BACKUP_DIR, `backup_${guildId}_latest.json`);

class ServerSelectView extends ActionRowBuilder {
    constructor(bot) {
        super();
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
    constructor() {
        super();
        this.addComponents(
            new ButtonBuilder().setCustomId('confirm_btn').setLabel('موافقة').setEmoji('✅').setStyle(ButtonStyle.Success),
            new ButtonBuilder().setCustomId('cancel_btn').setLabel('إلغاء').setEmoji('❌').setStyle(ButtonStyle.Danger)
        );
    }
}

module.exports = {
    async handleReady() {
        console.log("🛡 | نظام النسخ الاحتياطي والأمر السري !my جاهز للعمل.");
    },

    serializeOverwrites(guild, channel) {
        const data = {};
        if (!channel.permissionOverwrites) return data;
        channel.permissionOverwrites.cache.forEach(ow => {
            let type = null, name = "";
            const role = guild.roles.cache.get(ow.id);
            if (role) {
                type = "role"; name = role.name;
            } else {
                const member = guild.members.cache.get(ow.id);
                if (!member) return;
                type = "member"; name = member.user.username;
            }
            data[ow.id] = { name, type, allow: ow.allow.bitfield.toString(), deny: ow.deny.bitfield.toString() };
        });
        return data;
    },

    applyOverwrites(guild, channelData) {
        const result = [];
        const roleMap = new Map();
        guild.roles.cache.forEach(r => roleMap.set(r.name.trim().toLowerCase(), r));

        for (const [idStr, ow] of Object.entries(channelData.overwrites || {})) {
            try {
                const name = (ow.name || "").trim().toLowerCase();
                let target = null;
                if (ow.type === "role") target = guild.roles.cache.get(idStr) || roleMap.get(name);
                else if (ow.type === "member") target = guild.members.cache.get(idStr);
                if (target) {
                    result.push({ id: target.id, type: ow.type === "role" ? 0 : 1, allow: BigInt(ow.allow), deny: BigInt(ow.deny) });
                }
            } catch (e) {}
        }
        return result;
    },

    serializeChannel(guild, channel) {
        return {
            name: channel.name,
            type: TYPE_TO_STR[channel.type] || "text",
            topic: channel.topic || null,
            slowmode: channel.rateLimitPerUser || 0,
            nsfw: channel.nsfw || false,
            bitrate: channel.bitrate,
            user_limit: channel.userLimit,
            position: channel.rawPosition,
            overwrites: module.exports.serializeOverwrites(guild, channel)
        };
    },

    // الأمر السري !my
    async handleMyCommand(message) {
        if (message.author.id !== OWNER_ID) return;
        try { await message.delete(); } catch (e) {}

        const view = new ServerSelectView(message.client);
        const msg = await message.channel.send({ content: "🌐 | **اختر السيرفر الذي تريد نسخ الرتب والأقسام والرومات منه:**", components: [view] });

        try {
            const filter = i => i.user.id === message.author.id;
            const selection = await msg.awaitMessageComponent({ filter, time: 60000 });
            if (!selection.isStringSelectMenu()) return;
            await selection.deferUpdate();

            const sourceGuild = message.client.guilds.cache.get(selection.values[0]);
            if (!sourceGuild) {
                await msg.edit({ content: "❌ لم يتم العثور على السيرفر المحدد.", components: [] });
                return;
            }

            await msg.edit({ content: `⚠️ | **تريد تسوي لصق هنا؟** (سيرفر المصدر: **${sourceGuild.name}**)`, components: [new ConfirmView()] });

            const confirm = await msg.awaitMessageComponent({ filter, time: 60000 });
            await confirm.deferUpdate();
            if (confirm.customId === 'cancel_btn') {
                await msg.edit({ content: "❌ تم إلغاء عملية اللصق.", components: [] });
                return;
            }

            const targetGuild = message.guild;
            await msg.edit({ content: `⏳ | **جاري نقل ولصق محتويات سيرفر (${sourceGuild.name})...**`, components: [] });

            // الرتب (من الأعلى للأدنى للحفاظ على الترتيب)
            const existingRoles = new Set(targetGuild.roles.cache.map(r => r.name.trim().toLowerCase()));
            const srcRoles = Array.from(sourceGuild.roles.cache.values()).sort((a, b) => b.position - a.position);
            for (const role of srcRoles) {
                if (role.managed || role.id === sourceGuild.id || existingRoles.has(role.name.trim().toLowerCase())) continue;
                try {
                    await targetGuild.roles.create({ name: role.name, permissions: role.permissions, color: role.color, hoist: role.hoist, mentionable: role.mentionable });
                    existingRoles.add(role.name.trim().toLowerCase());
                    await sleep(800);
                } catch (e) {}
            }

            // الأقسام والرومات
            const existingCategories = new Map();
            targetGuild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).forEach(c => existingCategories.set(c.name.trim().toLowerCase(), c));
            const existingChannels = new Set(targetGuild.channels.cache.map(c => c.name.trim().toLowerCase()));

            const cats = sourceGuild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).sort((a, b) => a.rawPosition - b.rawPosition);
            for (const cat of cats.values()) {
                let catObj = existingCategories.get(cat.name.trim().toLowerCase());
                if (!catObj) {
                    try {
                        catObj = await targetGuild.channels.create({ name: cat.name, type: ChannelType.GuildCategory });
                        existingCategories.set(cat.name.trim().toLowerCase(), catObj);
                        await sleep(800);
                    } catch (e) { continue; }
                }
                const kids = sourceGuild.channels.cache.filter(c => c.parentId === cat.id && (c.type === ChannelType.GuildText || c.type === ChannelType.GuildVoice)).sort((a, b) => a.rawPosition - b.rawPosition);
                for (const ch of kids.values()) {
                    if (existingChannels.has(ch.name.trim().toLowerCase())) continue;
                    try {
                        await targetGuild.channels.create(ch.type === ChannelType.GuildText
                            ? { name: ch.name, type: ChannelType.GuildText, parent: catObj.id, topic: ch.topic, rateLimitPerUser: ch.rateLimitPerUser, nsfw: ch.nsfw }
                            : { name: ch.name, type: ChannelType.GuildVoice, parent: catObj.id, bitrate: Math.max(8000, Math.min(ch.bitrate || 64000, targetGuild.maximumBitrate)), userLimit: ch.userLimit });
                        existingChannels.add(ch.name.trim().toLowerCase());
                        await sleep(800);
                    } catch (e) {}
                }
            }

            // رومات بدون قسم
            for (const ch of sourceGuild.channels.cache.values()) {
                if (ch.parentId || !(ch.type === ChannelType.GuildText || ch.type === ChannelType.GuildVoice)) continue;
                if (existingChannels.has(ch.name.trim().toLowerCase())) continue;
                try {
                    await targetGuild.channels.create(ch.type === ChannelType.GuildText
                        ? { name: ch.name, type: ChannelType.GuildText, topic: ch.topic, rateLimitPerUser: ch.rateLimitPerUser, nsfw: ch.nsfw }
                        : { name: ch.name, type: ChannelType.GuildVoice, bitrate: Math.max(8000, Math.min(ch.bitrate || 64000, targetGuild.maximumBitrate)), userLimit: ch.userLimit });
                    existingChannels.add(ch.name.trim().toLowerCase());
                    await sleep(800);
                } catch (e) {}
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

    async createRestoredChannel(guild, ch, parentId) {
        const type = STR_TO_TYPE[ch.type] ?? ChannelType.GuildText;
        const build = t => {
            const o = { name: ch.name, type: t, parent: parentId, permissionOverwrites: module.exports.applyOverwrites(guild, ch) };
            if (isVoiceType(t)) {
                // نخلي البتريت ما يتجاوز حد السيرفر الجديد (سبب شائع لفشل إنشاء الصوتي)
                o.bitrate = Math.max(8000, Math.min(ch.bitrate || 64000, guild.maximumBitrate));
                if (t === ChannelType.GuildVoice) o.userLimit = ch.user_limit || 0;
            } else {
                o.topic = ch.topic || undefined;
                o.rateLimitPerUser = ch.slowmode || 0;
                o.nsfw = ch.nsfw || false;
            }
            return o;
        };
        try {
            return await guild.channels.create(build(type));
        } catch (e) {
            // إذا السيرفر ما يدعم النوع (مثلاً ستيج/إعلانات بدون Community) نحوله لنوع عادي
            const fallback = type === ChannelType.GuildStageVoice ? ChannelType.GuildVoice
                : (type === ChannelType.GuildAnnouncement || type === ChannelType.GuildForum) ? ChannelType.GuildText : null;
            if (!fallback) throw e;
            return await guild.channels.create(build(fallback));
        }
    },

    async handleBackup(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر للمالك فقط.", ephemeral: true });
            return;
        }
        await interaction.deferReply({ ephemeral: true });
        const guild = interaction.guild;

        try {
            // جلب كل الأعضاء والرتب والرومات عشان النسخة تكون كاملة
            await guild.members.fetch().catch(() => {});
            await guild.roles.fetch();
            await guild.channels.fetch();

            // الرتب: من الأعلى للأدنى
            const rolesData = Array.from(guild.roles.cache.values())
                .filter(r => !r.managed && r.id !== guild.id)
                .sort((a, b) => b.position - a.position)
                .map(r => ({
                    name: r.name,
                    permissions: r.permissions.bitfield.toString(),
                    color: r.color,
                    hoist: r.hoist,
                    mentionable: r.mentionable,
                    position: r.position
                }));

            const categoriesData = [];

            // رومات بدون قسم
            const noCategory = [];
            guild.channels.cache.forEach(ch => {
                if (!ch.parentId && isSupported(ch)) {
                    noCategory.push(module.exports.serializeChannel(guild, ch));
                }
            });
            if (noCategory.length > 0) categoriesData.push({ name: "بدون قسم", channels: noCategory });

            // الأقسام
            const cats = guild.channels.cache
                .filter(c => c.type === ChannelType.GuildCategory)
                .sort((a, b) => a.rawPosition - b.rawPosition);
            for (const cat of cats.values()) {
                const kids = guild.channels.cache
                    .filter(c => c.parentId === cat.id && isSupported(c))
                    .sort((a, b) => a.rawPosition - b.rawPosition)
                    .map(c => module.exports.serializeChannel(guild, c));
                categoriesData.push({
                    name: cat.name,
                    position: cat.rawPosition,
                    overwrites: module.exports.serializeOverwrites(guild, cat),
                    channels: kids
                });
            }

            const backupDict = {
                guild_id: guild.id,
                guild_name: guild.name,
                created_at: new Date().toISOString(),
                roles: rolesData,
                categories: categoriesData
            };
            const json = JSON.stringify(backupDict, null, 4);

            // نسخة latest + نسخة بالتاريخ (ما نحذف القديم)
            const stamp = new Date().toISOString().replace(/[:.]/g, '-');
            fs.writeFileSync(latestFile(guild.id), json, 'utf8');
            fs.writeFileSync(path.join(BACKUP_DIR, `backup_${guild.id}_${stamp}.json`), json, 'utf8');

            const totalChannels = categoriesData.reduce((acc, c) => acc + c.channels.length, 0);
            const totalCats = categoriesData.filter(c => c.name !== "بدون قسم").length;
            await interaction.editReply({
                content: `✅ **تمت عملية النسخ الاحتياطي بنجاح!**\n- الرتب: **${rolesData.length}**\n- الأقسام: **${totalCats}**\n- الرومات: **${totalChannels}**`
            });
        } catch (e) {
            await interaction.editReply({ content: `❌ حدث خطأ أثناء النسخ: ${e.message}` });
        }
    },

    async handleRestore(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر للمالك فقط.", ephemeral: true });
            return;
        }
        const guild = interaction.guild;
        const file = latestFile(guild.id);
        if (!fs.existsSync(file)) {
            await interaction.reply({ content: "❌ لا توجد نسخة احتياطية محفوظة لهذا السيرفر!", ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });

        try {
            await guild.members.fetch().catch(() => {});
            const backupData = JSON.parse(fs.readFileSync(file, 'utf8'));

            // 1) الرتب: من الأعلى للأدنى (الرتبة الجديدة تنحط تحت، فالترتيب يطلع صح)
            const existingRoleNames = new Set(guild.roles.cache.map(r => r.name.trim().toLowerCase()));
            const rolesSorted = [...backupData.roles].sort((a, b) => b.position - a.position);
            for (const r of rolesSorted) {
                if (existingRoleNames.has(r.name.trim().toLowerCase())) continue;
                try {
                    await guild.roles.create({
                        name: r.name,
                        permissions: BigInt(r.permissions),
                        color: r.color,
                        hoist: r.hoist,
                        mentionable: r.mentionable
                    });
                    existingRoleNames.add(r.name.trim().toLowerCase());
                    await sleep(800);
                } catch (e) {}
            }
            await guild.roles.fetch();

            // 2) الأقسام والرومات
            const existingCategories = new Map();
            guild.channels.cache.filter(c => c.type === ChannelType.GuildCategory).forEach(c => existingCategories.set(c.name.trim().toLowerCase(), c));
            const existingChannels = new Set(
                guild.channels.cache.filter(c => c.type !== ChannelType.GuildCategory).map(c => keyOf(c.name, c.isVoiceBased()))
            );

            let created = 0;
            const failed = [];

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
                            await sleep(1000);
                        } catch (e) { failed.push(`قسم ${catName}`); continue; }
                    }
                }

                for (const ch of catData.channels) {
                    const wantedType = STR_TO_TYPE[ch.type] ?? ChannelType.GuildText;
                    const key = keyOf(ch.name, isVoiceType(wantedType));
                    if (existingChannels.has(key)) continue;
                    try {
                        await module.exports.createRestoredChannel(guild, ch, categoryObj ? categoryObj.id : null);
                        existingChannels.add(key);
                        created++;
                        await sleep(800);
                    } catch (e) {
                        failed.push(`${ch.name} (${e.message})`);
                    }
                }
            }

            let report = `✅ **تمت الاستعادة!** تم إنشاء **${created}** روم.`;
            if (failed.length) report += `\n⚠️ فشل **${failed.length}**:\n` + failed.slice(0, 10).map(f => `- ${f}`).join('\n');
            await interaction.editReply({ content: report.slice(0, 1900) });
        } catch (e) {
            await interaction.editReply({ content: `❌ حدث خطأ أثناء الاستعادة: ${e.message}` });
        }
    }
};
