const { SlashCommandBuilder, PermissionFlagsBits, EmbedBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const fs = require('fs');
const path = require('path');

const BANNER_URL = "https://cdn.discordapp.com/attachments/1534625592287297789/1545811316474912808/file_00000000c75881f4b2f0ec4b8cdff737-1.png?ex=6a9d8079&is=6a9c2ef9&hm=e9dfe9091e4710e406bd1dbe59c88706418390be9f939991090721b416f27b5f&";
const CONFIG_FILE = path.join(__dirname, '../clan_config.json');
const DATA_FILE = path.join(__dirname, '../raid_data.json');

function loadConfig() {
    if (fs.existsSync(CONFIG_FILE)) {
        try {
            return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
        } catch (e) {
            return { clan_name: "VLX", embed_color: 0x8B0000 };
        }
    }
    return { clan_name: "VLX", embed_color: 0x8B0000 };
}

function saveConfig(config) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 4), 'utf8');
}

function loadRaidData() {
    if (fs.existsSync(DATA_FILE)) {
        try {
            const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
            const gid = Object.keys(data)[0]; // دعم الهيكل المتعدد أو المباشر
            if (gid && data[gid] && typeof data[gid] === 'object' && data[gid].raider_stats) {
                return data[gid];
            }
            return data.raider_stats ? data : { raider_stats: {}, win_streak: 0 };
        } catch (e) {
            return { raider_stats: {}, win_streak: 0 };
        }
    }
    return { raider_stats: {}, win_streak: 0 };
}

class RaidStartModal extends ModalBuilder {
    constructor() {
        super();
        this.setTitle("⚔️ | Raid Start & Announcement").setCustomId("raid_start_modal");

        const serverLink = new TextInputBuilder().setCustomId("server_link").setLabel("Server Link").setStyle(TextInputStyle.Short).setRequired(true);
        const difficulty = new TextInputBuilder().setCustomId("difficulty").setLabel("Difficulty").setStyle(TextInputStyle.Short).setRequired(true);
        const targets = new TextInputBuilder().setCustomId("targets").setLabel("Targets / Matchup").setStyle(TextInputStyle.Short).setRequired(true).setValue("");
        const counts = new TextInputBuilder().setCustomId("counts").setLabel("Our Count & Their Count").setStyle(TextInputStyle.Short).setRequired(true).setValue("");
        const region = new TextInputBuilder().setCustomId("region").setLabel("Region").setStyle(TextInputStyle.Short).setRequired(true).setValue("");

        this.addComponents(
            new ActionRowBuilder().addComponents(serverLink),
            new ActionRowBuilder().addComponents(difficulty),
            new ActionRowBuilder().addComponents(targets),
            new ActionRowBuilder().addComponents(counts),
            new ActionRowBuilder().addComponents(region)
        );
    }
}

module.exports = {
    async handleRaidStartModalSubmit(interaction, serverLink, difficulty, targets, counts, region) {
        await interaction.deferReply({ ephemeral: true });

        const config = loadConfig();
        const clan = config.clan_name || "VLX";
        const embedColor = config.embed_color || 0x8B0000;

        const embed = new EmbedBuilder()
            .setTitle(`⚔️ **${clan} Clan Raid Notification** ⚔️`)
            .setColor(embedColor)
            .addFields(
                { name: "⚔️ Difficulty", value: `\`${difficulty}\``, inline: false },
                { name: "🎯 Targets", value: `\`${targets}\``, inline: false },
                { name: "🔢 Our Count & Their Count", value: `\`${counts}\``, inline: false },
                { name: "📡 Region", value: `🌍 \`${region}\``, inline: false },
                { 
                    name: "📜 Instructions", 
                    value: "→ Click **Join** below to enter the server\n→ Click **Leaderboard** to check top active raiders\n→ Follow callouts from raid leadership\n→ Stay until the raid is concluded", 
                    inline: false 
                }
            );

        if (BANNER_URL) {
            embed.setImage(BANNER_URL);
        }

        embed.setFooter({ text: `Raid Initiated by ${interaction.user.tag} | ${clan} Clan` });

        const row = new ActionRowBuilder().addComponents(
            new ButtonBuilder().setLabel("Join").setStyle(ButtonStyle.Link).setURL(serverLink).setEmoji("🎮"),
            new ButtonBuilder().setCustomId("show_leaderboard").setLabel("Leaderboard").setStyle(ButtonStyle.Secondary).setEmoji("🏆")
        );

        await interaction.channel.send({ content: "@here 🔔 **New Raid Notification:**", embeds: [embed], components: [row] });
        await interaction.deleteReply().catch(() => {});
    },

    raidStartCommand: new SlashCommandBuilder()
        .setName('raid-start')
        .setDescription('[ Admin Only ] Start a raid with announcement')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    nameClanCommand: new SlashCommandBuilder()
        .setName('name_clan')
        .setDescription('[ Admin Only ] تعيين اسم الكلان الظهور بإعلانات الرايد')
        .addStringOption(o => o.setName('name').setDescription('اكتب اسم الكلان الجديد').setRequired(false))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    colorEmedCommand: new SlashCommandBuilder()
        .setName('color_emed')
        .setDescription('[ Admin Only ] تغيير لون شريط إعلان الرايد')
        .addStringOption(o => o.setName('hex_code').setDescription('اكتب كود اللون (مثل #FF0000)').setRequired(true))
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),

    async handleRaidStart(interaction) {
        await interaction.showModal(new RaidStartModal());
    },

    async handleNameClan(interaction) {
        const name = interaction.options.getString('name') || "VLX";
        const config = loadConfig();
        config.clan_name = name;
        saveConfig(config);
        await interaction.reply({ content: `✅ | تم تحديث اسم الكلان بنجاح إلى: **${name}**`, ephemeral: true });
    },

    async handleColorEmed(interaction) {
        const hexCode = interaction.options.getString('hex_code').trim();
        const cleanedCode = hexCode.startsWith("#") ? hexCode.substring(1) : hexCode;

        let colorInt;
        try {
            colorInt = parseInt(cleanedCode, 16);
            if (isNaN(colorInt)) throw new Error();
        } catch (e) {
            await interaction.reply({ content: "❌ | كود اللون غير صحيح! استخدم صيغة صحيحة مثل `#FF0000`.", ephemeral: true });
            return;
        }

        const config = loadConfig();
        config.embed_color = colorInt;
        saveConfig(config);
        await interaction.reply({ content: `✅ | تم تحديث لون إعلان الرايد بنجاح إلى \`#${cleanedCode}\``, ephemeral: true });
    },

    async handleButtonInteraction(interaction) {
        if (interaction.customId === "show_leaderboard") {
            const data = loadRaidData();
            const stats = data.raider_stats || {};

            if (Object.keys(stats).length === 0) {
                await interaction.reply({ content: "❌ | No raid statistics recorded yet!", ephemeral: true });
                return;
            }

            const sortedRaiders = Object.entries(stats).sort((a, b) => b[1] - a[1]).slice(0, 10);

            let description = "";
            for (let i = 0; i < sortedRaiders.length; i++) {
                const [uid, count] = sortedRaiders[i];
                const index = i + 1;
                const member = await interaction.guild.members.fetch(uid).catch(() => null);
                const name = member ? member.toString() : `<@${uid}>`;
                const medal = index === 1 ? "🥇" : index === 2 ? "🥈" : index === 3 ? "🥉" : `#${index}`;
                description += `${medal} ${name} ──> **${count}** Raids\n`;
            }

            const config = loadConfig();
            const lbEmbed = new EmbedBuilder()
                .setTitle("🏆 | Clan Top Raiders (Leaderboard)")
                .setDescription(description)
                .setColor(config.embed_color || 0x8B0000)
                .setFooter({ text: "Clan Statistics" });

            await interaction.reply({ embeds: [lbEmbed], ephemeral: true });
        }
    }
};
