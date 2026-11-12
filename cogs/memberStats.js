const {
    SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder,
    ModalBuilder, TextInputBuilder, TextInputStyle,
    ActionRowBuilder, ButtonBuilder, ButtonStyle
} = require('discord.js');
const fs = require('fs');
const path = require('path');

const STATS_FILE = path.join(__dirname, '../stats.json');
const RAID_DATA_FILE = path.join(__dirname, '../raid_data.json');
const ROLES_CONFIG_FILE = path.join(__dirname, '../raid_roles.json');

// بعد كم يوم بدون رايد يتصفّر الستريك الحالي
const INACTIVE_DAYS = 7;
const EMBED_COLOR = 0x8B0000;

class MemberStats {
    constructor(client) {
        this.client = client;
        this.loadFiles();
        this.startInactiveStreaksLoop();
    }

    loadFiles() {
        if (!fs.existsSync(STATS_FILE)) {
            fs.writeFileSync(STATS_FILE, JSON.stringify({}, null, 4), 'utf8');
        }
        if (!fs.existsSync(ROLES_CONFIG_FILE)) {
            fs.writeFileSync(ROLES_CONFIG_FILE, JSON.stringify({ raid_roles: {}, raid_role_descriptions: {}, top_roles: [] }, null, 4), 'utf8');
        }
    }

    getStatsData() {
        if (!fs.existsSync(STATS_FILE)) return {};
        try {
            return JSON.parse(fs.readFileSync(STATS_FILE, 'utf8'));
        } catch (e) {
            return {};
        }
    }

    saveStatsData(data) {
        fs.writeFileSync(STATS_FILE, JSON.stringify(data, null, 4), 'utf8');
    }

    getRaidData() {
        if (!fs.existsSync(RAID_DATA_FILE)) return {};
        try {
            return JSON.parse(fs.readFileSync(RAID_DATA_FILE, 'utf8'));
        } catch (e) {
            return {};
        }
    }

    getConfigData() {
        const empty = () => ({ raid_roles: {}, raid_role_descriptions: {}, top_roles: [] });
        if (!fs.existsSync(ROLES_CONFIG_FILE)) return empty();
        try {
            const data = JSON.parse(fs.readFileSync(ROLES_CONFIG_FILE, 'utf8'));
            if (!data.raid_roles) data.raid_roles = {};
            if (!data.raid_role_descriptions) data.raid_role_descriptions = {};
            if (!data.top_roles) data.top_roles = [];
            return data;
        } catch (e) {
            return empty();
        }
    }

    saveConfigData(data) {
        fs.writeFileSync(ROLES_CONFIG_FILE, JSON.stringify(data, null, 4), 'utf8');
    }

    async handleReady() {
        console.log("📊 | نظام إحصائيات ورتب الرايدات والتوبات جاهز للعمل بنجاح.");
    }

    // الدالة المركزية لتحديث رتب الفرد عند زيادة الرايدات
    async processMemberRaidUpdate(guild, member, totalRaids) {
        await this.checkAndApplyRaidRoles(guild, member, totalRaids);
        await this.updateTopRolesForGuild(guild);
    }

    async processTopRanksUpdate(guild, gidStr) {
        await this.updateTopRolesForGuild(guild);
    }

    async checkAndApplyRaidRoles(guild, member, totalRaids) {
        const config = this.getConfigData();
        const serverRaidRoles = config.raid_roles[guild.id] || {};
        if (Object.keys(serverRaidRoles).length === 0) return;

        const sortedThresholds = Object.keys(serverRaidRoles).map(k => parseInt(k)).sort((a, b) => a - b);
        for (const reqRaids of sortedThresholds) {
            const roleId = serverRaidRoles[reqRaids.toString()];
            const role = guild.roles.cache.get(roleId);
            if (!role) continue;

            if (totalRaids >= reqRaids) {
                if (!member.roles.cache.has(role.id)) {
                    try {
                        await member.roles.add(role, `الوصول إلى ${totalRaids} رايد`);
                    } catch (e) {
                        console.log(`⚠️ خطأ منح رتبة رايد: ${e.message}`);
                    }
                }
            }
        }
    }

    async updateTopRolesForGuild(guild) {
        const config = this.getConfigData();
        const gidStr = guild.id;
        const guildTopConfigs = config.top_roles.filter(r => r.guild_id === guild.id);
        if (guildTopConfigs.length === 0) return;

        const statsData = this.getStatsData();
        const raidData = this.getRaidData();

        const memberRaidsMap = {};
        const serverRaidStore = raidData[gidStr]?.raider_stats || {};

        const allUserIds = new Set([...Object.keys(statsData), ...Object.keys(serverRaidStore)]);
        for (const uidStr of allUserIds) {
            // ✅ نخلي الـ ID نص (parseInt يخرّب أرقام ديسكورد الكبيرة)
            if (!/^\d+$/.test(uidStr)) continue;

            const fileRaids = serverRaidStore[uidStr] || 0;
            const uStats = statsData[uidStr] || {};
            const alltimeR = Math.max(uStats.alltime_raids || 0, fileRaids);
            if (alltimeR > 0) memberRaidsMap[uidStr] = alltimeR;
        }

        const sortedMembers = Object.entries(memberRaidsMap).sort((a, b) => b[1] - a[1]);
        const allManagedRoleIds = new Set(guildTopConfigs.map(r => r.role_id));

        for (let index = 0; index < sortedMembers.length; index++) {
            const [uidStr] = sortedMembers[index];
            const rank = index + 1;
            const member = await guild.members.fetch(uidStr).catch(() => null);
            if (!member) continue;

            let deservedRoleId = null;
            for (const cfg of guildTopConfigs) {
                if (cfg.min_rank <= rank && rank <= cfg.max_rank) {
                    deservedRoleId = cfg.role_id;
                    break;
                }
            }

            for (const rId of allManagedRoleIds) {
                const roleObj = guild.roles.cache.get(rId);
                if (!roleObj) continue;

                if (rId === deservedRoleId) {
                    if (!member.roles.cache.has(roleObj.id)) {
                        try {
                            await member.roles.add(roleObj, `التوب التلقائي: المركز #${rank}`);
                        } catch (e) {}
                    }
                } else if (member.roles.cache.has(roleObj.id)) {
                    try {
                        await member.roles.remove(roleObj, `خروج من نطاق التوب أو تراجع المستوى`);
                    } catch (e) {}
                }
            }
        }
    }

    startInactiveStreaksLoop() {
        setInterval(async () => {
            try {
                const statsData = this.getStatsData();
                const now = Date.now();
                const limit = INACTIVE_DAYS * 24 * 3600 * 1000;
                let updated = false;

                for (const uData of Object.values(statsData)) {
                    if (!uData || !uData.last_raid_time) continue;

                    let last = Number(uData.last_raid_time);
                    if (isNaN(last)) last = new Date(uData.last_raid_time).getTime();
                    else if (last < 1e12) last *= 1000; // ثواني -> ميلي ثانية
                    if (isNaN(last)) continue;

                    if ((uData.win_streak_current || 0) > 0 && now - last > limit) {
                        uData.win_streak_current = 0;
                        updated = true;
                    }
                }

                if (updated) this.saveStatsData(statsData);
            } catch (e) {
                console.log(`⚠️ خطأ في حلقة الستريك: ${e.message}`);
            }
        }, 60 * 60 * 1000);
    }

    // ───────────────────────── رتب الرايدات ─────────────────────────

    // قائمة الرتب مرتبة من الأصغر للأكبر
    getSortedRaidRoles(gid) {
        const config = this.getConfigData();
        const roles = config.raid_roles[gid] || {};
        const descs = config.raid_role_descriptions[gid] || {};
        return Object.keys(roles)
            .map(k => parseInt(k))
            .filter(n => !isNaN(n))
            .sort((a, b) => a - b)
            .map(n => ({ raids: n, roleId: roles[n.toString()], description: descs[n.toString()] || "" }));
    }

    // يمنح الرتبة لكل من وصل العدد المطلوب
    async giveRoleToQualified(guild, raids, role) {
        const stats = this.getRaidData()[guild.id]?.raider_stats || {};
        let given = 0;
        for (const [uid, count] of Object.entries(stats)) {
            if (count < raids) continue;
            const member = await guild.members.fetch(uid).catch(() => null);
            if (!member || member.roles.cache.has(role.id)) continue;
            try {
                await member.roles.add(role, `رتبة رايدات (${raids})`);
                given++;
            } catch (e) {}
        }
        return given;
    }

    // /set-raid-role raids:<رقم> role:<رتبة> description:<اختياري>
    async handleSetRaidRole(interaction) {
        const raids = interaction.options.getInteger('raids');
        const role = interaction.options.getRole('role');
        const description = (interaction.options.getString('description') || "").trim();

        if (raids < 1) {
            await interaction.reply({ content: "❌ | عدد الرايدات لازم يكون 1 أو أكثر.", ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });

        const config = this.getConfigData();
        const gid = interaction.guildId;
        if (!config.raid_roles[gid]) config.raid_roles[gid] = {};
        if (!config.raid_role_descriptions[gid]) config.raid_role_descriptions[gid] = {};

        config.raid_roles[gid][raids.toString()] = role.id;
        if (description) config.raid_role_descriptions[gid][raids.toString()] = description;
        this.saveConfigData(config);

        const given = await this.giveRoleToQualified(interaction.guild, raids, role);

        await interaction.editReply({
            content: `✅ | تم ربط الرتبة ${role} بـ \`${raids}\` رايد${description ? ` (الوصف: ${description})` : ""}، وتم منحها لـ \`${given}\` عضو حالياً.`
        });
    }

    // ───────── /remove-raid-role : قائمة + أزرار ترقيم + حذف/تعديل ─────────

    buildRaidRolesListView(guild, notice) {
        const list = this.getSortedRaidRoles(guild.id).slice(0, 25);
        const embed = new EmbedBuilder().setColor(EMBED_COLOR).setTitle("🗑️ | إدارة رتب الرايدات | Manage Raid Roles");
        const head = notice ? `${notice}\n\n` : "";

        if (list.length === 0) {
            embed.setDescription(`${head}❌ | ما فيه رتب رايدات مسجّلة.\nNo raid roles configured.`);
            return { embeds: [embed], components: [] };
        }

        const lines = list.map((r, i) =>
            `**${i + 1}.** \`${r.raids}\` رايد ➜ <@&${r.roleId}>` + (r.description ? `\n╰ ${r.description}` : "")
        );
        embed.setDescription(`${head}${lines.join("\n\n")}\n\nاختر رقم الرتبة من الأزرار تحت\nPick a role number below`);

        const rows = [];
        for (let i = 0; i < list.length; i += 5) {
            const row = new ActionRowBuilder();
            list.slice(i, i + 5).forEach((r, j) => {
                row.addComponents(
                    new ButtonBuilder()
                        .setCustomId(`rr_pick:${r.raids}`)
                        .setLabel(String(i + j + 1))
                        .setStyle(ButtonStyle.Secondary)
                );
            });
            rows.push(row);
        }
        return { embeds: [embed], components: rows };
    }

    buildRaidRoleDetailView(guild, raids) {
        const r = this.getSortedRaidRoles(guild.id).find(x => x.raids === raids);
        if (!r) {
            return this.buildRaidRolesListView(guild, "❌ | هذي الرتبة ما عادت موجودة.\nThis role no longer exists.");
        }

        const embed = new EmbedBuilder()
            .setColor(EMBED_COLOR)
            .setTitle("🏅 | رتبة رايدات | Raid Role")
            .setDescription(
                `🎯 \`${r.raids}\` رايد ➜ <@&${r.roleId}>\n` +
                `📝 ${r.description || "—"}`
            );

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setCustomId(`rr_del:${r.raids}`).setLabel("حذف | Delete").setEmoji("🗑️").setStyle(ButtonStyle.Danger),
            new ButtonBuilder().setCustomId(`rr_edit:${r.raids}`).setLabel("تعديل | Edit").setEmoji("✏️").setStyle(ButtonStyle.Primary),
            new ButtonBuilder().setCustomId("rr_back").setLabel("رجوع | Back").setEmoji("⬅️").setStyle(ButtonStyle.Secondary)
        );
        return { embeds: [embed], components: [row] };
    }

    async handleRemoveRaidRole(interaction) {
        await interaction.reply({ ...this.buildRaidRolesListView(interaction.guild), ephemeral: true });
    }

    async handleRaidRoleButton(interaction) {
        if (!interaction.memberPermissions?.has(PermissionFlagsBits.Administrator)) {
            await interaction.reply({ content: "❌ | ليس لديك صلاحية!", ephemeral: true });
            return;
        }

        const [action, arg] = interaction.customId.split(':');
        const raids = parseInt(arg);
        const guild = interaction.guild;

        if (action === 'rr_back') {
            await interaction.update(this.buildRaidRolesListView(guild));
            return;
        }

        if (action === 'rr_pick') {
            await interaction.update(this.buildRaidRoleDetailView(guild, raids));
            return;
        }

        if (action === 'rr_del') {
            const config = this.getConfigData();
            const gid = guild.id;
            const roleId = config.raid_roles[gid]?.[raids.toString()];
            if (!roleId) {
                await interaction.update(this.buildRaidRolesListView(guild, "❌ | هذي الرتبة ما عادت موجودة.\nThis role no longer exists."));
                return;
            }
            delete config.raid_roles[gid][raids.toString()];
            if (config.raid_role_descriptions[gid]) delete config.raid_role_descriptions[gid][raids.toString()];
            this.saveConfigData(config);

            await interaction.update(this.buildRaidRolesListView(
                guild,
                `✅ | تم حذف ربط <@&${roleId}> من \`${raids}\` رايد (الرتبة تبقى عند الأعضاء الحاليين).\nRole link removed.`
            ));
            return;
        }

        if (action === 'rr_edit') {
            const r = this.getSortedRaidRoles(guild.id).find(x => x.raids === raids);
            if (!r) {
                await interaction.update(this.buildRaidRolesListView(guild, "❌ | هذي الرتبة ما عادت موجودة.\nThis role no longer exists."));
                return;
            }

            const raidsInput = new TextInputBuilder()
                .setCustomId("raids")
                .setLabel("عدد الرايدات | Raids Count")
                .setStyle(TextInputStyle.Short)
                .setRequired(true)
                .setValue(String(r.raids));

            const descInput = new TextInputBuilder()
                .setCustomId("description")
                .setLabel("وصف الرتبة | Role Description")
                .setStyle(TextInputStyle.Short)
                .setRequired(false)
                .setMaxLength(100);
            if (r.description) descInput.setValue(r.description);

            const modal = new ModalBuilder()
                .setCustomId(`rr_edit_modal:${r.raids}`)
                .setTitle("✏️ | تعديل الرتبة | Edit Raid Role")
                .addComponents(
                    new ActionRowBuilder().addComponents(raidsInput),
                    new ActionRowBuilder().addComponents(descInput)
                );

            await interaction.showModal(modal);
        }
    }

    async handleRaidRoleModal(interaction) {
        if (!interaction.memberPermissions?.has(PermissionFlagsBits.Administrator)) {
            await interaction.reply({ content: "❌ | ليس لديك صلاحية!", ephemeral: true });
            return;
        }

        const guild = interaction.guild;
        const gid = guild.id;
        const oldRaids = parseInt(interaction.customId.split(':')[1]);
        const newRaidsStr = interaction.fields.getTextInputValue('raids').trim();
        const description = interaction.fields.getTextInputValue('description').trim();

        if (!/^\d+$/.test(newRaidsStr) || parseInt(newRaidsStr) < 1) {
            await interaction.reply({ content: "❌ | اكتب عدد رايدات صحيح (1 أو أكثر).\nInvalid raids count.", ephemeral: true });
            return;
        }
        const newRaids = parseInt(newRaidsStr);

        const config = this.getConfigData();
        const roleId = config.raid_roles[gid]?.[oldRaids.toString()];
        if (!roleId) {
            await interaction.reply({ content: "❌ | هذي الرتبة ما عادت موجودة.\nThis role no longer exists.", ephemeral: true });
            return;
        }
        if (newRaids !== oldRaids && config.raid_roles[gid][newRaids.toString()]) {
            await interaction.reply({ content: `❌ | فيه رتبة ثانية مربوطة بـ \`${newRaids}\` رايد.\nAnother role already uses this count.`, ephemeral: true });
            return;
        }

        if (interaction.isFromMessage()) await interaction.deferUpdate();
        else await interaction.deferReply({ ephemeral: true });

        if (!config.raid_role_descriptions[gid]) config.raid_role_descriptions[gid] = {};
        delete config.raid_roles[gid][oldRaids.toString()];
        delete config.raid_role_descriptions[gid][oldRaids.toString()];

        config.raid_roles[gid][newRaids.toString()] = roleId;
        if (description) config.raid_role_descriptions[gid][newRaids.toString()] = description;
        this.saveConfigData(config);

        // لو تغيّر العدد، نمنح الرتبة لمن صار مؤهلاً
        if (newRaids !== oldRaids) {
            const role = guild.roles.cache.get(roleId);
            if (role) await this.giveRoleToQualified(guild, newRaids, role);
        }

        await interaction.editReply(this.buildRaidRolesListView(
            guild,
            `✅ | تم تعديل الرتبة <@&${roleId}> (\`${newRaids}\` رايد).\nRole updated.`
        ));
    }

    // /raid-roles-list
    async handleRaidRolesList(interaction) {
        const gid = interaction.guildId;
        const raidList = this.getSortedRaidRoles(gid);
        const topRoles = this.getConfigData().top_roles.filter(r => r.guild_id === gid);

        const raidLines = raidList.map(r =>
            `• \`${r.raids}\` رايد ➜ <@&${r.roleId}>` + (r.description ? `\n  ╰ ${r.description}` : "")
        );

        const topLines = topRoles
            .sort((a, b) => a.min_rank - b.min_rank)
            .map(r => `• التوب \`${r.min_rank}\` - \`${r.max_rank}\` ➜ <@&${r.role_id}>`);

        if (raidLines.length === 0 && topLines.length === 0) {
            await interaction.reply({ content: "❌ | ما فيه أي رتب رايدات أو توبات مسجّلة. استخدم `/set-raid-role`.", ephemeral: true });
            return;
        }

        const embed = new EmbedBuilder()
            .setTitle("🏅 | رتب الرايدات")
            .setColor(EMBED_COLOR)
            .addFields(
                { name: "رتب عدد الرايدات", value: raidLines.join("\n") || "—" },
                { name: "رتب التوب", value: topLines.join("\n") || "—" }
            );

        await interaction.reply({ embeds: [embed] });
    }
}

module.exports = {
    MemberStats,

    setRaidRoleCommand: new SlashCommandBuilder()
        .setName('set-raid-role')
        .setDescription('ربط رتبة بعدد رايدات معين (تنمنح تلقائياً)')
        .addIntegerOption(o => o.setName('raids').setDescription('عدد الرايدات المطلوب').setRequired(true))
        .addRoleOption(o => o.setName('role').setDescription('الرتبة').setRequired(true))
        .addStringOption(o => o.setName('description').setDescription('وصف الرتبة (اختياري - تقدر تتخطاه)').setRequired(false).setMaxLength(100))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    removeRaidRoleCommand: new SlashCommandBuilder()
        .setName('remove-raid-role')
        .setDescription('عرض رتب الرايدات لحذفها أو تعديلها')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    raidRolesListCommand: new SlashCommandBuilder()
        .setName('raid-roles-list')
        .setDescription('عرض رتب الرايدات والتوبات المسجّلة')
};
