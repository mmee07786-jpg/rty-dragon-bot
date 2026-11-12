const {
    SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder,
    ActionRowBuilder, ButtonBuilder, ButtonStyle,
    ModalBuilder, TextInputBuilder, TextInputStyle
} = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../data.json');

const EMBED_COLOR = 0xFF0000;
// عدد التنبيهات قبل ما البوت ينفذ العقوبة (ضع 0 لعقوبة فورية من أول مخالفة)
const WARNINGS_BEFORE_PUNISHMENT = 2;
const PAGE_SIZE = 20;
const DEFAULT_PUNISHMENT = { type: 'timeout', minutes: 10 };
const TIMEOUT_OPTIONS = [1, 10, 30, 60];

// تخزين عدد المخالفات المؤقتة (guildId-userId -> Count)
const warningsCount = {};

// ───────────────────────── تخزين ─────────────────────────

function loadData() {
    if (fs.existsSync(DATA_FILE)) {
        try {
            return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
        } catch (error) {
            return {};
        }
    }
    return {};
}

function saveData(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ البيانات:", error);
    }
}

function ensureGuild(data, gid) {
    if (!data.automod) data.automod = {};
    if (!data.automod[gid]) data.automod[gid] = { words: [], channel_id: null, enabled: true };
    if (!Array.isArray(data.automod[gid].words)) data.automod[gid].words = [];
    return data.automod[gid];
}

// ───────────────────────── مساعدات ─────────────────────────

function safe(text) {
    return String(text).replace(/`/g, "'");
}

function minutesLabel(m) {
    if (m === 1) return "دقيقة | 1 min";
    if (m === 10) return "10 دقائق | 10 min";
    if (m === 30) return "30 دقيقة | 30 min";
    if (m === 60) return "ساعة | 1 hour";
    return `${m} دقيقة`;
}

function describePunishment(p) {
    if (p.type === 'kick') return "👢 طرد | Kick";
    if (p.type === 'ban') return "🔨 باند | Ban";
    return `⏳ تايم أوت | Timeout (${minutesLabel(p.minutes)})`;
}

function isAdmin(interaction) {
    return interaction.memberPermissions?.has(PermissionFlagsBits.Administrator);
}

// ───────────────────────── واجهات (Views) ─────────────────────────

function buildListView(guildId, page = 0, notice = "") {
    const words = loadData().automod?.[guildId]?.words || [];
    const totalPages = Math.max(1, Math.ceil(words.length / PAGE_SIZE));
    page = Math.min(Math.max(page, 0), totalPages - 1);

    const embed = new EmbedBuilder().setColor(EMBED_COLOR).setTitle("🚫 | الكلمات الممنوعة | Banned Words");
    const head = notice ? `${notice}\n\n` : "";

    if (words.length === 0) {
        embed.setDescription(`${head}ما فيه كلمات ممنوعة مسجّلة. استخدم \`/add_badword\`\nNo banned words yet.`);
        return { embeds: [embed], components: [] };
    }

    const start = page * PAGE_SIZE;
    const slice = words.slice(start, start + PAGE_SIZE);
    const lines = slice.map((w, i) => `**${start + i + 1}.** \`${safe(w)}\``);
    embed.setDescription(`${head}${lines.join("\n")}\n\nاختر رقم الكلمة لحذفها\nPick a number to delete it`);
    embed.setFooter({ text: `الصفحة ${page + 1}/${totalPages} | Page ${page + 1}/${totalPages}` });

    const rows = [];
    for (let i = 0; i < slice.length; i += 5) {
        const row = new ActionRowBuilder();
        slice.slice(i, i + 5).forEach((w, j) => {
            const globalIdx = start + i + j;
            row.addComponents(
                new ButtonBuilder()
                    .setCustomId(`ab_pick:${globalIdx}`)
                    .setLabel(String(globalIdx + 1))
                    .setStyle(ButtonStyle.Secondary)
            );
        });
        rows.push(row);
    }

    if (totalPages > 1) {
        rows.push(new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId(`ab_page:${page - 1}`).setLabel("السابق | Prev").setEmoji("◀️").setStyle(ButtonStyle.Primary).setDisabled(page === 0),
            new ButtonBuilder().setCustomId(`ab_page:${page + 1}`).setLabel("التالي | Next").setEmoji("▶️").setStyle(ButtonStyle.Primary).setDisabled(page >= totalPages - 1)
        ));
    }

    return { embeds: [embed], components: rows };
}

function buildWordView(guildId, index) {
    const words = loadData().automod?.[guildId]?.words || [];
    const word = words[index];
    if (word === undefined) {
        return buildListView(guildId, 0, "❌ | هذي الكلمة ما عادت موجودة.\nThis word no longer exists.");
    }

    const embed = new EmbedBuilder()
        .setColor(EMBED_COLOR)
        .setTitle("🚫 | كلمة ممنوعة | Banned Word")
        .setDescription(`🔤 \`${safe(word)}\``);

    const row = new ActionRowBuilder().addComponents(
        new ButtonBuilder().setCustomId(`ab_del:${index}`).setLabel("حذف | Delete").setEmoji("🗑️").setStyle(ButtonStyle.Danger),
        new ButtonBuilder().setCustomId(`ab_back:${Math.floor(index / PAGE_SIZE)}`).setLabel("رجوع | Back").setEmoji("⬅️").setStyle(ButtonStyle.Secondary)
    );
    return { embeds: [embed], components: [row] };
}

function buildPunishmentView(guildId, notice = "") {
    const p = loadData().automod?.[guildId]?.punishment || DEFAULT_PUNISHMENT;
    const head = notice ? `${notice}\n\n` : "";

    const embed = new EmbedBuilder()
        .setColor(EMBED_COLOR)
        .setTitle("⚖️ | عقوبة الكلمات الممنوعة | Automod Punishment")
        .setDescription(
            `${head}العقوبة الحالية | Current: **${describePunishment(p)}**\n\n` +
            `البوت ينفذها تلقائياً على العضو بعد ${WARNINGS_BEFORE_PUNISHMENT} تنبيهات.\n` +
            `اختر عقوبة جديدة من الأزرار تحت، وتقدر تغيرها بأي وقت.\n` +
            `Bot applies it automatically after ${WARNINGS_BEFORE_PUNISHMENT} warnings. Change it anytime.`
        );

    const mark = t => (p.type === t ? "✅ " : "");
    const row = new ActionRowBuilder().addComponents(
        new ButtonBuilder().setCustomId("ab_pun:kick").setLabel(`${mark('kick')}طرد | Kick`).setEmoji("👢").setStyle(ButtonStyle.Secondary),
        new ButtonBuilder().setCustomId("ab_pun:ban").setLabel(`${mark('ban')}باند | Ban`).setEmoji("🔨").setStyle(ButtonStyle.Danger),
        new ButtonBuilder().setCustomId("ab_pun:timeout").setLabel(`${mark('timeout')}تايم أوت | Timeout`).setEmoji("⏳").setStyle(ButtonStyle.Primary)
    );
    return { embeds: [embed], components: [row] };
}

function buildDurationView() {
    const embed = new EmbedBuilder()
        .setColor(EMBED_COLOR)
        .setTitle("⏳ | مدة التايم أوت | Timeout Duration")
        .setDescription("اختر مدة التايم أوت\nChoose the timeout duration");

    const row = new ActionRowBuilder();
    TIMEOUT_OPTIONS.forEach(m => {
        row.addComponents(
            new ButtonBuilder().setCustomId(`ab_dur:${m}`).setLabel(minutesLabel(m)).setStyle(ButtonStyle.Primary)
        );
    });
    const backRow = new ActionRowBuilder().addComponents(
        new ButtonBuilder().setCustomId("ab_punback").setLabel("رجوع | Back").setEmoji("⬅️").setStyle(ButtonStyle.Secondary)
    );
    return { embeds: [embed], components: [row, backRow] };
}

// ───────────────────────── تنفيذ العقوبة ─────────────────────────

async function applyPunishment(message, triggeredWord, punishment) {
    const member = message.member || await message.guild.members.fetch(message.author.id).catch(() => null);
    if (!member) return { ok: false, error: "العضو غير موجود" };

    const reason = `استخدام كلمة ممنوعة متكررة: ${triggeredWord}`;
    try {
        if (punishment.type === 'kick') {
            await member.kick(reason);
        } else if (punishment.type === 'ban') {
            await member.ban({ reason });
        } else {
            await member.timeout(punishment.minutes * 60 * 1000, reason);
        }
        return { ok: true };
    } catch (e) {
        return { ok: false, error: e.message };
    }
}

// ───────────────────────── التصدير ─────────────────────────

module.exports = {
    setModChannelCommand: new SlashCommandBuilder()
        .setName('set_mod_channel')
        .setDescription('[خاص بالإدارة] تعيين روم تنبيهات المخالفات والكلمات الممنوعة')
        .addChannelOption(option =>
            option.setName('channel')
                .setDescription('روم الإدارة للتنبيهات')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    automodToggleCommand: new SlashCommandBuilder()
        .setName('automod_toggle')
        .setDescription('[خاص بالإدارة] تفعيل أو إلغاء تفعيل حماية الكلمات الممنوعة بالسيرفر')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    addBadwordCommand: new SlashCommandBuilder()
        .setName('add_badword')
        .setDescription('[خاص بالإدارة] إضافة كلمة أو عبارة ممنوعة')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    badwordsListCommand: new SlashCommandBuilder()
        .setName('badwords_list')
        .setDescription('[خاص بالإدارة] عرض الكلمات الممنوعة وحذف أي كلمة منها')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    punishmentCommand: new SlashCommandBuilder()
        .setName('automod_punishment')
        .setDescription('[خاص بالإدارة] تحديد عقوبة الكلمات الممنوعة (طرد / باند / تايم أوت)')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleSetModChannel(interaction) {
        const channel = interaction.options.getChannel('channel');
        const data = loadData();
        ensureGuild(data, interaction.guildId).channel_id = channel.id;
        saveData(data);
        await interaction.reply({ content: `✅ | تم بنجاح تعيين روم الإدارة للتنبيهات إلى: ${channel}`, ephemeral: true });
    },

    async handleAutomodToggle(interaction) {
        const data = loadData();
        const g = ensureGuild(data, interaction.guildId);
        g.enabled = !(g.enabled ?? true);
        saveData(data);
        await interaction.reply({
            content: `🛡️ | حالة نظام الحماية التلقائية الآن: **${g.enabled ? "مفعل ✅" : "معطل ❌"}**`,
            ephemeral: true
        });
    },

    // يفتح نافذة تسأله: شنو الكلمة أو العبارة؟
    async handleAddBadword(interaction) {
        const wordInput = new TextInputBuilder()
            .setCustomId("word")
            .setLabel("الكلمة أو العبارة | Word or phrase")
            .setStyle(TextInputStyle.Short)
            .setRequired(true)
            .setMaxLength(100)
            .setPlaceholder("اكتب كلمة وحدة أو عبارة معينة");

        const modal = new ModalBuilder()
            .setCustomId("ab_add_modal")
            .setTitle("🚫 | إضافة كلمة ممنوعة | Add Word")
            .addComponents(new ActionRowBuilder().addComponents(wordInput));

        await interaction.showModal(modal);
    },

    async handleModal(interaction) {
        if (!isAdmin(interaction)) {
            await interaction.reply({ content: "❌ | ليس لديك صلاحية!", ephemeral: true });
            return;
        }
        if (!interaction.customId.startsWith('ab_add_modal')) return;

        const word = interaction.fields.getTextInputValue("word").trim().toLowerCase();
        if (!word) {
            await interaction.reply({ content: "❌ | اكتب كلمة أو عبارة صحيحة.", ephemeral: true });
            return;
        }

        const data = loadData();
        const g = ensureGuild(data, interaction.guildId);
        if (g.words.includes(word)) {
            await interaction.reply({ content: `⚠️ | **\`${safe(word)}\`** موجودة مسبقاً في قائمة الكلمات الممنوعة!`, ephemeral: true });
            return;
        }

        g.words.push(word);
        saveData(data);
        await interaction.reply({ content: `✅ | تمت إضافة **\`${safe(word)}\`** إلى قائمة الحظر بنجاح.`, ephemeral: true });
    },

    async handleBadwordsList(interaction) {
        await interaction.reply({ ...buildListView(interaction.guildId, 0), ephemeral: true });
    },

    async handlePunishmentCommand(interaction) {
        await interaction.reply({ ...buildPunishmentView(interaction.guildId), ephemeral: true });
    },

    async handleButton(interaction) {
        if (!isAdmin(interaction)) {
            await interaction.reply({ content: "❌ | ليس لديك صلاحية!", ephemeral: true });
            return;
        }

        const [action, arg] = interaction.customId.split(':');
        const gid = interaction.guildId;

        if (action === 'ab_page' || action === 'ab_back') {
            await interaction.update(buildListView(gid, parseInt(arg)));
            return;
        }

        if (action === 'ab_pick') {
            await interaction.update(buildWordView(gid, parseInt(arg)));
            return;
        }

        if (action === 'ab_del') {
            const idx = parseInt(arg);
            const data = loadData();
            const g = ensureGuild(data, gid);
            const word = g.words[idx];
            if (word === undefined) {
                await interaction.update(buildListView(gid, 0, "❌ | هذي الكلمة ما عادت موجودة.\nThis word no longer exists."));
                return;
            }
            g.words.splice(idx, 1);
            saveData(data);
            await interaction.update(buildListView(
                gid,
                Math.floor(idx / PAGE_SIZE),
                `✅ | تم حذف \`${safe(word)}\` من القائمة.\nWord removed.`
            ));
            return;
        }

        if (action === 'ab_punback') {
            await interaction.update(buildPunishmentView(gid));
            return;
        }

        if (action === 'ab_pun') {
            if (arg === 'timeout') {
                await interaction.update(buildDurationView());
                return;
            }
            const data = loadData();
            const g = ensureGuild(data, gid);
            g.punishment = { type: arg };
            saveData(data);
            await interaction.update(buildPunishmentView(gid, `✅ | تم تعيين العقوبة: **${describePunishment(g.punishment)}**`));
            return;
        }

        if (action === 'ab_dur') {
            const minutes = parseInt(arg);
            const data = loadData();
            const g = ensureGuild(data, gid);
            g.punishment = { type: 'timeout', minutes };
            saveData(data);
            await interaction.update(buildPunishmentView(gid, `✅ | تم تعيين العقوبة: **${describePunishment(g.punishment)}**`));
        }
    },

    async handleMessage(message) {
        if (message.author.bot || !message.guild) return;
        if (message.member && message.member.permissions.has(PermissionFlagsBits.Administrator)) return;

        const guildId = message.guild.id;
        const automodData = loadData().automod?.[guildId] || {};

        if (automodData.enabled === false) return;

        const badWords = automodData.words || [];
        if (badWords.length === 0) return;

        const contentLower = message.content.toLowerCase();
        const triggeredWord = badWords.find(w => contentLower.includes(w));
        if (!triggeredWord) return;

        try { await message.delete(); } catch (e) {}

        const userKey = `${guildId}-${message.author.id}`;
        warningsCount[userKey] = (warningsCount[userKey] || 0) + 1;
        const strikes = warningsCount[userKey];

        // تنبيهات قبل العقوبة
        if (strikes <= WARNINGS_BEFORE_PUNISHMENT) {
            try {
                const warningMsg = await message.channel.send(
                    `⚠️ | ${message.author} احذر! لقد استخدمت كلمة ممنوعة (تنبيه رقم ${strikes}/${WARNINGS_BEFORE_PUNISHMENT}).`
                );
                setTimeout(async () => { try { await warningMsg.delete(); } catch (e) {} }, 5000);
            } catch (e) {}
            return;
        }

        // العقوبة تتنفذ تلقائياً من البوت
        warningsCount[userKey] = 0;
        const punishment = automodData.punishment || DEFAULT_PUNISHMENT;
        const result = await applyPunishment(message, triggeredWord, punishment);

        try {
            const note = await message.channel.send(
                result.ok
                    ? `🚨 | تم تطبيق عقوبة (${describePunishment(punishment)}) على ${message.author} بسبب تكرار الكلمات الممنوعة.`
                    : `⚠️ | ${message.author} تجاوز الحد، بس ما قدرت أطبق العقوبة (تحقق من صلاحياتي ورتبتي).`
            );
            setTimeout(async () => { try { await note.delete(); } catch (e) {} }, 8000);
        } catch (e) {}

        // سجل بروم الإدارة
        const modChannelId = automodData.channel_id;
        if (modChannelId) {
            const modChannel = message.guild.channels.cache.get(modChannelId);
            if (modChannel) {
                const embed = new EmbedBuilder()
                    .setTitle(result.ok ? "🚨 تم تنفيذ عقوبة تلقائية" : "⚠️ فشل تنفيذ العقوبة")
                    .setDescription(
                        `• **العضو:** ${message.author} (\`${message.author.id}\`)\n` +
                        `• **الروم:** ${message.channel}\n` +
                        `• **الكلمة الممنوعة:** \`${safe(triggeredWord)}\`\n` +
                        `• **العقوبة:** ${describePunishment(punishment)}\n` +
                        (result.ok ? "" : `• **سبب الفشل:** \`${result.error}\`\n`) +
                        `\n💬 **آخر رسالة:**\n> ${message.content.slice(0, 1000)}`
                    )
                    .setColor(result.ok ? 0xFF0000 : 0xFFA500);
                await modChannel.send({ embeds: [embed] }).catch(() => {});
            }
        }
    }
};
