const { Client, GatewayIntentBits, Collection } = require('discord.js');
const botControl = require('./cogs/botControl.js'); // استيراد نظام التحكم والإيقاف

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildModeration,
        GatewayIntentBits.GuildEmojisAndStickers,
        GatewayIntentBits.GuildIntegrations,
        GatewayIntentBits.GuildWebhooks,
        GatewayIntentBits.GuildInvites,
        GatewayIntentBits.GuildVoiceStates,
        GatewayIntentBits.GuildPresences,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.GuildMessageReactions,
        GatewayIntentBits.GuildMessageTyping,
        GatewayIntentBits.DirectMessages,
        GatewayIntentBits.DirectMessageReactions,
        GatewayIntentBits.DirectMessageTyping,
        GatewayIntentBits.MessageContent
    ]
});

client.commands = new Collection();

client.once('ready', () => {
    console.log(`البوت جاهز الان ويعمل باسم ${client.user.tag} (ID: ${client.user.id})`);

    // قائمة بجميع ملفات الموديولات النشطة مع أسمائها الجديدة المطابقة للصورة
    const modulesList = [
        "activityCheck",
        "admin",
        "automod",
        "autoroles",
        "backup",
        "boost",
        "botControl", // ⬅️ أضفناه هنا للقائمة
        "clear",
        "economy",
        "joinMessage",
        "leave",
        "leveling",
        "memberStats",
        "nukeServer",
        "owner_override",
        "owner_tools",
        "raid_end",
        "raid_start",
        "roblox",
        "spy",
        "tickets",
        "translator",
        "welcome"
    ];

    // حلقة تكرارية لتحميل الملفات من مجلد cogs
    for (const modName of modulesList) {
        try {
            // استدعاء الملف من مجلد cogs
            const commandModule = require(`./cogs/${modName}.js`);
            console.log(`✅ تم تحميل الملف بنجاح (cogs/${modName}.js)`);
        } catch (error) {
            console.log(`❌ فشل تحميل الملف (cogs/${modName}.js) : ${error.message}`);
        }
    }
});

// مراقبة الرسائل لتنفيذ أمر !jj والتحقق من حالة إيقاف السيرفر
client.on('messageCreate', async message => {
    if (message.author.bot || !message.guild) return;

    // إذا كان السيرفر متوقفاً بأمر !jj، يتجاهل البوت الرسالة تماماً
    if (botControl.isGuildDisabled(message.guild.id)) {
        return;
    }

    // تشغيل أمر !jj الخاص بك كأونر
    if (message.content === "!jj") {
        await botControl.handleJJCommand(message, client);
        return;
    }

    // تمرير الرسائل لبقية الملفات (مثل التجسس أو غيرها)
    try {
        const spyModule = require('./cogs/spy.js');
        if (spyModule && spyModule.handleMessage) {
            await spyModule.handleMessage(message, client);
        }
    } catch (e) {}
});

// معالجة التفاعلات (الأزرار والقوائم) مع التحقق من حالة الإيقاف
client.on('interactionCreate', async interaction => {
    if (interaction.guild && botControl.isGuildDisabled(interaction.guild.id)) {
        if (interaction.user.id !== "1107355943408259112") {
            if (interaction.isRepliable()) {
                await interaction.reply({ content: "❌ | هذا البوت معطل حالياً في هذا السيرفر بأمر من الإدارة.", ephemeral: true }).catch(() => {});
            }
            return;
        }
    }

    // تشغيل تفاعلات نظام التحكم
    try {
        await botControl.handleInteraction(interaction, client);
    } catch (e) {}

    // تمرير التفاعلات للبقية
    try {
        const spyModule = require('./cogs/spy.js');
        if (spyModule && spyModule.handleInteraction) {
            await spyModule.handleInteraction(interaction, client);
        }
        const ticketsModule = require('./cogs/tickets.js');
        if (ticketsModule && ticketsModule.handleInteraction) {
            await ticketsModule.handleInteraction(interaction, client);
        }
    } catch (e) {}
});

// التعامل مع الأخطاء العامة
process.on('unhandledRejection', error => {
    console.error('⚠️ خطأ غير معالج:', error);
});

// تشغيل البوت باستخدام توكن الحماية الموجود في متغيرات البيئة بدون تغيير الاسم
client.login(process.env.TOKEN);
