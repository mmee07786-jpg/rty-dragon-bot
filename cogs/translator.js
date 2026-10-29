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

async function translateText(text, targetLang) {
    try {
        const encodedText = encodeURIComponent(text);
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodedText}`;
        
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            // تجميع أجزاء النص المترجم بدقة كاملة
            const translatedParts = data[0].map(item => item[0]).filter(Boolean);
            return translatedParts.join("");
        }
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
        // إذا كان الإيموجي عبارة عن علم مركب (Custom or Unicode emoji handling)
        const fullEmoji = payload.emoji.id ? `<:${payload.emoji.name}:${payload.emoji.id}>` : payload.emoji.name;

        // التحقق مما إذا كان الإيموجي موجوداً في القائمة
        const targetLang = flagToLang[fullEmoji] || flagToLang[emojiStr];
        if (!targetLang) return;

        const channel = client.channels.cache.get(payload.channel_id) || await client.channels.fetch(payload.channel_id).catch(() => null);
        if (!channel || !channel.isTextBased()) return;

        let message;
        try {
            message = await channel.messages.fetch(payload.message_id);
        } catch (e) {
            return;
        }

        // التأكد من وجود محتوى نصي بالرسالة
        if (!message.content || !message.content.trim()) return;

        try {
            const textToTranslate = message.content.trim();
            
            // جلب الترجمة الفورية المباشرة
            const translatedText = await translateText(textToTranslate, targetLang);
            if (!translatedText) return;

            // جلب معلومات العضو لعمل المنشن بدقة
            let member = payload.member;
            if (!member) {
                member = await channel.guild.members.fetch(payload.user_id).catch(() => null);
            }

            const memberMention = member ? member.toString() : `<@${payload.user_id}>`;
            const footerName = member ? member.displayName : "عضو";
            const footerAvatar = member ? member.displayAvatarURL() : null;

            // تصميم الرد
            const embed = new EmbedBuilder()
                .setDescription(translatedText)
                .setColor(0x2ECC71)
                .setAuthor({ name: "الترجمة الفورية", iconURL: "https://i.imgur.com/3Z4h7uK.png" })
                .setFooter({ text: `تمت الترجمة بواسطة ${footerName}`, iconURL: footerAvatar });

            // الرد مع منشن الشخص
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
