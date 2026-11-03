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

async function translateText(text, targetLang) {
    if (!fetchFn) return null;
    try {
        const encodedText = encodeURIComponent(text);
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodedText}`;

        const response = await fetchFn(url, {
            headers: {
                // بعض الاستضافات تحجب الطلبات بدون User-Agent فيرجع Google خطأ 403
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        });

        if (!response.ok) {
            console.log(`⚠️ خدمة الترجمة رفضت الطلب (HTTP ${response.status}). جرب لاحقاً أو تأكد إن الاستضافة ما تحجب الاتصال بـ Google.`);
            return null;
        }

        const data = await response.json();
        const translatedParts = data[0].map(item => item[0]).filter(Boolean);
        return translatedParts.join("");
    } catch (e) {
        console.log(`⚠️ خطأ في اتصال الترجمة: ${e.message}`);
    }
    return null;
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
            const translatedText = await translateText(textToTranslate, targetLang);
            if (!translatedText) return;

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
