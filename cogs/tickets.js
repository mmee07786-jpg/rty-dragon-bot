const { 
    SlashCommandBuilder, 
    PermissionFlagsBits, 
    EmbedBuilder, 
    ActionRowBuilder, 
    ButtonBuilder, 
    ButtonStyle, 
    ChannelType 
} = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../ticket_config.json');

function loadTicketData() {
    if (fs.existsSync(DATA_FILE)) {
        try {
            return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
        } catch (e) {
            return { guilds: {} };
        }
    }
    return { guilds: {} };
}

function saveTicketData(data) {
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
}

function getGuildTicketConfig(guildId) {
    const data = loadTicketData();
    if (!data.guilds) data.guilds = {};
    if (!data.guilds[guildId]) {
        data.guilds[guildId] = {
            counter: 0,
            buttons: {} // key: custom_id, value: { label, description, emoji }
        };
        saveTicketData(data);
    }
    return data.guilds[guildId];
}

function updateGuildTicketConfig(guildId, guildConfig) {
    const data = loadTicketData();
    if (!data.guilds) data.guilds = {};
    data.guilds[guildId] = guildConfig;
    saveTicketData(data);
}

// زر إغلاق التكت (ثابت)
class CloseTicketButtonView extends ActionRowBuilder {
    constructor() {
        super();
        this.addComponents(
            new ButtonBuilder()
                .setCustomId("close_ticket_btn")
                .setLabel("إغلاق التكت 🔒")
                .setStyle(ButtonStyle.Danger)
        );
    }
}

module.exports = {
    // 1. أمر إرسال لوحة التكتات الرئيسية
    ticketPanelCommand: new SlashCommandBuilder()
        .setName('ticket-panel')
        .setDescription('[ خاص بالإدارة ] إرسال لوحة التذاكر المتقدمة بالأزرار المخصصة')
        .addStringOption(o => o.setName('message').setDescription('رسالة اللوحة التي ستظهر للأعضاء').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    // 2. إدارة الأزرار (إضافة)
    ticketAddBtnCommand: new SlashCommandBuilder()
        .setName('ticket-add-btn')
        .setDescription('[ خاص بالإدارة ] إضافة زر جديد لقائمة التذاكر مع وصف مخصص')
        .addStringOption(o => o.setName('id').setDescription('معرف فريد للزر بالإنجليزية (مثل: support, complaint)').setRequired(true))
        .addStringOption(o => o.setName('label').setDescription('اسم الزر الظاهري (مثل: تقديم, شكوى)').setRequired(true))
        .addStringOption(o => o.setName('description').setDescription('الرسالة أو الوصف الذي يظهر داخل التكت عند فتحها بهذا الزر').setRequired(true))
        .addStringOption(o => o.setName('emoji').setDescription('إيموجي الزر (اختياري، مثل 🎫)').setRequired(false))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    // 3. إدارة الأزرار (حذف)
    ticketRemoveBtnCommand: new SlashCommandBuilder()
        .setName('ticket-remove-btn')
        .setDescription('[ خاص بالإدارة ] حذف زر تذاكر موجود سابقاً')
        .addStringOption(o => o.setName('id').setDescription('معرف الزر (ID) المراد حذفه').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    // معالجة إرسال اللوحة
    async handleTicketPanel(interaction) {
        const guildId = interaction.guildId;
        const messageText = interaction.options.getString('message');
        const config = getGuildTicketConfig(guildId);

        if (Object.keys(config.buttons).length === 0) {
            await interaction.reply({ content: "❌ | لم تقم بإضافة أي أزرار للتكتات حتى الآن! استخدم `/ticket-add-btn` أولاً.", ephemeral: true });
            return;
        }

        const buttons = Object.entries(config.buttons).map(([btnId, btnData]) => {
            const builder = new ButtonBuilder()
                .setCustomId(`ticket_create_${btnId}`)
                .setLabel(btnData.label)
                .setStyle(ButtonStyle.Secondary);
            if (btnData.emoji) builder.setEmoji(btnData.emoji);
            return builder;
        });

        const rows = [];
        for (let i = 0; i < buttons.length; i += 5) {
            rows.push(new ActionRowBuilder().addComponents(buttons.slice(i, i + 5)));
        }

        const embed = new EmbedBuilder()
            .setTitle("🎫 | قسم تذاكر الدعم الفني المتقدمة")
            .setDescription(messageText)
            .setColor(0x000000)
            .setFooter({ text: `Server Support • ${interaction.guild.name}` });

        await interaction.channel.send({ embeds: [embed], components: rows });
        await interaction.reply({ content: "✅ | تم إرسال لوحة التكتات المتقدمة بنجاح!", ephemeral: true });
    },

    // معالجة إضافة زر
    async handleTicketAddBtn(interaction) {
        const guildId = interaction.guildId;
        const btnId = interaction.options.getString('id').trim().toLowerCase();
        const label = interaction.options.getString('label');
        const description = interaction.options.getString('description');
        const emoji = interaction.options.getString('emoji');

        const config = getGuildTicketConfig(guildId);
        config.buttons[btnId] = { label, description, emoji };
        updateGuildTicketConfig(guildId, config);

        await interaction.reply({ content: `✅ | تم إضافة زر التكت **(${label})** بالمعرف \`${btnId}\` بنجاح!`, ephemeral: true });
    },

    // معالجة حذف زر
    async handleTicketRemoveBtn(interaction) {
        const guildId = interaction.guildId;
        const btnId = interaction.options.getString('id').trim().toLowerCase();

        const config = getGuildTicketConfig(guildId);
        if (config.buttons[btnId]) {
            delete config.buttons[btnId];
            updateGuildTicketConfig(guildId, config);
            await interaction.reply({ content: `✅ | تم حذف الزر ذو المعرف \`${btnId}\` بنجاح.`, ephemeral: true });
        } else {
            await interaction.reply({ content: `❌ | لم يتم العثور على زر بهذا المعرف \`${btnId}\`.`, ephemeral: true });
        }
    },

    // معالجة التفاعلات (فتح التكت، إغلاقها، والأزرار المخصصة)
    async handleInteraction(interaction, client) {
        if (!interaction.isButton()) return;

        const customId = interaction.customId;

        // 1. زر إغلاق التكت
        if (customId === "close_ticket_btn") {
            if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
                await interaction.reply({ content: "عذراً، زر إغلاق التكت مخصص للإداريين فقط! ❌", ephemeral: true });
                return;
            }

            await interaction.reply({ content: "جاري إغلاق وحذف التذكرة خلال 3 ثوانٍ... ⏱️" });
            setTimeout(async () => {
                try {
                    await interaction.channel.delete();
                } catch (e) {}
            }, 3000);
            return;
        }

        // 2. أزرار إنشاء التذاكر المخصصة
        if (customId.startsWith("ticket_create_")) {
            const btnId = customId.replace("ticket_create_", "");
            const guildId = interaction.guildId;
            const config = getGuildTicketConfig(guildId);
            const btnData = config.buttons[btnId];

            if (!btnData) {
                await interaction.reply({ content: "❌ | هذا الزر لم يعد متوفراً أو تم حذفه من النظام.", ephemeral: true });
                return;
            }

            const guild = interaction.guild;
            const member = interaction.user;

            // زيادة العداد وترقيمه من 001 إلى ما لانهاية
            config.counter = (config.counter || 0) + 1;
            const ticketNumber = String(config.counter).padStart(3, '0');
            updateGuildTicketConfig(guildId, config);

            const channelName = `ticket-${ticketNumber}`;
            const existingChannel = guild.channels.cache.find(c => c.name === channelName);
            if (existingChannel) {
                await interaction.reply({ content: `لديك تذكرة مفتوحة بالفعل هنا: ${existingChannel} ❌`, ephemeral: true });
                return;
            }

            const overwrites = [
                { id: guild.id, deny: [PermissionFlagsBits.ViewChannel] },
                { id: member.id, allow: [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.SendMessages, PermissionFlagsBits.ReadMessageHistory] },
                { id: client.user.id, allow: [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.SendMessages, PermissionFlagsBits.ManageChannels] }
            ];

            const ticketChannel = await guild.channels.create({
                name: channelName,
                type: ChannelType.GuildText,
                permissionOverwrites: overwrites,
                topic: `تذكرة نوع (${btnData.label}) خاصة بالعضو: ${member.tag}`
            });

            const embed = new EmbedBuilder()
                .setTitle(`🎫 | تذكرة جديدة - ${btnData.label}`)
                .setDescription(
                    `مرحباً بك ${member}!\n` +
                    `نوع التذكرة: **${btnData.label}**\n\n` +
                    `📝 **الوصف / التعليمات:**\n${btnData.description}\n\n` +
                    `⚠️ **ملاحظة:** إذا لم يتم إرسال أي رسالة خلال **ساعة كاملة**، سيتم إغلاق التذكرة تلقائياً.`
                )
                .setColor(0x000000)
                .setFooter({ text: `Ticket #${ticketNumber} | Requested by ${member.username}`, iconURL: member.displayAvatarURL() });

            const row = new CloseTicketButtonView();
            await ticketChannel.send({ content: `${member}`, embeds: [embed], components: [row] });
            await interaction.reply({ content: `تم فتح تذكرتك بنجاح: ${ticketChannel} ✅`, ephemeral: true });

            // نظام إغلاق التكت تلقائياً بعد ساعة من عدم النشاط
            const checkInactivity = async () => {
                try {
                    const filter = m => m.channelId === ticketChannel.id && !m.author.bot;
                    await ticketChannel.awaitMessages({ filter, max: 1, time: 3600 * 1000, errors: ['time'] });
                } catch (e) {
                    try {
                        await ticketChannel.delete("إغلاق تلقائي بسبب عدم النشاط لمدة ساعة");
                    } catch (err) {}
                }
            };
            checkInactivity();
        }
    }
};
