const { MongoClient } = require('mongodb');

// استخدام نفس رابط الاتصال بقاعدة البيانات الخاص بك
const MONGO_URI = "mongodb+srv://esramer2009_db_user:@cluster0.fkw1q0y.mongodb.net/?appName=Cluster0";

const client = new MongoClient(MONGO_URI);
let db, settings_collection, economy_collection;

async function connectDB() {
    if (!db) {
        await client.connect();
        db = client.db("discord_bot_db");
        settings_collection = db.collection("guild_settings");
        economy_collection = db.collection("economy_data");
    }
}

async function get_guild_setting(guild_id, key, default_value = null) {
    await connectDB();
    guild_id = String(guild_id);
    const doc = await settings_collection.findOne({ guild_id: guild_id });
    if (doc && key in doc) {
        return doc[key];
    }
    return default_value;
}

async function set_guild_setting(guild_id, key, value) {
    await connectDB();
    guild_id = String(guild_id);
    await settings_collection.updateOne(
        { guild_id: guild_id },
        { $set: { [key]: value } },
        { upsert: true }
    );
}

async function load_data() {
    await connectDB();
    const doc = await economy_collection.findOne({ _id: "global_economy" });
    if (!doc) {
        return { balances: {}, shops: {} };
    }
    return {
        balances: doc.balances || {},
        shops: doc.shops || {}
    };
}

async function save_data(data) {
    await connectDB();
    await economy_collection.updateOne(
        { _id: "global_economy" },
        {
            $set: {
                balances: data.balances || {},
                shops: data.shops || {}
            }
        },
        { upsert: true }
    );
}

module.exports = {
    get_guild_setting,
    set_guild_setting,
    load_data,
    save_data
};
