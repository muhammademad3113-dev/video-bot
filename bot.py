import telebot
import requests
import os
import uuid
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

url_store = {}

def store_url(url):
    key = str(uuid.uuid4())[:8]
    url_store[key] = url
    return key

def is_tiktok(url):
    return "tiktok.com" in url or "vm.tiktok.com" in url

def is_supported(url):
    return any(x in url for x in [
        "tiktok.com", "vm.tiktok.com",
        "youtube.com", "youtu.be",
        "facebook.com", "fb.watch",
        "instagram.com"
    ])

def get_markup(url):
    key = store_url(url)
    markup = InlineKeyboardMarkup()
    if is_tiktok(url):
        markup.row(
            InlineKeyboardButton("🎬 فيديو", callback_data=f"vid|{key}"),
            InlineKeyboardButton("🎵 صوت MP3", callback_data=f"aud|{key}")
        )
    else:
        markup.row(
            InlineKeyboardButton("🎬 720p", callback_data=f"vid|{key}"),
            InlineKeyboardButton("🎵 صوت MP3", callback_data=f"aud|{key}")
        )
    return markup

def get_loader(url, audio_only=False):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}

    # الخطوة 1: نبعت الرابط
    res = session.post(
        'https://loader.to/ajax/download.php',
        data={
            'url': url,
            'format': 'mp3' if audio_only else 'mp4',
        },
        headers=headers,
        timeout=30
    ).json()

    token = res.get('id')
    if not token:
        raise Exception("فشل الحصول على token")

    # الخطوة 2: ننتظر جهوز الرابط
    for _ in range(20):
        time.sleep(3)
        check = session.get(
            f'https://loader.to/ajax/progress.php?id={token}',
            headers=headers,
            timeout=15
        ).json()

        if check.get('success') == 1:
            download_url = check.get('download_url')
            if download_url:
                return download_url
        if check.get('success') == -1:
            raise Exception("فشل التحميل من loader")

    raise Exception("انتهى الوقت")

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message,
        "✅ أهلاً! أنا بوت التحميل 🎬\n\n"
        "ابعتلي رابط من:\n"
        "🎵 تيك توك\n"
        "▶️ يوتيوب\n"
        "📘 فيسبوك\n"
        "📸 انستغرام"
    )

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    url = message.text.strip()
    if is_supported(url):
        bot.reply_to(message, "⚙️ اختار نوع التحميل:", reply_markup=get_markup(url))
    else:
        bot.reply_to(message, "❌ ابعت رابط صحيح من تيك توك أو يوتيوب أو فيسبوك أو انستغرام.")

@bot.callback_query_handler(func=lambda call: True)
def handle_download(call):
    parts = call.data.split('|', 1)
    q_code, key = parts[0], parts[1]
    url = url_store.get(key)

    if not url:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الرابط، ابعته تاني.")
        return

    bot.edit_message_text("🔍 جاري الفحص...", call.message.chat.id, call.message.message_id)

    try:
        # ==================== تيك توك ====================
        if is_tiktok(url):
            res = requests.get(
                f"https://www.tikwm.com/api/?url={url}",
                timeout=20
            ).json()

            if res.get('code') != 0:
                raise Exception("فشل الـ API")

            t_data = res['data']

            if t_data.get('images'):
                bot.edit_message_text("📸 ألبوم صور، جاري الرفع...", call.message.chat.id, call.message.message_id)
                photos = [InputMediaPhoto(img) for img in t_data['images'][:10]]
                bot.send_media_group(call.message.chat.id, photos)
                bot.delete_message(call.message.chat.id, call.message.message_id)
                return

            if q_code == "aud":
                link = t_data.get('music')
                if link:
                    bot.send_audio(call.message.chat.id, link, caption="🎵 صوت التيك توك")
            else:
                link = t_data.get('hdplay') or t_data.get('play')
                if link:
                    bot.send_video(call.message.chat.id, link, caption="🎬 فيديو تيك توك", supports_streaming=True)

            bot.delete_message(call.message.chat.id, call.message.message_id)
            return

        # ==================== يوتيوب / فيسبوك / انستغرام ====================
        bot.edit_message_text("⏳ جاري التجهيز (ممكن يأخد دقيقة)...", call.message.chat.id, call.message.message_id)

        audio_only = q_code == "aud"
        link = get_loader(url, audio_only)

        bot.edit_message_text("📤 جاري الرفع...", call.message.chat.id, call.message.message_id)

        if audio_only:
            bot.send_audio(call.message.chat.id, link, caption="🎵 الصوت")
        else:
            bot.send_video(call.message.chat.id, link, caption="🎬 الفيديو", supports_streaming=True)

        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        try:
            bot.edit_message_text("❌ فشل التحميل، جرب رابط تاني.", call.message.chat.id, call.message.message_id)
        except:
            pass

bot.infinity_polling(skip_pending=True)
