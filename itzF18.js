const { Client, GatewayIntentBits, Collection } = require('discord.js');
const fs = require('fs');
const path = require('path');

class MyBot extends Client {
    constructor() {
        super({
            intents: [
                GatewayIntentBits.Guilds,
                GatewayIntentBits.GuildMembers,
                GatewayIntentBits.GuildMessages,
                GatewayIntentBits.MessageContent
            ]
        });

        this.commands = new Collection();
    }

    async init() {
        // تحميل جميع ملفات JavaScript من مجلد cogs تلقائياً مع معالجة الأخطاء
        const cogsPath = path.join(__dirname, 'cogs');
        if (fs.existsSync(cogsPath)) {
            const commandFiles = fs.readdirSync(cogsPath).filter(file => file.endsWith('.js'));
            for (const file of commandFiles) {
                const cogName = file.replace('.js', '');
                try {
                    // استدعاء الملف للتأكد من عمله
                    require(`./cogs/${file}`);
                    console.log(`تم تحميل الملف بنجاح: ${cogName}`);
                } catch (error) {
                    console.log(`فشل تحميل الملف ${cogName}: ${error.message}`);
                }
            }
        }

        // حدث عندما يصبح البوت جاهزاً
        this.once('ready', () => {
            console.log(`البوت جاهز الآن ويعمل باسم: ${this.user.tag} (ID: ${this.user.id})`);
            console.log("-----------------------------------------");
        });

        // نظام حماية عالمي لمنع البوت من الكراش بسبب الأخطاء غير المعالجة
        process.on('unhandledRejection', error => {
            console.error('خطأ تم رصده وتجاوزه لمنع الكراش:', error);
        });

        // تشغيل البوت مع التوكن الصحيح من متغيرات البيئة (دعم TOKEN أو DISCORD_TOKEN)
        const token = process.env.TOKEN || process.env.DISCORD_TOKEN;
        if (token) {
            try {
                await this.login(token);
            } catch (error) {
                console.log(`خطأ حرج في التشغيل: ${error.message}`);
            }
        } else {
            console.log("خطأ: لم يتم العثور على التوكن في متغيرات البيئة!");
        }
    }
}

const bot = MyBotClient = new MyBot();
bot.init();

module.exports = bot;
