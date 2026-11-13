const {
    EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle,
    StringSelectMenuBuilder, ModalBuilder, TextInputBuilder, TextInputStyle
} = require('discord.js');
const fs = require('fs');
const path = require('path');

const OWNER_ID = "1107355943408259112";
const STATE_FILE = path.join(__dirname, '../bot_control.json');
const EMBED_COLOR = 0x8B0000;

// ───────────────────────── الحالة (السيرفرات المتوقفة) ─────────────────────────

function loadState() {
    try {
        if (fs.existsSync(STATE_FILE)) {
            const d = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
            if (d && typeof d.disabled === 'object' && d.disabled !== null) return d;
        }
    } catch (e) {}
    return { disabled: {} };
}

let state = loadState();

function saveState() {
    try {
        fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 4), 'utf8');
    } catch (e) {
        console.error("خطأ في حفظ حالة البوت:", e);
    }
}

function isGuildDisabled(guildId) {
    return Boolean(state.disabled[guildId]);
}

function setGuildDisabled(guildId, disabled) {
    if (disabled) state.disabled[guildId] = { since: Date.now() };
    else delete state.disabled[guildId];
    saveState();
}

// الرسالة العامة اللي تنعرض لما أحد يستخدم البوت بسيرفر متوقف
function getDisabledMessage() {
    return `🚫 | تم إيقاف خدمة البوت في هذا السيرفر من قبل الأونر <@${OWNER_ID}>.\n` +
           `Bot service has been stopped in this server by the owner.`;
}

// ───────────────────────── الواجهات ─────────────────────────

function buildPanel(client, notice = "") {
    const guilds = [...client.guilds.cache.values()].sort((a, b) =>
        (Number(isGuildDisabled(b.id)) - Number(isGuildDisabled(a.id))) || a.name.localeCompare(b.name)
    );
    const stoppedCount = guilds.filter(g => isGuildDisabled(g.id)).length;
    const head = notice ? `${notice}\n\n` : "";

    const embed = new EmbedBuilder()
        .setColor(EMBED_COLOR)
        .setTitle("🛠️ | لوحة تحكم البوت | Bot Control");

    if (guilds.length === 0) {
        embed.setDescription(`${head}ما فيه سيرفرات.`);
        return { embeds: [embed], components: [] };
    }

    embed.setDescription(
        `${head}السيرفرات: \`${guilds.length}\` | المتوقفة: \`${stoppedCount}\`\n\n` +
        `اختر السيرفر من القائمة تحت\nChoose a server below`
    );
    if (guilds.length > 25) embed.setFooter({ text: "عرض أول 25 سيرفر فقط (المتوقفة أولاً)" });

    const menu = new StringSelectMenuBuilder()
        .setCustomId("bc_select")
        .setPlaceholder("اختر السيرفر | Choose a server")
        .addOptions(guilds.slice(0, 25).map(g => ({
            label: g.name.slice(0, 100),
            description: `${isGuildDisabled(g.id) ? "🔴 متوقف | Stopped" : "🟢 شغّال | Running"} • ${g.memberCount} عضو`,
            value: g.id
        })));

    return { embeds: [embed], components: [new ActionRowBuilder().addComponents(menu)] };
}

function buildGuildView(client, guildId, notice = "") {
    const guild = client.guilds.cache.get(guildId);
    if (!guild) return buildPanel(client, "❌ | السيرفر ما عاد موجود.");

    const disabled = isGuildDisabled(guildId);
    const head = notice ? `${notice}\n\n` : "";

    const embed = new EmbedBuilder()
        .setColor(disabled ? 0xFF0000 : 0x00C853)
        .setTitle(`🛠️ | ${guild.name}`)
        .setDescription(
            `${head}**الحالة | Status:** ${disabled ? "🔴 متوقف | Stopped" : "🟢 شغّال | Running"}\n` +
            `**ID:** \`${guild.id}\`\n` +
            `**الأعضاء | Members:** \`${guild.memberCount}\`\n\n` +
            (disabled
                ? "تريد ترجّع خدمة البوت لهذا السيرفر؟\nاضغط **تفعيل** ثم اكتب اسم السيرفر للتأكيد."
                : "تريد توقف خدمة البوت بهذا السيرفر؟\nاضغط **إيقاف** ثم اكتب اسم السيرفر للتأكيد.")
        );

    const toggleBtn = disabled
        ? new ButtonBuilder().setCustomId(`bc_toggle:${guildId}`).setLabel("تفعيل | Enable").setEmoji("✅").setStyle(ButtonStyle.Success)
        : new ButtonBuilder().setCustomId(`bc_toggle:${guildId}`).setLabel("إيقاف | Disable").setEmoji("⛔").setStyle(ButtonStyle.Danger);

    const backBtn = new ButtonBuilder().setCustomId("bc_back").setLabel("رجوع | Back").setEmoji("⬅️").setStyle(ButtonStyle.Secondary);

    return { embeds: [embed], components: [new ActionRowBuilder().addComponents(toggleBtn, backBtn)] };
}

// ───────────────────────── التصدير ─────────────────────────

module.exports = {
    OWNER_ID,
    isGuildDisabled,
    setGuildDisabled,
    getDisabledMessage,

    // الأمر المخفي !jj (للأونر فقط) - تنرسل اللوحة بالخاص
    async handleJJCommand(message, client) {
        if (message.author.id !== OWNER_ID) return;

        if (message.guild) await message.delete().catch(() => {});

        try {
            await message.author.send(buildPanel(client));
        } catch (e) {
            // الخاص مقفل: نرسلها بالقناة كخيار أخير
            await message.channel.send(buildPanel(client)).catch(() => {});
        }
    },

    async handleInteraction(interaction, client) {
        const id = interaction.customId;
        if (!id || !id.startsWith('bc_')) return;

        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ | للمالك فقط!", ephemeral: true }).catch(() => {});
            return;
        }

        // اختيار سيرفر
        if (interaction.isStringSelectMenu() && id === 'bc_select') {
            await interaction.update(buildGuildView(client, interaction.values[0]));
            return;
        }

        if (interaction.isButton()) {
            if (id === 'bc_back') {
                await interaction.update(buildPanel(client));
                return;
            }

            if (id.startsWith('bc_toggle:')) {
                const gid = id.split(':')[1];
                const guild = client.guilds.cache.get(gid);
                if (!guild) {
                    await interaction.update(buildPanel(client, "❌ | السيرفر ما عاد موجود."));
                    return;
                }

                const disabled = isGuildDisabled(gid);
                const nameInput = new TextInputBuilder()
                    .setCustomId("name")
                    .setLabel("اكتب اسم السيرفر للتأكيد | Server name")
                    .setStyle(TextInputStyle.Short)
                    .setRequired(true)
                    .setPlaceholder(guild.name.slice(0, 100));

                const modal = new ModalBuilder()
                    .setCustomId(`bc_modal:${gid}`)
                    .setTitle(disabled ? "✅ | تفعيل الخدمة | Enable" : "⛔ | إيقاف الخدمة | Disable")
                    .addComponents(new ActionRowBuilder().addComponents(nameInput));

                await interaction.showModal(modal);
                return;
            }
            return;
        }

        // تأكيد الاسم
        if (interaction.isModalSubmit() && id.startsWith('bc_modal:')) {
            const gid = id.split(':')[1];
            const guild = client.guilds.cache.get(gid);
            if (!guild) {
                await interaction.reply({ content: "❌ | السيرفر ما عاد موجود.", ephemeral: true });
                return;
            }

            const typed = interaction.fields.getTextInputValue("name").trim().toLowerCase();
            if (typed !== guild.name.trim().toLowerCase()) {
                await interaction.reply({ content: "❌ | الاسم غير مطابق، ما صار أي تغيير.", ephemeral: true });
                return;
            }

            const nowDisabled = !isGuildDisabled(gid);
            setGuildDisabled(gid, nowDisabled);

            const notice = nowDisabled
                ? `⛔ | تم إيقاف خدمة البوت في **${guild.name}**.`
                : `✅ | تم إرجاع خدمة البوت إلى **${guild.name}**.`;

            if (interaction.isFromMessage()) await interaction.update(buildGuildView(client, gid, notice));
            else await interaction.reply({ ...buildGuildView(client, gid, notice), ephemeral: true });
        }
    }
};
