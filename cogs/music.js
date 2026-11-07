const { SlashCommandBuilder, PermissionFlagsBits, ChannelType, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const {
    joinVoiceChannel, createAudioPlayer, createAudioResource, entersState, getVoiceConnection,
    AudioPlayerStatus, VoiceConnectionStatus, NoSubscriberBehavior
} = require('@discordjs/voice');
const { execFile } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');

const BIN_DIR = path.join(__dirname, '../bin');
const BIN_PATH = path.join(BIN_DIR, process.platform === 'win32' ? 'yt-dlp.exe' : 'yt-dlp');
const MAX_BIN_AGE = 3 * 24 * 60 * 60 * 1000; // نحدّث yt-dlp كل 3 أيام
const MEDIA_EXT = /\.(mp3|mp4|m4a|aac|wav|ogg|opus|flac|webm|mkv|mov)(\?.*)?$/i;

// حالة التشغيل لكل سيرفر
const states = new Map();
// السيرفرات اللي فيها أمر /play شغال حالياً (للقفل)
const busyGuilds = new Set();

/* ---------------- جلب الصوت من الرابط ---------------- */

/* ---------- تثبيت yt-dlp تلقائياً (بدون صلاحيات على الاستضافة) ---------- */

function candidates() {
    const arm = process.arch === 'arm64';
    if (process.platform === 'win32') return ['yt-dlp.exe'];
    if (process.platform === 'darwin') return ['yt-dlp_macos'];
    return arm ? ['yt-dlp_linux_aarch64', 'yt-dlp_musllinux_aarch64'] : ['yt-dlp_linux', 'yt-dlp_musllinux'];
}

function download(url, dest, redirects = 0) {
    return new Promise((resolve, reject) => {
        if (redirects > 6) return reject(new Error('too many redirects'));
        https.get(url, { headers: { 'User-Agent': 'discord-bot' } }, res => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                res.resume();
                return resolve(download(res.headers.location, dest, redirects + 1));
            }
            if (res.statusCode !== 200) { res.resume(); return reject(new Error('HTTP ' + res.statusCode)); }
            const file = fs.createWriteStream(dest);
            res.pipe(file);
            file.on('finish', () => file.close(() => resolve()));
            file.on('error', reject);
        }).on('error', reject);
    });
}

function testBinary(bin) {
    return new Promise(resolve => {
        execFile(bin, ['--version'], { timeout: 20000 }, err => resolve(!err));
    });
}

let ytdlpPromise = null;
function getYtdlpPath() {
    if (process.env.YTDLP_PATH) return Promise.resolve(process.env.YTDLP_PATH);
    if (!ytdlpPromise) {
        ytdlpPromise = ensureYtdlp().catch(e => { ytdlpPromise = null; throw e; });
    }
    return ytdlpPromise;
}

async function ensureYtdlp() {
    fs.mkdirSync(BIN_DIR, { recursive: true });

    // إذا موجود وحديث وشغّال نستخدمه
    if (fs.existsSync(BIN_PATH)) {
        const fresh = Date.now() - fs.statSync(BIN_PATH).mtimeMs < MAX_BIN_AGE;
        if (fresh && await testBinary(BIN_PATH)) return BIN_PATH;
    }

    for (const name of candidates()) {
        const tmp = BIN_PATH + '.tmp';
        try {
            console.log(`⬇️ جاري تحميل yt-dlp (${name})...`);
            await download(`https://github.com/yt-dlp/yt-dlp/releases/latest/download/${name}`, tmp);
            fs.chmodSync(tmp, 0o755);
            if (await testBinary(tmp)) {
                fs.renameSync(tmp, BIN_PATH);
                console.log('✅ تم تجهيز yt-dlp');
                return BIN_PATH;
            }
        } catch (e) {
            console.error(`فشل تحميل ${name}:`, e.message);
        }
        try { fs.unlinkSync(tmp); } catch (e) {}
    }

    // إذا فشل التحديث لكن عندنا نسخة قديمة تشتغل نستخدمها
    if (fs.existsSync(BIN_PATH) && await testBinary(BIN_PATH)) return BIN_PATH;
    throw Object.assign(new Error('YTDLP_MISSING'), { code: 'ENOENT' });
}

function execYtdlp(bin, args) {
    return new Promise((resolve, reject) => {
        execFile(bin, args, { timeout: 60000, maxBuffer: 1024 * 1024 }, (err, stdout, stderr) => {
            if (err) { err.stderr = stderr || ''; return reject(err); }
            const lines = stdout.trim().split('\n').filter(Boolean);
            if (lines.length < 2) return reject(new Error('no output'));
            resolve({ title: lines[0], direct: lines[lines.length - 1] });
        });
    });
}

async function runYtdlp(link) {
    const bin = await getYtdlpPath();
    const base = ['--no-playlist', '--no-warnings', '-f', 'bestaudio/best', '--print', '%(title)s', '--print', '%(url)s', link];
    try {
        // يوتيوب يحتاج JavaScript runtime، نستخدم نفس Node اللي يشغّل البوت
        return await execYtdlp(bin, ['--js-runtimes', `node:${process.execPath}`, ...base]);
    } catch (e) {
        if (/no such option|unrecognized arguments/i.test(e.stderr || '')) return await execYtdlp(bin, base);
        throw e;
    }
}

function nameFromLink(link) {
    try { return decodeURIComponent(link.split('/').pop().split('?')[0]) || 'ملف صوتي'; }
    catch (e) { return 'ملف صوتي'; }
}

async function resolveTrack(link) {
    // رابط ملف مباشر (mp3, mp4...) ما يحتاج yt-dlp
    if (MEDIA_EXT.test(link)) return { title: nameFromLink(link), direct: link };
    try {
        return await runYtdlp(link);
    } catch (e) {
        if (e.code === 'ENOENT') throw new Error('YTDLP_MISSING');
        console.error('yt-dlp error:', (e.stderr || e.message).slice(-600));
        if (/confirm you.re not a bot|Sign in to confirm/i.test(e.stderr || '')) throw new Error('YT_BLOCKED');
        throw new Error('YTDLP_FAILED');
    }
}

/* ---------------- التشغيل ---------------- */

async function startPlayback(state) {
    // رابط الستريم المباشر ينتهي بعد فترة، فنجدده إذا مر نص ساعة
    if (!state.direct || Date.now() - state.directAt > 30 * 60 * 1000) {
        const t = await resolveTrack(state.url);
        state.direct = t.direct;
        state.title = t.title;
        state.directAt = Date.now();
    }
    state.player.play(createAudioResource(state.direct));
}

function cleanup(guildId, connection) {
    const st = states.get(guildId);
    if (!st || st.connection !== connection) return;
    states.delete(guildId);
    try { st.player.stop(true); } catch (e) {}
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
        url: null, title: '', direct: null, directAt: 0,
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
                // خطأ بالستريم (غالباً الرابط انتهى): نحاول مرة وحدة نجدد الرابط
                state.errored = false;
                if (state.retries < 1) {
                    state.retries++;
                    state.direct = null;
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
    // يجهّز yt-dlp وقت تشغيل البوت حتى أول تشغيل يكون سريع
    async prepare() {
        try { await getYtdlpPath(); }
        catch (e) { console.error('⚠️ تعذر تجهيز yt-dlp:', e.message); }
    },

    playCommand: new SlashCommandBuilder()
        .setName('play_music')
        .setDescription('تشغيل رابط فيديو أو صوت داخل روم صوتي')
        .addStringOption(o => o.setName('link').setDescription('رابط الفيديو أو الصوت').setRequired(true))
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
            console.error('خطأ في /play:', e);
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

        const channel = interaction.options.getChannel('channel') || interaction.member.voice?.channel;
        if (!channel) {
            await interaction.editReply("❌ اختر روم صوتي بخيار `channel`، أو ادخل روم صوتي وشغّل الأمر.");
            return;
        }
        if (!channel.joinable || !channel.speakable) {
            await interaction.editReply("❌ ما عندي صلاحية الدخول أو التكلم بهذا الروم (Connect / Speak).");
            return;
        }

        // نجيب الرابط قبل ما ندخل الروم، حتى لو فشل ما يدخل بدون فايدة
        let track;
        try {
            track = await resolveTrack(link);
        } catch (e) {
            const msg = e.message === 'YTDLP_MISSING'
                ? "❌ ما قدرت أجهّز أداة yt-dlp على الاستضافة. روابط الملفات المباشرة (mp3/mp4) تشتغل، بس يوتيوب وغيره يحتاج yt-dlp."
                : e.message === 'YT_BLOCKED'
                ? "❌ يوتيوب حاظر عنوان الاستضافة (يطلب تسجيل دخول). جرب رابط من موقع ثاني، أو قلّي ونحل المشكلة."
                : "❌ ما قدرت أجيب الصوت من هذا الرابط. تأكد أنه عام ويشتغل.";
            await interaction.editReply(msg);
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
        state.title = track.title;
        state.direct = track.direct;
        state.directAt = Date.now();
        state.retries = 0;

        try {
            await startPlayback(state);
        } catch (e) {
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
