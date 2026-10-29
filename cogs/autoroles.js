const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../data.json');

function loadData() {
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

function saveData(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ البيانات:", error);
    }
}

module.exports = {
    autoroleAddCommand: new SlashCommandBuilder()
        .setName('autorole_add')
        .setDescription('[خاص بالإدارة] إضافة رتبة لتُعطى تلقائياً لكل عضو جديد يدخل السيرفر')
        .addRoleOption(option =>
            option.setName('role')
                .setDescription('الرتبة المراد إضافتها')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    autoroleRemoveCommand: new SlashCommandBuilder()
        .setName('autorole_remove')
        .setDescription('[خاص بالإدارة] إزالة رتبة من قائمة الرتب التلقائية')
        .addRoleOption(option =>
            option.setName('role')
                .setDescription('الرتبة المراد إزالتها')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    autoroleToggleCommand: new SlashCommandBuilder()
        .setName('autorole_toggle')
        .setDescription('[خاص بالإدارة] تفعيل أو إلغاء تفعيل نظام الرتب التلقائية بالكامل')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    autoroleListCommand: new SlashCommandBuilder()
        .setName('autorole_list')
        .setDescription('[خاص بالإدارة] عرض جميع الرتب التلقائية المعينة حالياً بالسيرفر')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleAutoroleAdd(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const role = interaction.options.getRole('role');
        const data = loadData();

        if (!data.autoroles) data.autoroles = {};
        if (!data.autoroles[guildId]) {
            data.autoroles[guildId] = { roles: [], enabled: true };
        }

        if (Array.isArray(data.autoroles[guildId])) {
            const oldList = data.autoroles[guildId];
            data.autoroles[guildId] = { roles: oldList, enabled: true };
        }

        if (data.autoroles[guildId].roles.includes(role.id)) {
            await interaction.followup.send({ content: `⚠️ | الرتبة ${role} موجودة مسبقاً في قائمة الرتب التلقائية!`, ephemeral: true });
            return;
        }

        if (role.position >= interaction.guild.members.me.roles.highest.position) {
            await interaction.followup.send({ content: "❌ | عذراً، رتبة البوت أدنى من هذه الرتبة أو تساواها، يجب أن تكون رتبة البوت أعلى!", ephemeral: true });
            return;
        }

        data.autoroles[guildId].roles.push(role.id);
        saveData(data);

        await interaction.followup.send(`✅ | تم بنجاح إضافة الرتبة ${role} إلى قائمة الرتب التلقائية للأعضاء الجدد.`);
    },

    async handleAutoroleRemove(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const role = interaction.options.getRole('role');
        const data = loadData();

        if (!data.autoroles || !data.autoroles[guildId]) {
            await interaction.followup.send({ content: "❌ | لا توجد أي رتب تلقائية مسجلة في هذا السيرفر أساساً!", ephemeral: true });
            return;
        }

        const guildData = data.autoroles[guildId];
        const roleList = Array.isArray(guildData) ? guildData : guildData.roles;

        const index = roleList.indexOf(role.id);
        if (index > -1) {
            roleList.splice(index, 1);
            saveData(data);
            await interaction.followup.send(`🗑️ | تم إزالة الرتبة ${role} من قائمة الرتب التلقائية بنجاح.`);
        } else {
            await interaction.followup.send({ content: `❌ | هذه الرتبة غير موجودة في قائمة الرتب التلقائية.`, ephemeral: true });
        }
    },

    async handleAutoroleToggle(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const data = loadData();

        if (!data.autoroles || !data.autoroles[guildId]) {
            await interaction.followup.send({ content: "❌ | لم تقم بإضافة أي رتب تلقائية بعد لتفعيل/إلغاء النظام.", ephemeral: true });
            return;
        }

        let guildData = data.autoroles[guildId];
        if (Array.isArray(guildData)) {
            data.autoroles[guildId] = { roles: guildData, enabled: true };
            guildData = data.autoroles[guildId];
        }

        const currentState = guildData.enabled ?? true;
        const newState = !currentState;
        guildData.enabled = newState;
        saveData(data);

        const statusText = newState ? "مفعل ✅" : "معطل (ملغي) ❌";
        await interaction.followup.send(`🛡️ | حالة نظام الرتب التلقائية أصبحت الآن: **${statusText}**`);
    },

    async handleAutoroleList(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const data = loadData();

        const guildData = data.autoroles?.[guildId];
        if (!guildData) {
            await interaction.followup.send("📋 | لا توجد أي رتب تلقائية مفعلة في هذا السيرفر حالياً.");
            return;
        }

        const roleIds = Array.isArray(guildData) ? guildData : guildData.roles;
        const isEnabled = Array.isArray(guildData) ? true : (guildData.enabled ?? true);

        if (!roleIds || roleIds.length === 0) {
            await interaction.followup.send("📋 | لا توجد رتب مسجلة في القائمة حالياً.");
            return;
        }

        const rolesMention = roleIds
            .map(rId => interaction.guild.roles.cache.get(rId))
            .filter(role => role !== undefined)
            .map(role => role.toString());

        const embed = new EmbedBuilder()
            .setTitle("🛡️ | قائمة الرتب التلقائية")
            .setDescription(`**حالة النظام:** \`${isEnabled ? 'مفعل ✅' : 'معطل ❌'}\`\n\n**الرتب الممنوحة عند الدخول:**\n` + rolesMention.map(rm => `• ${rm}`).join('\n'))
            .setColor(0x5865F2);

        await interaction.followup.send({ embeds: [embed] });
    },

    async handleMemberJoin(member) {
        const guildId = member.guild.id;
        const data = loadData();

        const guildData = data.autoroles?.[guildId];
        if (!guildData) return;

        const isEnabled = Array.isArray(guildData) ? true : (guildData.enabled ?? true);
        if (!isEnabled) return;

        const roleIds = Array.isArray(guildData) ? guildData : guildData.roles;
        if (!roleIds) return;

        for (const rId of roleIds) {
            const role = member.guild.roles.cache.get(rId);
            if (role) {
                try {
                    await member.roles.add(role, "توزيع الرتب التلقائية للأعضاء الجدد");
                } catch (e) {
                    console.error(`Failed to assign role ${rId}:`, e.message);
                }
            }
        }
    }
};
