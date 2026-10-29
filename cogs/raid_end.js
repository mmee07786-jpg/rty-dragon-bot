const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, ActionRowBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../raid_data.json');
const EMBED_COLOR = 0x8B0000;
const GIF_BANNER_URL = "https://cdn.discordapp.com/attachments/1479214156560466045/1542918296322572338/Comp1-ezgif.com-crop-2.gif?ex=6aa4c663&is=6aa374e3&hm=4b16c8a711658887aa9f018379775fff77ef8c176114498832a5a3dc10e5b8eb&";

const OWNER_ID = "1107355943408259112";
const BYPASS_IDS = new Set([OWNER_ID, "1182323811341840447"]);
const adminCooldows = new Map();

function loadRaidData() {
    if (fs.existsSync(DATA_FILE)) {
        try {
            const d = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
            for (const g in d) {
                if (typeof d[g] === 'object' && d[g] !== null) {
                    if (!d[g].roblox_users) d[g].roblox_users = {};
                    if (!d[g].member_countries) d[g].member_countries = {};
                    if (!d[g].custom_avatars) d[g].custom_avatars = {};
                    if (!d[g].blacklist) d[g].blacklist = [];
                }
            }
            return d;
        } catch (e) {
            return {};
        }
    }
    return {};
}

function saveRaidData(d) {
    fs.writeFileSync(DATA_FILE, JSON.stringify(d, null, 4), 'utf8');
}

class RobloxTopAvatarModal extends ModalBuilder {
    constructor() {
        super();
        this.setTitle("🖼️ | تعيين صورة توب روبلوكس").setCustomId("roblox_top_avatar_modal");

        const topPosition = new TextInputBuilder()
            .setCustomId("top_position")
            .setLabel("رقم التوب المراد تغييره (من 1 إلى 20)")
            .setStyle(TextInputStyle.Short)
            .setRequired(true)
            .setPlaceholder("مثال: 1");

        const avatarLink = new TextInputBuilder()
            .setCustomId("avatar_link")
            .setLabel("رابط الصورة أو يوزر/إيدي روبلوكس")
            .setStyle(TextInputStyle.Short)
            .setRequired(true)
            .setPlaceholder("مثال: رابط مباشر أو يوزر روبلوكس");

        this.addComponents(new ActionRowBuilder().addComponents(topPosition), new ActionRowBuilder().addComponents(avatarLink));
    }
}

class RaidEndInfoModal extends ModalBuilder {
    constructor() {
        super();
        this.setTitle("🏁 | Conclude Raid & Record Results").setCustomId("raid_end_info_modal");

        const raidNumber = new TextInputBuilder().setCustomId("raid_number").setLabel("RAID Number").setStyle(TextInputStyle.Short).setRequired(true);
        const enemy = new TextInputBuilder().setCustomId("enemy").setLabel("ENEMY").setStyle(TextInputStyle.Short).setRequired(true);
        const ally = new TextInputBuilder().setCustomId("ally").setLabel("ALLY").setStyle(TextInputStyle.Short).setRequired(true);
        const duration = new TextInputBuilder().setCustomId("duration").setLabel("DURATION").setStyle(TextInputStyle.Short).setRequired(true);
        const statusReason = new TextInputBuilder().setCustomId("status_reason").setLabel("STATUS").setStyle(TextInputStyle.Short).setRequired(true);

        this.addComponents(
            new ActionRowBuilder().addComponents(raidNumber),
            new ActionRowBuilder().addComponents(enemy),
            new ActionRowBuilder().addComponents(ally),
            new ActionRowBuilder().addComponents(duration),
            new ActionRowBuilder().addComponents(statusReason)
        );
    }
}

class RaidSubmitModal extends ModalBuilder {
    constructor(rn, en, al, dur, st) {
        super();
        this.setTitle("👥 | MVPs & Media").setCustomId("raid_submit_modal");
        this.rn = rn; this.en = en; this.al = al; this.dur = dur; this.st = st;

        const mvpsInput = new TextInputBuilder()
            .setCustomId("mvps_input")
            .setLabel("MVPs (منشنات)")
            .setStyle(TextInputStyle.Paragraph)
            .setRequired(true);

        const mediaLinks = new TextInputBuilder()
            .setCustomId("media_links")
            .setLabel("Media Link")
            .setStyle(TextInputStyle.Paragraph)
            .setRequired(false);

        this.addComponents(new ActionRowBuilder().addComponents(mvpsInput), new ActionRowBuilder().addComponents(mediaLinks));
    }
}

module.exports = {
    async handleRobloxTopAvatarSubmit(interaction) {
        const posVal = interaction.fields.getTextInputValue("top_position").trim();
        if (!/^\d+$/.test(posVal)) {
            await interaction.reply({ content: "❌ | يرجى كتابة رقم توب صحيح بين 1 و 20!", ephemeral: true });
            return;
        }
        const num = parseInt(posVal, 10);
        if (num < 1 || num > 20) {
            await interaction.reply({ content: "❌ | التوبات محددة من 1 إلى 20 فقط!", ephemeral: true });
            return;
        }

        const val = interaction.fields.getTextInputValue("avatar_link").trim();
        let link = val;
        if (!val.startsWith("http")) {
            if (/^\d+$/.test(val)) {
                link = `https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds=${val}&size=420x420&format=Png&isCircular=false`;
            } else {
                link = `https://www.roblox.com/headshot-thumbnail/image?username=${val}&width=420&height=420&format=png`;
            }
        }

        const gid = interaction.guildId;
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };
        data[gid].custom_avatars[num.toString()] = link;
        saveRaidData(data);

        await interaction.reply({ content: `✅ | تم تعيين وتحديث صورة التوب رقم \`${num}\` بنجاح وتطبيقها تلقائياً على اللوحة!`, ephemeral: true });
        
        const cog = interaction.client.getRaidSystemCog ? interaction.client.getRaidSystemCog() : null; // سيتم استدعاؤها عبر methods
    },

    async handleRaidSubmitModal(interaction, rn, en, al, dur, st) {
        await interaction.deferReply({ ephemeral: true });
        const gid = interaction.guildId;
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };
        
        data[gid].win_streak = (data[gid].win_streak || 0) + 1;
        const streak = data[gid].win_streak;

        const mvpsText = interaction.fields.getTextInputValue("mvps_input");
        const mediaText = interaction.fields.getTextInputValue("media_links");

        const uids = [...mvpsText.matchAll(/<@!?(\d+)>/g)].map(m => m[1]);
        const blacklist = data[gid].blacklist || [];
        const statsCog = interaction.client.memberStatsCog; // مرجع لـ MemberStats

        for (const uid of uids) {
            if (blacklist.includes(uid)) continue;
            const currentRaids = (data[gid].raider_stats[uid] || 0) + 1;
            data[gid].raider_stats[uid] = currentRaids;

            if (statsCog && typeof statsCog.processMemberRaidUpdate === 'function') {
                const memberObj = await interaction.guild.members.fetch(uid).catch(() => null);
                if (memberObj) {
                    await statsCog.processMemberRaidUpdate(interaction.guild, memberObj, currentRaids);
                }
            }
        }

        saveRaidData(data);

        let content = `╭─〔 𝐒𝐂𝐎𝐑𝐄 〕─╮\n\n**𝐑𝐀𝐈𝐃:**\n╰➤${rn}\n\n**𝐄𝐍𝐄𝐌𝐘:**\n╰➤${en}\n\n**𝐀𝐋𝐋𝐘:**\n╰➤${al}\n\n**𝐃𝐔𝐑𝐀𝐓𝐈𝐎𝐍:**\n╰➤${dur}\n\n**𝐒𝐓𝐀𝐓𝐔𝐒:**\n╰➤${st}\n\n**𝐌𝐕𝐏𝐒:**\n╰➤ ${mvpsText}\n\n`;
        let imgUrl = null;
        const mval = mediaText ? mediaText.trim() : "";
        if (mval && mval.toLowerCase() !== "skip") {
            const urls = mval.match(/https?:\/\/[^\s]+/g);
            if (urls && urls.length > 0) {
                imgUrl = urls[0];
                content += `**𝐏𝐑𝐎𝐎𝐅:**\n╰➤ ${mval}\n\n`;
            }
        }
        content += `🔥 **Win Streak:** \`${streak} in a row\`\n\n╰────────────────╯`;

        const emb = new EmbedBuilder().setColor(EMBED_COLOR).setDescription(content);
        if (imgUrl) emb.setImage(imgUrl);
        emb.setFooter({ text: `Ended by ${interaction.user.tag} | VLX` });

        await interaction.channel.send({ content: "🏁 **Raid Report:**", embeds: [emb] });
        await interaction.followup({ content: "✅ | تم تسجيل الرايد وإضافة النقاط بنجاح (ستتحدث اللوحات تلقائياً نهاية الأسبوع)!", ephemeral: true });
    },

    setTop10ChannelCommand: new SlashCommandBuilder()
        .setName('set-top10-channel')
        .setDescription('تعيين قناة توب 10 الأسبوعية')
        .addChannelOption(o => o.setName('channel').setDescription('قناة توب 10').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    setTop20ChannelCommand: new SlashCommandBuilder()
        .setName('set-top20-channel')
        .setDescription('تعيين قناة توب من 11 إلى 20 الأسبوعية')
        .addChannelOption(o => o.setName('channel').setDescription('قناة توب 20').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    avatarRobloxTopCommand: new SlashCommandBuilder()
        .setName('avatar-roblox-top')
        .setDescription('تعيين صورة أو سكن أفتار لروبلوكس لتوب معين تلقائياً')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    setCountryCommand: new SlashCommandBuilder()
        .setName('set-country')
        .setDescription('تحديد دولة العضو')
        .addUserOption(o => o.setName('member').setDescription('العضو').setRequired(true))
        .addStringOption(o => o.setName('country_value').setDescription('اسم الدولة').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    endRaidCommand: new SlashCommandBuilder()
        .setName('end-raid')
        .setDescription('إنهاء الرايد وتسجيل النتائج'),

    setRobloxCommand: new SlashCommandBuilder()
        .setName('set-roblox')
        .setDescription('ربط يوزر روبلوكس الخاص بك')
        .addStringOption(o => o.setName('username').setDescription('يوزر روبلوكس').setRequired(true)),

    setRobloxUserCommand: new SlashCommandBuilder()
        .setName('set-roblox-user')
        .setDescription('ربط يوزر روبلوكس لعضو آخر (للإدارة)')
        .addUserOption(o => o.setName('member').setDescription('العضو').setRequired(true))
        .addStringOption(o => o.setName('username').setDescription('يوزر روبلوكس').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    syncCommandsCommand: new SlashCommandBuilder()
        .setName('sync')
        .setDescription('مزامنة الأوامر يدوياً'),

    raidMentionsCommand: new SlashCommandBuilder()
        .setName('raid-mentions')
        .setDescription('نشر قائمة المنشنات للرايد')
        .addStringOption(o => o.setName('mentions_content').setDescription('المنشنات').setRequired(true)),

    raidListCommand: new SlashCommandBuilder()
        .setName('raid-list')
        .setDescription('عرض أكثر 50 عضواً مشاركاً في الرايدات كـ Embed'),

    raidAddCommand: new SlashCommandBuilder()
        .setName('raid-add')
        .setDescription('إضافة أو خصم عدد الرايدات لعضو معين')
        .addUserOption(o => o.setName('member').setDescription('العضو').setRequired(true))
        .addIntegerOption(o => o.setName('amount').setDescription('الكمية').setRequired(true)),

    raidSetCommand: new SlashCommandBuilder()
        .setName('raid-set')
        .setDescription('تعيين عدد الرايدات المباشر لعضو معين')
        .addUserOption(o => o.setName('member').setDescription('العضو').setRequired(true))
        .addIntegerOption(o => o.setName('amount').setDescription('الكمية').setRequired(true)),

    setAvatarRemoveCommand: new SlashCommandBuilder()
        .setName('set-avatar-remove')
        .setDescription('حذف الصورة المخصصة لتوب معين وإزالتها')
        .addIntegerOption(o => o.setName('top_number').setDescription('رقم التوب').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    raidResetCommand: new SlashCommandBuilder()
        .setName('raid-reset')
        .setDescription('تصفير النقاط')
        .addUserOption(o => o.setName('member').setDescription('العضو (اختياري)').setRequired(false)),

    // دوال المساعدة للوحات
    async updateSingleBoard(client, gid, guild, startIdx, endIdx, channelKey, msgKey) {
        const data = loadRaidData();
        if (!data[gid]) return;
        const gData = data[gid];
        const channelId = gData[channelKey];
        if (!channelId) return;
        const channel = guild.channels.cache.get(channelId) || await guild.channels.fetch(channelId).catch(() => null);
        if (!channel) return;

        const stats = gData.raider_stats || {};
        const blacklist = gData.blacklist || [];
        const cdict = gData.member_countries || {};
        const robDict = gData.roblox_users || {};
        const customAvs = gData.custom_avatars || {};

        const filtered = Object.entries(stats).filter(([u, c]) => !blacklist.includes(u) && c > 0);
        const sortedTop = filtered.sort((a, b) => b[1] - a[1]);
        const sliceTop = sortedTop.slice(startIdx, endIdx);

        if (sliceTop.length === 0) return;

        const embeds = [];
        for (let idx = 0; idx < sliceTop.length; idx++) {
            const [uid, cnt] = sliceTop[idx];
            const i = startIdx + idx + 1;
            const member = guild.members.cache.get(uid) || client.users.cache.get(uid);
            const memberMention = member ? member.toString() : `<@${uid}>`;

            const cou = cdict[uid] || "—";
            const robUser = robDict[uid] || "—";

            const textDesc = `╔══『 TOP ${i} 』══╗\n│  | ${memberMention} |\n│  <<< • ${robUser} • >>>\n│  \n│  Country: ${cou}\n│  —\n│  Raids Joined: ${cnt}`;
            const emb = new EmbedBuilder().setColor(EMBED_COLOR).setDescription(textDesc);

            if (customAvs[i.toString()]) {
                emb.setThumbnail(customAvs[i.toString()]);
            } else if (robUser !== "—") {
                const thumbUrl = /^\d+$/.test(robUser)
                    ? `https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds=${robUser}&size=420x420&format=Png&isCircular=false`
                    : `https://www.roblox.com/headshot-thumbnail/image?username=${robUser}&width=420&height=420&format=png`;
                emb.setThumbnail(thumbUrl);
            }

            emb.setImage(GIF_BANNER_URL);
            embeds.push(emb);
        }

        const msgId = gData[msgKey];
        try {
            if (msgId) {
                const msg = await channel.messages.fetch(msgId).catch(() => null);
                if (msg) {
                    await msg.edit({ content: "@here", embeds });
                    return;
                }
            }
        } catch (e) {}

        const newMsg = await channel.send({ content: "@here", embeds });
        gData[msgKey] = newMsg.id;
        saveRaidData(data);
    },

    async updateAllTops(client, gid, guild) {
        await module.exports.updateSingleBoard(client, gid, guild, 0, 10, "top10_channel_id", "top10_message_id");
        await module.exports.updateSingleBoard(client, gid, guild, 10, 20, "top20_channel_id", "top20_message_id");
    },

    startWeeklyWebhookLoop(client) {
        setInterval(async () => {
            const data = loadRaidData();
            for (const [gid, gData] of Object.entries(data)) {
                const guild = client.guilds.cache.get(gid);
                if (guild) {
                    await module.exports.updateAllTops(client, gid, guild);
                    gData.raider_stats = {};
                    gData.win_streak = 0;
                    saveRaidData(data);
                }
            }
        }, 168 * 60 * 60 * 1000);
    },

    // معالجة الأوامر
    async handleSetTop10Channel(interaction) {
        const gid = interaction.guildId;
        const channel = interaction.options.getChannel('channel');
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };
        
        data[gid].top10_channel_id = channel.id;
        delete data[gid].top10_message_id;
        saveRaidData(data);

        await interaction.reply({ content: `✅ | تم تعيين قناة توب 10 إلى ${channel} !`, ephemeral: true });
        await module.exports.updateSingleBoard(interaction.client, gid, interaction.guild, 0, 10, "top10_channel_id", "top10_message_id");
    },

    async handleSetTop20Channel(interaction) {
        const gid = interaction.guildId;
        const channel = interaction.options.getChannel('channel');
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };
        
        data[gid].top20_channel_id = channel.id;
        delete data[gid].top20_message_id;
        saveRaidData(data);

        await interaction.reply({ content: `✅ | تم تعيين قناة توب 20 إلى ${channel} !`, ephemeral: true });
        await module.exports.updateSingleBoard(interaction.client, gid, interaction.guild, 10, 20, "top20_channel_id", "top20_message_id");
    },

    async handleAvatarRobloxTop(interaction) {
        await interaction.showModal(new RobloxTopAvatarModal());
    },

    async handleSetCountry(interaction) {
        const gid = interaction.guildId;
        const member = interaction.options.getMember('member');
        const countryValue = interaction.options.getString('country_value');
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };

        data[gid].member_countries[member.id] = countryValue.trim();
        saveRaidData(data);

        await interaction.reply({ content: `✅ | تم تحديث دولة ${member}`, ephemeral: true });
        await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
    },

    async handleEndRaid(interaction) {
        if (BYPASS_IDS.has(interaction.user.id)) {
            await interaction.showModal(new RaidEndInfoModal());
            return;
        }
        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            await interaction.reply({ content: "❌ | ليس لديك صلاحية!", ephemeral: true });
            return;
        }
        const gid = interaction.guildId;
        const now = Date.now() / 1000;
        const cd = 3 * 3600;
        if (adminCooldows.has(gid) && now - adminCooldows.get(gid) < cd) {
            const rem = Math.floor(cd - (now - adminCooldows.get(gid)));
            await interaction.reply({ content: `⏳ انتظر \`${Math.floor(rem / 3600)}س و ${Math.floor((rem % 3600) / 60)}د\``, ephemeral: true });
            return;
        }
        adminCooldows.set(gid, now);
        await interaction.showModal(new RaidEndInfoModal());
    },

    async handleSetRoblox(interaction) {
        const gid = interaction.guildId;
        const username = interaction.options.getString('username');
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };

        data[gid].roblox_users[interaction.user.id] = username.trim();
        saveRaidData(data);

        await interaction.reply({ content: `✅ | تم ربط يوزر روبلوكس الخاص بك (\`${username.trim()}\`)`, ephemeral: true });
        await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
    },

    async handleSetRobloxUser(interaction) {
        const gid = interaction.guildId;
        const member = interaction.options.getMember('member');
        const username = interaction.options.getString('username');
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };

        data[gid].roblox_users[member.id] = username.trim();
        saveRaidData(data);

        await interaction.reply({ content: `✅ | تم ربط يوزر روبلوكس \`${username.trim()}\` لـ ${member}`, ephemeral: true });
        await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
    },

    async handleSync(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ | للمالك فقط!", ephemeral: true });
            return;
        }
        await interaction.deferReply({ ephemeral: true });
        const synced = await interaction.client.application.commands.fetch();
        await interaction.followup({ content: `✅ | تمت المزامنة بنجاح (\`${synced.size}\` أمر)`, ephemeral: true });
    },

    async handleRaidMentions(interaction) {
        const content = interaction.options.getString('mentions_content');
        const emb = new EmbedBuilder().setTitle("👤 | Mentions").setDescription(content).setColor(EMBED_COLOR);
        await interaction.reply({ embeds: [emb] });
    },

    async handleRaidList(interaction) {
        const gid = interaction.guildId;
        const data = loadRaidData();
        if (!data[gid] || !data[gid].raider_stats || Object.keys(data[gid].raider_stats).length === 0) {
            await interaction.reply({ content: "❌ | لا توجد مسجلات رايدات حتى الآن!", ephemeral: true });
            return;
        }

        const stats = data[gid].raider_stats;
        const blacklist = data[gid].blacklist || [];

        const filtered = Object.entries(stats).filter(([u, c]) => !blacklist.includes(u) && c > 0);
        const sortedTop = filtered.sort((a, b) => b[1] - a[1]).slice(0, 50);

        if (sortedTop.length === 0) {
            await interaction.reply({ content: "❌ | لا توجد أي بيانات لعرضها!", ephemeral: true });
            return;
        }

        const lines = sortedTop.map(([uid, cnt], idx) => {
            let medal = `#${idx + 1}`;
            if (idx === 0) medal = "🥇";
            else if (idx === 1) medal = "🥈";
            else if (idx === 2) medal = "🥉";
            return `${medal} <@${uid}> ──> **${cnt}** Raids Won`;
        });

        const embeds = [];
        let currentDesc = "";
        for (const line of lines) {
            if (currentDesc.length + line.length + 1 > 3900) {
                embeds.push(new EmbedBuilder().setTitle("🏆 | Top Raid Participants").setDescription(currentDesc).setColor(EMBED_COLOR));
                currentDesc = line + "\n";
            } else {
                currentDesc += line + "\n";
            }
        }
        if (currentDesc) {
            embeds.push(new EmbedBuilder().setTitle("🏆 | Top Raid Participants").setDescription(currentDesc).setColor(EMBED_COLOR));
        }

        await interaction.reply({ embeds: [embeds[0]], ephemeral: false });
        for (const extraEmb of embeds.slice(1)) {
            await interaction.channel.send({ embeds: [extraEmb] });
        }
    },

    async handleRaidAdd(interaction) {
        if (!BYPASS_IDS.has(interaction.user.id) && !interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            await interaction.reply({ content: "❌ | ليس لديك صلاحية!", ephemeral: true });
            return;
        }
        const gid = interaction.guildId;
        const member = interaction.options.getMember('member');
        const amount = interaction.options.getInteger('amount');
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };

        const current = data[gid].raider_stats[member.id] || 0;
        const newTotal = current + amount;
        data[gid].raider_stats[member.id] = newTotal;
        saveRaidData(data);

        const statsCog = interaction.client.memberStatsCog;
        if (statsCog && typeof statsCog.processMemberRaidUpdate === 'function') {
            await statsCog.processMemberRaidUpdate(interaction.guild, member, newTotal);
        }

        await interaction.reply({ content: `✅ | تمت إضافة \`${amount}\` رايد لـ ${member} وأصبح إجمالي رصيده: \`${newTotal}\``, ephemeral: true });
        await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
    },

    async handleRaidSet(interaction) {
        if (!BYPASS_IDS.has(interaction.user.id) && !interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
            await interaction.reply({ content: "❌ | ليس لديك صلاحية!", ephemeral: true });
            return;
        }
        const gid = interaction.guildId;
        const member = interaction.options.getMember('member');
        const amount = interaction.options.getInteger('amount');
        const data = loadRaidData();
        if (!data[gid]) data[gid] = { raider_stats: {}, win_streak: 0, roblox_users: {}, member_countries: {}, custom_avatars: {}, blacklist: [] };

        data[gid].raider_stats[member.id] = amount;
        saveRaidData(data);

        const statsCog = interaction.client.memberStatsCog;
        if (statsCog && typeof statsCog.processMemberRaidUpdate === 'function') {
            await statsCog.processMemberRaidUpdate(interaction.guild, member, amount);
        }

        await interaction.reply({ content: `✅ | تم تعيين رصيد ${member} مباشرة إلى: \`${amount}\` رايد`, ephemeral: true });
        await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
    },

    async handleSetAvatarRemove(interaction) {
        const gid = interaction.guildId;
        const topNumber = interaction.options.getInteger('top_number');
        const data = loadRaidData();
        if (data[gid] && data[gid].custom_avatars && data[gid].custom_avatars[topNumber.toString()]) {
            delete data[gid].custom_avatars[topNumber.toString()];
            saveRaidData(data);
            await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
            await interaction.reply({ content: `✅ | تم إزالة الصورة المخصصة للتوب رقم \`${topNumber}\` بنجاح.`, ephemeral: true });
            return;
        }
        await interaction.reply({ content: `❌ | لا توجد صورة مخصصة مسجلة للتوب رقم \`${topNumber}\`.`, ephemeral: true });
    },

    async handleRaidReset(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ | للمالك فقط!", ephemeral: true });
            return;
        }
        const gid = interaction.guildId;
        const member = interaction.options.getMember('member');
        const data = loadRaidData();
        if (!data[gid]) {
            await interaction.reply({ content: "❌ | لا توجد بيانات!", ephemeral: true });
            return;
        }
        if (member) {
            data[gid].raider_stats[member.id] = 0;
            saveRaidData(data);
            await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
            await interaction.reply({ content: `✅ | تم تصفير نقاط العضو`, ephemeral: true });
        } else {
            data[gid].raider_stats = {};
            data[gid].win_streak = 0;
            data[gid].custom_avatars = {};
            saveRaidData(data);
            await module.exports.updateAllTops(interaction.client, gid, interaction.guild);
            await interaction.reply({ content: "✅ | تم تصفير السيرفر بالكامل.", ephemeral: true });
        }
    }
};
