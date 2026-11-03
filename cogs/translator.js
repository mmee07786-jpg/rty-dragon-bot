const { EmbedBuilder } = require('discord.js');

// قائمة شاملة لربط أعلام الدول برموز اللغات
const flagToLang = {
    // الدول العربية
    "🇮🇶": "ar", "🇸🇦": "ar", "🇪🇬": "ar", "🇦🇪": "ar", "🇸🇾": "ar",
    "🇯🇴": "ar", "🇱🇧": "ar", "🇰🇼": "ar", "🇶🇦": "ar", "🇧🇭": "ar",
    "🇴🇲": "ar", "🇾🇪": "ar", "🇵🇸": "ar", "🇩🇿": "ar", "🇲🇦": "ar",
    "🇹🇳": "ar", "🇸🇩": "ar", "🇱🇾": "ar", "🇸🇴": "ar", "🇲🇷": "ar",

    // اللغات الأجنبية الشائعة
    "🇺🇸": "en", "🇬🇧": "en", "🇨🇦": "en", "🇦🇺": "en",
    "🇫🇷": "fr",
    "🇪🇸": "es",
    "🇩🇪": "de",
    "🇹🇷": "tr",
    "🇮🇷": "fa",
    "🇷🇺": "ru",
    "🇮🇹": "it",
    "🇨🇳": "zh-CN",
    "🇯🇵": "ja",
    "🇰🇷": "ko",
    "🇧🇷": "pt", "🇵🇹": "pt",
    "🇮🇳": "hi",
    "🇵🇰": "ur"
};

// Node 18+ عنده fetch جاهز. إذا نسخة أقدم، نحاول node-fetch كبديل.
let fetchFn = (typeof fetch === 'function') ? fetch : null;
if (!fetchFn) {
    try {
        fetchFn = require('node-fetch');
        console.log("ℹ️ نظام الترجمة يستخدم node-fetch (Node قديم بدون fetch مدمج).");
    } catch (e) {
        fetchFn = null;
        console.log("❌ نظام الترجمة معطّل: لا توجد دالة fetch ولا مكتبة node-fetch مثبتة. ثبّت Node.js 18+ أو شغّل: npm install node-fetch");
    }
}

// محاولة 1: Google (سريعة لكن IP الاستضافات المشتركة يتعرض لحظر 429 أحياناً)
async function translateViaGoogle(text, targetLang) {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t`;
    const body = new URLSearchParams({ q: text }).toString();

    const response = await fetchFn(url, {
        method: "POST",
        headers: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body
    });

    if (response.status === 429) {
        const err = new Error("RATE_LIMITED");
        err.code = 429;
        throw err;
    }
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return data[0].map(item => item[0]).filter(Boolean).join("");
}

// MyMemory ما يقبل "auto" كلغة مصدر، فنحزر لغة النص بشكل تقريبي حسب نوع الحروف
function guessSourceLang(text) {
    if (/[\u0600-\u06FF]/.test(text)) return "ar";       // عربي
    if (/[\u0400-\u04FF]/.test(text)) return "ru";       // روسي
    if (/[\u3040-\u30FF]/.test(text)) return "ja";       // ياباني
    if (/[\uAC00-\uD7AF]/.test(text)) return "ko";       // كوري
    if (/[\u4E00-\u9FFF]/.test(text)) return "zh-CN";    // صيني
    if (/[\u0590-\u05FF]/.test(text)) return "he";       // عبري
    return "en"; // افتراضي لأي حروف لاتينية أو غير معروفة
}

// محاولة 2 (احتياطية): MyMemory، تُستخدم فقط إذا Google رفض الطلب (429) أو فشل
async function translateViaMyMemory(text, targetLang) {
    let sourceLang = guessSourceLang(text);
    if (sourceLang === targetLang) sourceLang = "en"; // تجنب ar|ar أو نفس اللغة للمصدر والهدف

    const langPair = `${sourceLang}|${targetLang}`;
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${encodeURIComponent(langPair)}`;

    const response = await fetchFn(url, {
        headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" }
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    const text2 = data && data.responseData && data.responseData.translatedText;
    if (!text2) throw new Error("NO_TRANSLATION");

    // MyMemory أحياناً يرجع رسالة خطأ نصية (مثل "'XX' IS AN INVALID...") بدل الترجمة الفعلية
    if (/IS AN INVALID (SOURCE|TARGET) LANGUAGE/i.test(text2) || /QUERY LENGTH LIMIT/i.test(text2)) {
        throw new Error(`MYMEMORY_REJECTED: ${text2}`);
    }

    return text2;
}

// يترجم مقطع واحد: يجرب Google، وإذا انحظر (429) أو فشل يتحول لـ MyMemory تلقائياً
async function translateChunk(text, targetLang) {
    if (!fetchFn) return null;

    for (let attempt = 1; attempt <= 2; attempt++) {
        try {
            return await translateViaGoogle(text, targetLang);
        } catch (e) {
            if (e.code === 429) {
                console.log(`⚠️ Google رفض الطلب (429 - طلبات كثيرة من IP الاستضافة). جاري المحاولة بخدمة بديلة...`);
            } else {
                console.log(`⚠️ خطأ من Google: ${e.message}. جاري المحاولة بخدمة بديلة...`);
            }
            break; // ننتقل فوراً للخدمة البديلة بدل الانتظار
        }
    }

    try {
        return await translateViaMyMemory(text, targetLang);
    } catch (e) {
        console.log(`⚠️ فشلت أيضاً الخدمة البديلة: ${e.message}`);
        return null;
    }
}

// يقسم النص الطويل جداً إلى مقاطع (حسب أقرب مسافة) حتى لا يتجاوز حد Google للطلب الواحد
function splitIntoChunks(text, maxLen = 3500) {
    if (text.length <= maxLen) return [text];
    const chunks = [];
    let remaining = text;
    while (remaining.length > maxLen) {
        let cut = remaining.lastIndexOf(" ", maxLen);
        if (cut <= 0) cut = maxLen;
        chunks.push(remaining.slice(0, cut));
        remaining = remaining.slice(cut).trimStart();
    }
    if (remaining) chunks.push(remaining);
    return chunks;
}

async function translateText(text, targetLang) {
    if (!fetchFn) return null;
    const chunks = splitIntoChunks(text);
    const results = [];
    for (const chunk of chunks) {
        const translated = await translateChunk(chunk, targetLang);
        if (translated === null) return null; // فشل مقطع = نوقف، حتى لا نرسل ترجمة ناقصة
        results.push(translated);
    }
    return results.join(" ");
}

module.exports = {
    async handleRawReactionAdd(payload, client) {
        // تجاهل تفاعل البوت نفسه
        if (payload.user_id === client.user.id) return;

        const emojiStr = payload.emoji.name;
        const fullEmoji = payload.emoji.id ? `<:${payload.emoji.name}:${payload.emoji.id}>` : payload.emoji.name;

        const targetLang = flagToLang[fullEmoji] || flagToLang[emojiStr];
        if (!targetLang) return;

        const channel = client.channels.cache.get(payload.channel_id) || await client.channels.fetch(payload.channel_id).catch(() => null);
        if (!channel || !channel.isTextBased()) return;

        let message;
        try {
            message = await channel.messages.fetch(payload.message_id);
        } catch (e) {
            console.log(`⚠️ تعذر جلب الرسالة للترجمة: ${e.message}`);
            return;
        }

        if (!message.content || !message.content.trim()) {
            // إذا وصل هنا فارغ رغم إن الرسالة فيها نص، فالسبب الأكيد:
            // Message Content Intent غير مفعّل من Discord Developer Portal
            console.log("⚠️ محتوى الرسالة فارغ عند البوت. تأكد إن 'MESSAGE CONTENT INTENT' مفعّل من Developer Portal > Bot.");
            return;
        }

        try {
            const textToTranslate = message.content.trim();
            let translatedText = await translateText(textToTranslate, targetLang);
            if (!translatedText) return;

            // حد ديسكورد لوصف الـ Embed هو 4096 حرف
            if (translatedText.length > 4096) {
                translatedText = translatedText.slice(0, 4090) + " …";
            }

            let member = payload.member;
            if (!member) {
                member = await channel.guild.members.fetch(payload.user_id).catch(() => null);
            }

            const memberMention = member ? member.toString() : `<@${payload.user_id}>`;
            const footerName = member ? member.displayName : "عضو";
            const footerAvatar = member ? member.displayAvatarURL() : null;

            const embed = new EmbedBuilder()
                .setDescription(translatedText)
                .setColor(0x2ECC71)
                .setAuthor({ name: "الترجمة الفورية", iconURL: "https://i.imgur.com/3Z4h7uK.png" })
                .setFooter({ text: `تمت الترجمة بواسطة ${footerName}`, iconURL: footerAvatar });

            await message.reply({
                content: `🌐 | ترجمة الرسالة بناءً على طلب ${memberMention}:`,
                embeds: [embed],
                allowedMentions: { parse: [] }
            });

        } catch (e) {
            console.log(`⚠️ خطأ أثناء تنفيذ الترجمة: ${e.message}`);
        }
    }
};
