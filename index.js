const { Client, GatewayIntentBits, Collection } = require('discord.js');

const client = new Client({
    intents: [GatewayIntentBits.All]
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

// التعامل مع الأخطاء العامة
process.on('unhandledRejection', error => {
    console.error('⚠️ خطأ غير معالج:', error);
});

// تشغيل البوت باستخدام توكن الحماية الموجود في متغيرات البيئة بدون تغيير الاسم
client.login(process.env.TOKEN);
