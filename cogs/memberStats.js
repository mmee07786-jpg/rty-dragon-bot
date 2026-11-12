const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const STATS_FILE = path.join(__dirname, '../stats.json');
const RAID_DATA_FILE = path.join(__dirname, '../raid_data.json');
const ROLES_CONFIG_FILE = path.join(__dirname, '../raid_roles.json');

// بعد كم يوم بدون رايد يتصفّر الستريك الحالي
const INACTIVE_DAYS = 7;

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
            fs.writeFileSync(ROLES_CONFIG_FILE, JSON.stringify({ raid_roles: {}, top_roles: [] }, null, 4), 'utf8');
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
        if (!fs.existsSync(ROLES_CONFIG_FILE)) return { raid_roles: {}, top_roles: [] };
        try {
            const data = JSON.parse(fs.readFileSync(ROLES_CONFIG_FILE, 'utf8'));
            if (!data.raid_roles) data.raid_roles = {};
            if (!data.top_roles) data.top_roles = [];
            return data;
        } catch (e) {
            return { raid_roles: {}, top_roles: [] };
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

    // /set-raid-role raids:<رقم> role:<رتبة>
    async handleSetRaidRole(interaction) {
        const raids = interaction.options.getInteger('raids');
        const role = interaction.options.getRole('role');

        if (raids < 1) {
            await interaction.reply({ content: "❌ | عدد الرايدات لازم يكون 1 أو أكثر.", ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });

        const config = this.getConfigData();
        const gid = interaction.guildId;
        if (!config.raid_roles[gid]) config.raid_roles[gid] = {};
        config.raid_roles[gid][raids.toString()] = role.id;
        this.saveConfigData(config);

        // منح الرتبة فوراً لمن وصل العدد
        const stats = this.getRaidData()[gid]?.raider_stats || {};
        let given = 0;
        for (const [uid, count] of Object.entries(stats)) {
            if (count < raids) continue;
            const member = await interaction.guild.members.fetch(uid).catch(() => null);
            if (!member || member.roles.cache.has(role.id)) continue;
            try {
                await member.roles.add(role, `رتبة رايدات (${raids})`);
                given++;
            } catch (e) {}
        }

        await interaction.editReply({
            content: `✅ | تم ربط الرتبة ${role} بـ \`${raids}\` رايد، وتم منحها لـ \`${given}\` عضو حالياً.`
        });
    }

    // /remove-raid-role raids:<رقم>
    async handleRemoveRaidRole(interaction) {
        const raids = interaction.options.getInteger('raids');
        const config = this.getConfigData();
        const gid = interaction.guildId;
        const serverRoles = config.raid_roles[gid] || {};

        if (!serverRoles[raids.toString()]) {
            await interaction.reply({ content: `❌ | ما فيه رتبة مربوطة بـ \`${raids}\` رايد.`, ephemeral: true });
            return;
        }

        const roleId = serverRoles[raids.toString()];
        delete serverRoles[raids.toString()];
        config.raid_roles[gid] = serverRoles;
        this.saveConfigData(config);

        await interaction.reply({ content: `✅ | تم حذف ربط الرتبة <@&${roleId}> من \`${raids}\` رايد (الرتبة تبقى عند الأعضاء الحاليين).`, ephemeral: true });
    }

    // /raid-roles-list
    async handleRaidRolesList(interaction) {
        const config = this.getConfigData();
        const gid = interaction.guildId;
        const raidRoles = config.raid_roles[gid] || {};
        const topRoles = config.top_roles.filter(r => r.guild_id === gid);

        const raidLines = Object.keys(raidRoles)
            .map(k => parseInt(k))
            .sort((a, b) => a - b)
            .map(n => `• \`${n}\` رايد ➜ <@&${raidRoles[n.toString()]}>`);

        const topLines = topRoles
            .sort((a, b) => a.min_rank - b.min_rank)
            .map(r => `• التوب \`${r.min_rank}\` - \`${r.max_rank}\` ➜ <@&${r.role_id}>`);

        if (raidLines.length === 0 && topLines.length === 0) {
            await interaction.reply({ content: "❌ | ما فيه أي رتب رايدات أو توبات مسجّلة. استخدم `/set-raid-role`.", ephemeral: true });
            return;
        }

        const embed = new EmbedBuilder()
            .setTitle("🏅 | رتب الرايدات")
            .setColor(0x8B0000)
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
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    removeRaidRoleCommand: new SlashCommandBuilder()
        .setName('remove-raid-role')
        .setDescription('حذف ربط رتبة بعدد رايدات معين')
        .addIntegerOption(o => o.setName('raids').setDescription('عدد الرايدات المربوط بالرتبة').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    raidRolesListCommand: new SlashCommandBuilder()
        .setName('raid-roles-list')
        .setDescription('عرض رتب الرايدات والتوبات المسجّلة')
};
