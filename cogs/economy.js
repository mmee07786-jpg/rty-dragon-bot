const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder } = require('discord.js');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '../data.json');

function loadData() {
    if (fs.existsSync(DATA_FILE)) {
        try {
            const data = fs.readFileSync(DATA_FILE, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return {};
        }
    }
    return {};
}

function saveData(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 4), 'utf8');
    } catch (error) {
        console.error("خطأ في حفظ البيانات:", error);
    }
}

module.exports = {
    dailyCommand: new SlashCommandBuilder()
        .setName('daily')
        .setDescription('استلم جائزتك اليومية من عملة أورا (كل 24 ساعة) - متاح للجميع'),

    balanceCommand: new SlashCommandBuilder()
        .setName('balance')
        .setDescription('معرفة رصيدك من عملة أورا أو رصيد عضو آخر (الرصيد عام بكل السيرفرات)')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد الاستعلام عن رصيده')),

    giveCommand: new SlashCommandBuilder()
        .setName('give')
        .setDescription('[خاص بمنشئ البوت فقط] إعطاء عملة أورا لعضو معين')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد إعطاؤه العملات')
                .setRequired(true))
        .addIntegerOption(option =>
            option.setName('amount')
                .setDescription('الكمية المراد إضافتها')
                .setRequired(true)),

    takeMoneyCommand: new SlashCommandBuilder()
        .setName('take_money')
        .setDescription('[خاص بمنشئ البوت فقط] سحب عملات من عضو متطاول وتأديبه')
        .addUserOption(option =>
            option.setName('member')
                .setDescription('العضو المراد سحب الأموال منه')
                .setRequired(true))
        .addIntegerOption(option =>
            option.setName('amount')
                .setDescription('الكمية المراد سحبها')
                .setRequired(true)),

    storeAddCommand: new SlashCommandBuilder()
        .setName('store_add')
        .setDescription('[خاص بالإدارة] إضافة سلعة جديدة لمتجر هذا السيرفر فقط مع الوصف والسعر')
        .addStringOption(option =>
            option.setName('item_name')
                .setDescription('اسم السلعة')
                .setRequired(true))
        .addIntegerOption(option =>
            option.setName('price')
                .setDescription('سعر السلعة بأورا')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('description')
                .setDescription('وصف السلعة')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('image_url')
                .setDescription('رابط صورة السلعة (اختياري)'))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    storeRemoveCommand: new SlashCommandBuilder()
        .setName('store_remove')
        .setDescription('[خاص بالإدارة] حذف سلعة من متجر هذا السيرفر')
        .addStringOption(option =>
            option.setName('item_name')
                .setDescription('اسم السلعة المراد حذفها')
                .setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    storeCommand: new SlashCommandBuilder()
        .setName('store')
        .setDescription('عرض سلع متجر هذا السيرفر الحالية فقط'),

    buyCommand: new SlashCommandBuilder()
        .setName('buy')
        .setDescription('شراء سلعة من متجر هذا السيرفر (يخصم من رصيدك العام)')
        .addStringOption(option =>
            option.setName('item_name')
                .setDescription('اسم السلعة المراد شراؤها')
                .setRequired(true)),

    async handleDaily(interaction) {
        await interaction.deferReply();
        const userId = interaction.user.id;
        const currentTime = Date.now() / 1000; // بالثواني

        const data = loadData();
        if (!data.dailies) data.dailies = {};

        const lastClaim = data.dailies[userId] || 0;
        const cooldown = 86400; // 24 ساعة بالثواني

        if (currentTime - lastClaim < cooldown) {
            const remaining = Math.floor(cooldown - (currentTime - lastClaim));
            const hours = Math.floor(remaining / 3600);
            const minutes = Math.floor((remaining % 3600) / 60);
            await interaction.followup({ content: `⏳ | لقد استلمت جائزتك اليومية مسبقاً! يمكنك استلامها مرة أخرى بعد **{hours} ساعة و {minutes} دقيقة**.`.replace('{hours}', hours).replace('{minutes}', minutes), ephemeral: true });
            return;
        }

        const dailyAmount = 500;
        if (!data.balances) data.balances = {};

        data.balances[userId] = (data.balances[userId] || 0) + dailyAmount;
        data.dailies[userId] = currentTime;
        saveData(data);

        const newBal = data.balances[userId];
        await interaction.followup.send(`🎁 | مبروك يا ${interaction.user}! استلمت جائزتك اليومية بنجاح وحصلت على **{dailyAmount} أورا** 🪙\n💰 رصيدك العام الحالي: **{newBal} أورا**`.replace('{dailyAmount}', dailyAmount).replace('{newBal}', newBal));
    },

    async handleBalance(interaction) {
        await interaction.deferReply();
        const target = interaction.options.getUser('member') || interaction.user;
        const userId = target.id;

        const data = loadData();
        const balances = data.balances || {};
        const bal = balances[userId] || 0;

        await interaction.followup.send(`💰 | رصيد العضو ${target} هو: **{bal} أورا** 🪙`.replace('{bal}', bal));
    },

    async handleGive(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const appInfo = await interaction.client.application.fetch();
        if (interaction.user.id !== appInfo.owner.id) {
            await interaction.followup.send({ content: "❌ | عذراً، هذا الأمر مخصص **لمنشئ البوت** فقط ولا يحق لأحد استخدامه!", ephemeral: true });
            return;
        }

        const member = interaction.options.getUser('member');
        const amount = interaction.options.getInteger('amount');

        if (amount <= 0) {
            await interaction.followup.send({ content: "❌ | يجب أن يكون المبلغ أكبر من صفر!", ephemeral: true });
            return;
        }

        const userId = member.id;
        const data = loadData();
        if (!data.balances) data.balances = {};

        const currentBal = data.balances[userId] || 0;
        const newBal = currentBal + amount;
        data.balances[userId] = newBal;
        saveData(data);

        await interaction.followup.send({ content: `✅ | تم بنجاح إضافة **{amount} أورا** إلى رصيد العضو ${member}.\nرصيده الحالي العام: **{newBal} أورا** 🪙`.replace('{amount}', amount).replace('{newBal}', newBal) });
    },

    async handleTakeMoney(interaction) {
        await interaction.deferReply({ ephemeral: true });
        const appInfo = await interaction.client.application.fetch();
        if (interaction.user.id !== appInfo.owner.id) {
            await interaction.followup.send({ content: "❌ | عذراً، هذا الأمر مخصص **لمنشئ البوت** فقط لتأديب المتطاولين!", ephemeral: true });
            return;
        }

        const member = interaction.options.getUser('member');
        let amount = interaction.options.getInteger('amount');

        if (amount <= 0) {
            await interaction.followup.send({ content: "❌ | يجب أن يكون المبلغ المراد سحبه أكبر من صفر!", ephemeral: true });
            return;
        }

        const userId = member.id;
        const data = loadData();
        if (!data.balances) data.balances = {};

        const currentBal = data.balances[userId] || 0;
        if (currentBal < amount) {
            amount = currentBal;
        }

        const newBal = currentBal - amount;
        data.balances[userId] = newBal;
        saveData(data);

        const embed = new EmbedBuilder()
            .setTitle("⚖️ تأديب وسحب أموال")
            .setDescription(`تم سحب **{amount} أورا** من العضو ${member} لأنه كان يتباهى ويتطاول على الشباب! 😎\n💰 رصيده الحالي العام: **{newBal} أورا**`.replace('{amount}', amount).replace('{newBal}', newBal))
            .setColor(0xFF0000)
            .setFooter({ text: "بواسطة المطور الشخصي للبوت" });

        await interaction.followup.send({ embeds: [embed] });
    },

    async handleStoreAdd(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const itemName = interaction.options.getString('item_name');
        const price = interaction.options.getInteger('price');
        const description = interaction.options.getString('description');
        const imageUrl = interaction.options.getString('image_url');

        const data = loadData();
        if (!data.shops) data.shops = {};
        if (!data.shops[guildId]) data.shops[guildId] = [];

        const item = {
            name: itemName,
            price: price,
            description: description,
            image: imageUrl
        };

        data.shops[guildId].push(item);
        saveData(data);

        await interaction.followup.send(`✅ | تم إضافة السلعة **{itemName}** بنجاح إلى متجر **هذا السيرفر فقط**!\n💵 السعر: \`{price} أورا\`\n📝 الوصف: \`{description}\``
            .replace('{itemName}', itemName)
            .replace('{price}', price)
            .replace('{description}', description));
    },

    async handleStoreRemove(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const itemName = interaction.options.getString('item_name');

        const data = loadData();
        if (!data.shops || !data.shops[guildId] || data.shops[guildId].length === 0) {
            await interaction.followup.send({ content: "❌ | متجر هذا السيرفر فارغ أساساً!", ephemeral: true });
            return;
        }

        const initialLen = data.shops[guildId].length;
        data.shops[guildId] = data.shops[guildId].filter(item => item.name.toLowerCase() !== itemName.toLowerCase());

        if (data.shops[guildId].length < initialLen) {
            saveData(data);
            await interaction.followup.send(`🗑️ | تم حذف السلعة **{itemName}** من متجر هذا السيرفر بنجاح.`.replace('{itemName}', itemName));
        } else {
            await interaction.followup.send({ content: `❌ | لم يتم العثور على سلعة بهذا الاسم في متجر هذا السيرفر.`, ephemeral: true });
        }
    },

    async handleStore(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const data = loadData();
        const items = data.shops?.[guildId] || [];

        if (items.length === 0) {
            await interaction.followup.send("🛒 | متجر هذا السيرفر فارغ حالياً، لم يقم الإداريون بإضافة أي سلع هنا بعد.");
            return;
        }

        const embed = new EmbedBuilder()
            .setTitle(`🛍️ | متجر سيرفر: ${interaction.guild.name} (عملة أورا)`)
            .setColor(0x9b59b6)
            .setDescription("قائمة السلع المخصصة لهذا السيرفر فقط:");

        items.forEach((item, idx) => {
            embed.addFields({
                name: `${idx + 1}. ${item.name} - 💵 ${item.price} أورا`,
                value: `📝 **الوصف:** ${item.description}`,
                inline: false
            });
        });

        await interaction.followup.send({ embeds: [embed] });
    },

    async handleBuy(interaction) {
        await interaction.deferReply();
        const guildId = interaction.guild.id;
        const itemName = interaction.options.getString('item_name');

        const data = loadData();
        const items = data.shops?.[guildId] || [];
        const targetItem = items.find(i => i.name.toLowerCase() === itemName.toLowerCase());

        if (!targetItem) {
            await interaction.followup.send({ content: "❌ | عذراً، هذه السلعة غير موجودة في متجر هذا السيرفر. تأكد من الاسم عبر أمر `/store`", ephemeral: true });
            return;
        }

        const userId = interaction.user.id;
        if (!data.balances) data.balances = {};

        const userBalance = data.balances[userId] || 0;
        const itemPrice = targetItem.price;

        if (userBalance < itemPrice) {
            await interaction.followup.send({ content: `❌ | رصيدك غير كافٍ! رصيدك العام الحالي هو \`{userBalance} أورا\` بينما السعر المطلوب هو \`{itemPrice} أورا\`.`.replace('{userBalance}', userBalance).replace('{itemPrice}', itemPrice), ephemeral: true });
            return;
        }

        data.balances[userId] -= itemPrice;
        saveData(data);

        const remainingBalance = data.balances[userId];
        await interaction.followup.send(`🎉 | مبروك يا ${interaction.user}! اشتريت بنجاح سلعة **{itemName}** مقابل \`{itemPrice} أورا\` من متجر هذا السيرفر.\n💰 رصيدك العام المتبقي: \`{remainingBalance} أورا\` 🪙✨`
            .replace('{itemName}', targetItem.name)
            .replace('{itemPrice}', itemPrice)
            .replace('{remainingBalance}', remainingBalance));
    }
};
