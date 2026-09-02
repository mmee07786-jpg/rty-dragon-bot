import json
import os

DB_FILE = "data.json"

def load_data():
    """تحميل البيانات من الملف الخارجي بأمان"""
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    """حفظ البيانات بشكل دائم في الملف الخارجي"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_guild_setting(guild_id, key, default=None):
    """جلب إعداد معين لسيرفر معين (مثل روم الترحيب أو التلفيل)"""
    data = load_data()
    guild_id = str(guild_id)
    if guild_id in data and key in data[guild_id]:
        return data[guild_id][key]
    return default

def set_guild_setting(guild_id, key, value):
    """تعديل أو حفظ إعداد معين لسيرفر معين"""
    data = load_data()
    guild_id = str(guild_id)
    if guild_id not in data:
        data[guild_id] = {}
    data[guild_id][key] = value
    save_data(data)

