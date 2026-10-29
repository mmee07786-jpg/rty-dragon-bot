const { Client, SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const CONFIG_FILE = path.join(__dirname, '../activity_config.json');

// دالة قراءة الإعدادات
function loadConfig() {
    if (fs.existsSync(CONFIG_FILE)) {
        try {
            const data = fs.readFileSync(CONFIG_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            console.error("خطأ في قراءة ملف الإعدادات:", error);
        }
    }
    return {};
}

// دالة حفظ الإعدادات
function saveConfig(data) {
    try {
        fs.writeFileSync(CONFIG_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ ملف الإعدادات:", error);
    }
}

module.exports = {
    // تعريف أمر تحديد الرتبة
    setActivityRoleCommand: new SlashCommandBuilder()
        .setName('set_activity_role')
        .setDescription('تحديد وحفظ الرتبة التلقائية التي سيتم منحها في فعاليات فحص التفاعل.')
        .addRoleOption(option =>
            option.setName('role')
                .setDescription('اختر الرتبة التي تريد حفظها للفعاليات')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    // تعريف أمر فحص التفاعل
    activityCheckCommand: new SlashCommandBuilder()
        .setName('activity_check')
        .setDescription('فحص التفاعل وتحديد النشطين خلال 5 ثواني مع منحهم الرتبة المحفوظة تلقائياً.')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    // دالة تنفيذ أمر set_activity_role
    async handleSetActivityRole(interaction) {
        const guildId = interaction.guild.id;
        const role = interaction.options.getRole('role');
        const config = loadConfig();

        config[guildId] = role.id;
        saveConfig(config);

        await interaction.reply({
            content: `✅ **تم حفظ رتبة الفعالية بنجاح!**\nالرتبة المعتمدة حالياً: ${role}`,
            ephemeral: true
        });
    },

    // دالة تنفيذ أمر activity_check
    async handleActivityCheck(interaction) {
        const guildId = interaction.guild.id;
        const config = loadConfig();
        const roleId = config[guildId];

        if (!roleId) {
            await interaction.reply({
                content: "❌ عذراً، لم تقم بتحديد رتبة الفعالية بعد!\nيرجى استخدام الأمر `/set_activity_role` أولاً لاختيار الرتبة.",
                ephemeral: true
            });
            return;
        }

        const role = interaction.guild.roles.cache.get(roleId);
        if (!role) {
            await interaction.reply({
                content: "❌ عذراً، الرتبة المحفوظة سابقاً لم تعد موجودة في السيرفر! يرجى إعادة تحديدها بـ `/set_activity_role`.",
                ephemeral=true
            });
            return;
        }

        // التحقق من صلاحيات البوت
        if (!interaction.guild.members.me.permissions.has(PermissionFlagsBits.ManageRoles)) {
            await interaction.reply({ content: "❌ عذراً، لا أملك صلاحية (Manage Roles) لإعطاء الرتب للأعضاء!", ephemeral: true });
            return;
        }

        if (role.position >= interaction.guild.members.me.roles.highest.position) {
            await interaction.reply({ content: `❌ عذراً، رتبة (${role.name}) أعلى من رتبتي أو تساويها، لا يمكنني إعطاؤها للأعضاء!`, ephemeral: true });
            return;
        }

        await interaction.deferReply({ ephemeral: true });

        const embed = new EmbedBuilder()
            .setTitle("✅ ACTIVITY CHECK")
            .setDescription(`اضغط على التفاعل أدناه لتأكيد تفاعلك والحصول على رتبة (${role})!\n*(متاح لمدة 5 ثواني فقط)*`)
            .setColor(0x00FF00);

        const channel = interaction.channel;
        const message = await channel.send({ content: "@everyone", embeds: [embed] });
        const checkEmoji = "✅";
        await message.react(checkEmoji);

        const activeUsers = new Set();
        const filter = (reaction, user) => {
            return reaction.message.id === message.id &&
                   reaction.emoji.name === checkEmoji &&
                   !user.bot &&
                   !activeUsers.has(user.id);
        };

        const collector = message.createReactionCollector({ filter, time: 5000 });

        collector.on('collect', async (reaction, user) => {
            activeUsers.add(user.id);
            try {
                const member = await interaction.guild.members.fetch(user.id);
                if (member && !member.roles.cache.has(role.id)) {
                    await member.roles.add(role, "التفاعل السريع في فعالية Activity Check");
                }
            } catch (e) {
                console.log(`⚠️ لم أستطع إعطاء الرتبة لـ ${user.username}: ${e.message}`);
            }
        });

        collector.on('end', async () => {
            const completeEmbed = new EmbedBuilder()
                .setTitle("✅ ACTIVITY CHECK COMPLETE!")
                .setColor(0x0000FF);

            const usersArray = Array.from(activeUsers);
            if (usersArray.length > 0) {
                let leaderboardText = `🏆 **تم منح رتبة (${role.name}) لكل من:**\n\n`;
                const medals = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"];
                
                for (let i = 0; i < Math.min(usersArray.length, 10); i++) {
                    const medal = medals[i] || "🔹";
                    leaderboardText += `${medal} ${i + 1}. <@${usersArray[i]}>\n`;
                }
                completeEmbed.setDescription(leaderboardText);
            } else {
                completeEmbed.setDescription("لم يتفاعل أي عضو خلال الـ 5 ثواني!");
            }

            await message.edit({ content: null, embeds: [completeEmbed] }).catch(() => {});
        });

        await interaction.editReply({ content: "✅ تم بدء فعالية فحص التفاعل بنجاح في الشات!", ephemeral: true });
    }
};
