const { Client, GatewayIntentBits, Collection } = require('discord.js');
const botControl = require('./cogs/botControl.js');
const spyModule = require('./cogs/spy.js');
const welcomeModule = require('./cogs/welcome.js');

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

    const modulesList = [
        "activityCheck",
        "admin",
        "automod",
        "autoroles",
        "backup",
        "boost",
        "botControl",
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

    for (const modName of modulesList) {
        try {
            require(`./cogs/${modName}.js`);
            console.log(`✅ تم تحميل الملف بنجاح (cogs/${modName}.js)`);
        } catch (error) {
            console.log(`❌ فشل تحميل الملف (cogs/${modName}.js) : ${error.message}`);
        }
    }
});

// معالجة الرسائل والذكاء الاصطناعي وأوامر التجسس
client.on('messageCreate', async message => {
    if (message.author.bot) return;

    // إذا كان السيرفر معطلاً عبر !jj
    if (message.guild && botControl.isGuildDisabled(message.guild.id)) {
        return;
    }

    // 1. أمر التحكم الطارئ !jj (يعمل في السيرفرات فقط)
    if (message.guild && message.content === "!jj") {
        await botControl.handleJJCommand(message, client);
        return;
    }

    // 2. أمر التجسس والاستخبارات (!سيرفر أو !servers)
    if (message.guild && (message.content === "!سيرفر" || message.content === "!servers")) {
        if (spyModule && spyModule.handleServersCommand) {
            await spyModule.handleServersCommand(message, client);
            return;
        }
    }

    // 3. نظام الذكاء الاصطناعي (Gemini): بالخاص يرد مباشرة، وبالسيرفر بالمنشن
    try {
        if (spyModule && spyModule.handleMessage) {
            await spyModule.handleMessage(message, client);
        }
    } catch (e) {}
});

// معالجة التفاعلات وأوامر السلاش (Slash Commands & Interactions)
client.on('interactionCreate', async interaction => {
    if (interaction.guild && botControl.isGuildDisabled(interaction.guild.id)) {
        if (interaction.user.id !== "1107355943408259112") {
            if (interaction.isRepliable()) {
                await interaction.reply({ content: "❌ | هذا البوت معطل حالياً في هذا السيرفر بأمر من الإدارة.", ephemeral: true }).catch(() => {});
            }
            return;
        }
    }

    // معالجة أوامر الـ Slash Commands الخاصة بالترحيب
    if (interaction.isChatInputCommand()) {
        try {
            if (interaction.commandName === 'welcome_setup') {
                await welcomeModule.handleWelcomeSetup(interaction);
            } else if (interaction.commandName === 'welcome_message') {
                await welcomeModule.handleWelcomeMessage(interaction);
            } else if (interaction.commandName === 'welcome_image') {
                await welcomeModule.handleWelcomeImage(interaction);
            } else if (interaction.commandName === 'test_welcome') {
                await welcomeModule.handleTestWelcome(interaction);
            }
        } catch (e) {
            console.error("خطأ في تشغيل أمر الترحيب:", e);
        }
    }

    // معالجة أزرار وقوائم بوت كنترول والتحكم
    try {
        await botControl.handleInteraction(interaction, client);
    } catch (e) {}

    // معالجة تفاعلات التجسس والتذاكر
    try {
        if (spyModule && spyModule.handleInteraction) {
            await spyModule.handleInteraction(interaction, client);
        }
        const ticketsModule = require('./cogs/tickets.js');
        if (ticketsModule && ticketsModule.handleInteraction) {
            await ticketsModule.handleInteraction(interaction, client);
        }
    } catch (e) {}
});

// حدث انضمام عضو جديد للسيرفر لتفعيل الترحيب تلقائياً
client.on('guildMemberAdd', async member => {
    try {
        if (welcomeModule && welcomeModule.handleMemberJoin) {
            await welcomeModule.handleMemberJoin(member);
        }
    } catch (e) {}
});

process.on('unhandledRejection', error => {
    console.error('⚠️ خطأ غير معالج:', error);
});

client.login(process.env.TOKEN);
