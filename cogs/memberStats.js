const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const OWNER_ID = "1107355943408259112"; // أونر البوت الأساسي
const STATS_FILE = path.join(__dirname, '../stats.json');
const RAID_DATA_FILE = path.join(__dirname, '../raid_data.json');
const ROLES_CONFIG_FILE = path.join(__dirname, '../raid_roles.json');

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
            const data = fs.readFileSync(STATS_FILE, 'utf8');
            return JSON.parse(data);
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
            const data = fs.readFileSync(RAID_DATA_FILE, 'utf8');
            return JSON.parse(data);
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

    // الدالة المطلوبة للتحقق وتحديث التوبات وسحب ورقتة الرتبة ممن تراجع مستواه
    async processTopRanksUpdate(guild, gidStr) {
        await this.updateTopRolesForGuild(guild);
    }

    async checkAndApplyRaidRoles(guild, member, totalRaids) {
        const config = this.getConfigData();
        const gidStr = guild.id;
        const serverRaidRoles = config.raid_roles[gidStr] || {};
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
        const topRolesConfig = config.top_roles;
        const guildTopConfigs = topRolesConfig.filter(r => r.guild_id === guild.id);
        if (guildTopConfigs.length === 0) return;

        const statsData = this.getStatsData();
        const raidData = this.getRaidData();

        const memberRaidsMap = {};
        const serverRaidStore = raidData[gidStr]?.raider_stats || {};

        const allUserIds = new Set([...Object.keys(statsData), ...Object.keys(serverRaidStore)]);
        for (const uidStr of allUserIds) {
            const uid = parseInt(uidStr);
            if (isNaN(uid)) continue;

            const fileRaids = serverRaidStore[uidStr] || 0;
            const uStats = statsData[uidStr] || {};
            const alltimeR = Math.max(uStats.alltime_raids || 0, fileRaids);
            if (alltimeR > 0) memberRaidsMap[uid] = alltimeR;
        }

        const sortedMembers = Object.entries(memberRaidsMap).sort((a, b) => b[1] - a[1]);
        const allManagedRoleIds = new Set(guildTopConfigs.map(r => r.role_id));

        for (let index = 0; index < sortedMembers.length; index++) {
            const [uidStr, raids] = sortedMembers[index];
            const uid = parseInt(uidStr);
            const rank = index + 1;
            const member = await guild.members.fetch(uid).catch(() => null);
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
                } else {
                    if (member.roles.cache.has(roleObj.id)) {
                        try {
                            await member.roles.remove(roleObj, `خروج من نطاق التوب أو تراجع المستوى`);
                        } catch (e) {}
                    }
                }
            }
        }
    }

    startInactiveStreaksLoop() {
        setInterval(async () => {
            try {
                const statsData = this.getStatsData();
                const now = Date.now();
                let updated = false;

                for (const [userId, uData] of Object.entries(statsData)) {
                    const lastRaidStr = uData.last_raid_time;
                    if (lastRaidStr && (uData.win_streak_current
