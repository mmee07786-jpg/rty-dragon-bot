const { SlashCommandBuilder, ChannelType, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const {
    joinVoiceChannel, createAudioPlayer, createAudioResource, entersState, getVoiceConnection,
    AudioPlayerStatus, VoiceConnectionStatus, NoSubscriberBehavior, StreamType
} = require('@discordjs/voice');
const { Readable } = require('stream');
const vm = require('vm');

/*
 * هذا الإصدار ما يحتاج ffmpeg ولا yt-dlp ولا أي ملف تنفيذي.
 * يجيب صوت يوتيوب بصيغة WebM/Opus ويرسله لديسكورد مباشرة.
 * يدعم روابط يوتيوب فقط.
 */

// حالة التشغيل لكل سيرفر
const states = new Map();
// السيرفرات اللي فيها أمر /play_music شغال حالياً (للقفل)
const busyGuilds = new Set();

/* ---------------- يوتيوب (youtubei.js) ---------------- */

const YT_ID = /(?:youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/|live\/)|music\.youtube\.com\/watch\?(?:.*&)?v=)([\w-]{11})/i;
const CLIENTS = ['IOS', 'ANDROID', 'TV', 'WEB'];

let ytClientPromise = null;
function getInnertube() {
    if (!ytClientPromise) {
        ytClientPromise = (async () => {
            const { Innertube, Platform } = await import('youtubei.js');
            // المكتبة تحتاج تشغّل سكربت فك التشفير من يوتيوب، نشغّله داخل vm معزول
            try {
                if (Platform && Platform.shim) {
                    Platform.shim.eval = async (data, env) => {
                        const props = [];
                        if (env.n) props.push(`n: exportedVars.nFunction("${env.n}")`);
                        if (env.sig) props.push(`sig: exportedVars.sigFunction("${env.sig}")`);
                        const code = `${data.output}\nreturn { ${props.join(', ')} }`;
                        return vm.runInNewContext(`(function(){${code}})()`, Object.create(null), { timeout: 8000 });
                    };
                }
            } catch (e) {}
            return Innertube.create({ retrieve_player: true });
        })().catch(e => { ytClientPromise = null; throw e; });
    }
    return ytClientPromise;
}

// يجيب معلومات الفيديو ويتأكد أن فيه صوت WebM/Opus
async function resolveTrack(link) {
    const m = link.match(YT_ID);
    if (!m) throw new Error('UNSUPPORTED');

    const yt = await getInnertube();
    let lastErr = null;
    for (const client of CLIENTS) {
        try {
            const info = await yt.getBasicInfo(m[1], { client });
            info.chooseFormat({ type: 'audio', quality: 'best', format: 'webm' }); // يرمي خطأ إذا ما في
            return { title: (info.basic_info && info.basic_info.title) || 'YouTube', info, client };
        } catch (e) {
            lastErr = e;
            console.error(`youtubei (${client}):`, e.message);
        }
    }
    throw lastErr || new Error('YT_FAILED');
}

// يفتح ستريم الصوت ويحوله لمورد للمشغّل
async function openStream(track) {
    const web = await track.info.download({ type: 'audio', quality: 'best', format: 'webm', client: track.client });
    const stream = Readable.fromWeb(web);
    stream.on('error', err => console.error('خطأ بستريم الصوت:', err.message));
    return { stream, resource: createAudioResource(stream, { inputType: StreamType.WebmOpus }) };
}

/* ---------------- التشغيل ---------------- */

async function startPlayback(state, preTrack) {
    const track = preTrack || await resolveTrack(state.url);
    state.title = track.title;

    const { stream, resource } = await openStream(track);
    const oldStream = state.stream;
    state.stream = stream;
    state.player.play(resource);
    // نسكّر الستريم القديم بعد ما نبدّل المورد
    if (oldStream) { try { oldStream.destroy(); } catch (e) {} }
}

function cleanup(guildId, connection) {
    const st = states.get(guildId);
    if (!st || st.connection !== connection) return;
    states.delete(guildId);
    try { st.player.stop(true); } catch (e) {}
    try { if (st.stream) st.stream.destroy(); } catch (e) {}
    if (st.kicked && st.interaction) {
        st.interaction.editReply({
            content: "⚠️ انطردت من الروم الصوتي، وتوقف التشغيل. إذا تريدني ارجع شغّلني من جديد بـ `/play_music`.",
            components: []
        }).catch(() => {});
    }
}

function createState(guild, channel, connection, interaction) {
    const player = createAudioPlayer({ behaviors: { noSubscriber: NoSubscriberBehavior.Play } });
    connection.subscribe(player);

    const state = {
        guildId: guild.id, channelId: channel.id, connection, player, interaction,
        url: null, title: '', stream: null,
        loop: false, retries: 0, errored: false, kicked: false
    };
    states.set(guild.id, state);

    // إذا انطرد من الروم: ما نرجع ندخل، نسوي تنظيف وبس
    // (إذا انسحب لروم ثاني يرجع يتصل لحاله خلال ثواني)
    connection.on(VoiceConnectionStatus.Disconnected, async () => {
        try {
            await Promise.race([
                entersState(connection, VoiceConnectionStatus.Signalling, 5000),
                entersState(connection, VoiceConnectionStatus.Connecting, 5000)
            ]);
        } catch (e) {
            state.kicked = true;
            if (connection.state.status !== VoiceConnectionStatus.Destroyed) connection.destroy();
        }
    });
    connection.on(VoiceConnectionStatus.Destroyed, () => cleanup(guild.id, connection));

    player.on('error', err => {
        console.error('خطأ في المشغل:', err.message);
        state.errored = true;
    });

    player.on('stateChange', (oldS, newS) => {
        if (newS.status === AudioPlayerStatus.Playing) state.retries = 0;

        if (newS.status === AudioPlayerStatus.Idle && oldS.status !== AudioPlayerStatus.Idle) {
            if (state.errored) {
                // خطأ بالستريم (غالباً الرابط انتهى): نحاول مرة وحدة من جديد
                state.errored = false;
                if (state.retries < 1) {
                    state.retries++;
                    startPlayback(state).catch(e => console.error('فشل إعادة المحاولة:', e.message));
                }
                return;
            }
            // انتهت النغمة طبيعياً: إذا التكرار شغال نعيدها
            if (state.loop) {
                startPlayback(state).catch(e => console.error('فشل التكرار:', e.message));
            }
        }
    });

    return state;
}

/* ---------------- الرسالة المخفية (لوحة التحكم) ---------------- */

function buildPanel(state) {
    const status = state.player.state.status;
    const playing = status === AudioPlayerStatus.Playing || status === AudioPlayerStatus.Buffering;
    const paused = status === AudioPlayerStatus.Paused || status === AudioPlayerStatus.AutoPaused;

    const title = state.title.length > 100 ? state.title.slice(0, 100) + '...' : state.title;
    const content =
        `🎵 **${title}**\n` +
        `🔊 الروم: <#${state.channelId}>\n` +
        `📻 الحالة: ${playing ? 'يشغّل الآن' : paused ? 'متوقف مؤقتاً' : 'انتهت'}\n` +
        `🔁 التكرار: ${state.loop ? 'مفعّل' : 'معطّل'}`;

    const row = new ActionRowBuilder().addComponents(
        new ButtonBuilder()
            .setCustomId('music_toggle')
            .setLabel(playing ? 'إيقاف مؤقت' : paused ? 'متابعة' : 'تشغيل من جديد')
            .setEmoji(playing ? '⏸️' : '▶️')
            .setStyle(ButtonStyle.Primary),
        new ButtonBuilder()
            .setCustomId('music_loop')
            .setLabel(state.loop ? 'التكرار: شغال' : 'التكرار: مطفي')
            .setEmoji('🔁')
            .setStyle(state.loop ? ButtonStyle.Success : ButtonStyle.Secondary),
        new ButtonBuilder()
            .setCustomId('music_stop')
            .setLabel('إيقاف وخروج')
            .setEmoji('⏹️')
            .setStyle(ButtonStyle.Danger)
    );
    return { content, components: [row] };
}

/* ---------------- الأوامر ---------------- */

module.exports = {
    // يجهّز مكتبة يوتيوب وقت تشغيل البوت حتى أول تشغيل يكون أسرع
    async prepare() {
        try { await getInnertube(); console.log('✅ تم تجهيز مكتبة يوتيوب'); }
        catch (e) { console.error('⚠️ تعذر تجهيز مكتبة يوتيوب:', e.message); }
    },

    playCommand: new SlashCommandBuilder()
        .setName('play_music')
        .setDescription('تشغيل رابط يوتيوب داخل روم صوتي')
        .addStringOption(o => o.setName('link').setDescription('رابط فيديو يوتيوب').setRequired(true))
        .addChannelOption(o => o
            .setName('channel')
            .setDescription('الروم الصوتي (إذا تركته فاضي يدخل رومك الحالي)')
            .addChannelTypes(ChannelType.GuildVoice)),

    // قفل لكل سيرفر: إذا اثنين شغّلوا الأمر بنفس اللحظة، الثاني يطلع له خطأ
    async handlePlay(interaction) {
        if (busyGuilds.has(interaction.guildId)) {
            await interaction.reply({
                content: "⚠️ حدث خطأ: شخص ثاني يستخدم الأمر بنفس اللحظة بهذا السيرفر. أعد المحاولة بعد ثواني.",
                ephemeral: true
            });
            return;
        }
        busyGuilds.add(interaction.guildId);
        try {
            await module.exports._play(interaction);
        } catch (e) {
            console.error('خطأ في /play_music:', e);
            const msg = "❌ حدث خطأ غير متوقع، أعد المحاولة.";
            if (interaction.deferred || interaction.replied) await interaction.editReply(msg).catch(() => {});
            else await interaction.reply({ content: msg, ephemeral: true }).catch(() => {});
        } finally {
            busyGuilds.delete(interaction.guildId);
        }
    },

    async _play(interaction) {
        await interaction.deferReply({ ephemeral: true });

        const guild = interaction.guild;
        const link = interaction.options.getString('link').trim();
        if (!/^https?:\/\//i.test(link)) {
            await interaction.editReply("❌ لازم تحط رابط صحيح يبدأ بـ http أو https.");
            return;
        }
        if (!YT_ID.test(link)) {
            await interaction.editReply("❌ حالياً أدعم روابط **يوتيوب** فقط.");
            return;
        }

        const channel = interaction.options.getChannel('channel') || interaction.member.voice?.channel;
        if (!channel) {
            await interaction.editReply("❌ اختر روم صوتي بخيار `channel`، أو ادخل روم صوتي وشغّل الأمر.");
            return;
        }
        if (!channel.joinable || !channel.speakable) {
            await interaction.editReply("❌ ما عندي صلاحية الدخول أو التكلم بهذا الروم (Connect / Speak).");
            return;
        }

        // نجيب معلومات الفيديو قبل ما ندخل الروم، حتى لو فشل ما يدخل بدون فايدة
        let track;
        try {
            track = await resolveTrack(link);
        } catch (e) {
            console.error('فشل جلب الفيديو:', e.message);
            await interaction.editReply("❌ ما قدرت أجيب الصوت من يوتيوب. تأكد أن الفيديو عام ويشتغل. (ممكن يوتيوب حاظر عنوان الاستضافة)");
            return;
        }

        // الاتصال بالروم
        let connection = getVoiceConnection(guild.id);
        let state = states.get(guild.id);

        if (connection && (connection.joinConfig.channelId !== channel.id || !state)) {
            if (connection.state.status !== VoiceConnectionStatus.Destroyed) connection.destroy();
            connection = null;
            state = null;
        }

        if (!connection) {
            connection = joinVoiceChannel({
                channelId: channel.id,
                guildId: guild.id,
                adapterCreator: guild.voiceAdapterCreator,
                selfDeaf: true
            });
            try {
                await entersState(connection, VoiceConnectionStatus.Ready, 20000);
            } catch (e) {
                if (connection.state.status !== VoiceConnectionStatus.Destroyed) connection.destroy();
                await interaction.editReply("❌ ما قدرت أدخل الروم الصوتي (انتهت المهلة).");
                return;
            }
            state = createState(guild, channel, connection, interaction);
        }

        // تغيير النغمة = نفس الأمر برابط جديد
        state.interaction = interaction;
        state.url = link;
        state.retries = 0;

        try {
            await startPlayback(state, track);
        } catch (e) {
            console.error('فشل بدء التشغيل:', e.message);
            await interaction.editReply("❌ صار خطأ أثناء التشغيل.");
            return;
        }

        await interaction.editReply(buildPanel(state));
    },

    async handleButton(interaction) {
        await interaction.deferUpdate();

        const state = states.get(interaction.guildId);
        if (!state) {
            await interaction.editReply({ content: "ℹ️ ما في تشغيل حالياً. استخدم `/play_music`.", components: [] });
            return;
        }
        state.interaction = interaction;

        try {
            if (interaction.customId === 'music_toggle') {
                const status = state.player.state.status;
                if (status === AudioPlayerStatus.Playing || status === AudioPlayerStatus.Buffering) {
                    state.player.pause();
                } else if (status === AudioPlayerStatus.Paused || status === AudioPlayerStatus.AutoPaused) {
                    state.player.unpause();
                } else {
                    await startPlayback(state);
                }
            } else if (interaction.customId === 'music_loop') {
                state.loop = !state.loop;
            } else if (interaction.customId === 'music_stop') {
                if (state.connection.state.status !== VoiceConnectionStatus.Destroyed) state.connection.destroy();
                await interaction.editReply({ content: "⏹️ تم الإيقاف والخروج من الروم.", components: [] });
                return;
            }
            await interaction.editReply(buildPanel(state));
        } catch (e) {
            console.error('خطأ في أزرار الموسيقى:', e.message);
            await interaction.editReply({ ...buildPanel(state), content: "❌ صار خطأ، جرب مرة ثانية." }).catch(() => {});
        }
    }
};
