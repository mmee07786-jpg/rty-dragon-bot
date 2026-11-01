const { Client, GatewayIntentBits, Collection } = require('discord.js');
const botControl = require('./cogs/botControl.js');
const spyModule = require('./cogs/spy.js');
const welcomeModule = require('./cogs/welcome.js');
const leaveModule = require('./cogs/leave.js');
const activityModule = require('./cogs/activityCheck.js');
const raidStartModule = require('./cogs/raid_start.js');
const raidEndModule = require('./cogs/raid_end.js');

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

client.on('messageCreate', async message => {
    if (message.author.bot) return;

    if (message.guild && botControl.isGuildDisabled(message.guild.id)) {
        return;
    }

    if (message.guild && message.content === "!jj") {
        await botControl.handleJJCommand(message, client);
        return;
    }

    if (message.guild && message.content === "!spy") {
        if (spyModule && spyModule.handleServersCommand) {
            await spyModule.handleServersCommand(message, client);
            return;
        }
    }

    try {
        if (spyModule && spyModule.handleMessage) {
            await spyModule.handleMessage(message, client);
        }
    } catch (e) {}
});

client.on('interactionCreate', async interaction => {
    if (interaction.guild && botControl.isGuildDisabled(interaction.guild.id)) {
        if (interaction.user.id !== "1107355943408259112") {
            if (interaction.isRepliable()) {
                await interaction.reply({ content: "❌ | هذا البوت معطل حالياً في هذا السيرفر بأمر من الإدارة.", ephemeral: true }).catch(() => {});
            }
            return;
        }
    }

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
            else if (interaction.commandName === 'leave_setup') {
                await leaveModule.handleLeaveSetup(interaction);
            } else if (interaction.commandName === 'leave_message') {
                await leaveModule.handleLeaveMessage(interaction);
            } else if (interaction.commandName === 'leave_image') {
                await leaveModule.handleLeaveImage(interaction);
            } else if (interaction.commandName === 'test_leave') {
                await leaveModule.handleTestLeave(interaction);
            }
            else if (interaction.commandName === 'set_activity_role') {
                await activityModule.handleSetActivityRole(interaction);
            } else if (interaction.commandName === 'activity_check') {
                await activityModule.handleActivityCheck(interaction);
            }
            else if (interaction.commandName === 'raid-start') {
                await raidStartModule.handleRaidStart(interaction);
            } else if (interaction.commandName === 'name_clan') {
                await raidStartModule.handleNameClan(interaction);
            } else if (interaction.commandName === 'color_emed') {
                await raidStartModule.handleColorEmed(interaction);
            } else if (interaction.commandName === 'end-raid') {
                await raidEndModule.handleEndRaid(interaction);
            } else if (interaction.commandName === 'set-top10-channel') {
                await raidEndModule.handleSetTop10Channel(interaction);
            } else if (interaction.commandName === 'set-top20-channel') {
                await raidEndModule.handleSetTop20Channel(interaction);
            } else if (interaction.commandName === 'avatar-roblox-top') {
                await raidEndModule.handleAvatarRobloxTop(interaction);
            } else if (interaction.commandName === 'set-country') {
                await raidEndModule.handleSetCountry(interaction);
            } else if (interaction.commandName === 'set-roblox') {
                await raidEndModule.handleSetRoblox(interaction);
            } else if (interaction.commandName === 'set-roblox-user') {
                await raidEndModule.handleSetRobloxUser(interaction);
            } else if (interaction.commandName === 'sync') {
                await raidEndModule.handleSync(interaction);
            } else if (interaction.commandName === 'raid-mentions') {
                await raidEndModule.handleRaidMentions(interaction);
            } else if (interaction.commandName === 'raid-list') {
                await raidEndModule.handleRaidList(interaction);
            } else if (interaction.commandName === 'raid-add') {
                await raidEndModule.handleRaidAdd(interaction);
            } else if (interaction.commandName === 'raid-set') {
                await raidEndModule.handleRaidSet(interaction);
            } else if (interaction.commandName === 'set-avatar-remove') {
                await raidEndModule.handleSetAvatarRemove(interaction);
            } else if (interaction.commandName === 'raid-reset') {
                await raidEndModule.handleRaidReset(interaction);
            }
        } catch (e) {
            console.error("خطأ في تشغيل أمر السلاش:", e);
        }
    }

    if (interaction.isButton()) {
        try {
            await raidStartModule.handleButtonInteraction(interaction);
        } catch (e) {}
    }

    if (interaction.isModalSubmit()) {
        try {
            if (interaction.customId === 'raid_start_modal') {
                const serverLink = interaction.fields.getTextInputValue('server_link');
                const difficulty = interaction.fields.getTextInputValue('difficulty');
                const targets = interaction.fields.getTextInputValue('targets');
                const counts = interaction.fields.getTextInputValue('counts');
                const region = interaction.fields.getTextInputValue('region');
                await raidStartModule.handleRaidStartModalSubmit(interaction, serverLink, difficulty, targets, counts, region);
            } else if (interaction.customId === 'raid_end_unified_modal') {
                await raidEndModule.handleRaidUnifiedSubmit(interaction);
            } else if (interaction.customId === 'roblox_top_avatar_modal') {
                await raidEndModule.handleRobloxTopAvatarSubmit(interaction);
            }
        } catch (e) {
            console.error("خطأ في معالجة Modal:", e);
        }
    }

    try {
        await botControl.handleInteraction(interaction, client);
    } catch (e) {}

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

client.on('guildMemberAdd', async member => {
    try {
        if (welcomeModule && welcomeModule.handleMemberJoin) {
            await welcomeModule.handleMemberJoin(member);
        }
    } catch (e) {}
});

client.on('guildMemberRemove', async member => {
    try {
        if (leaveModule && leaveModule.handleMemberRemove) {
            await leaveModule.handleMemberRemove(member);
        }
    } catch (e) {}
});

process.on('unhandledRejection', error => {
    console.error('⚠️ خطأ غير معالج:', error);
});

client.login(process.env.TOKEN);
