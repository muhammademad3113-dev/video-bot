import telebot
import requests
import yt_dlp
import os
import uuid
import glob
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
            InlineKeyboardButton("🎬 1080p", callback_data=f"10|{key}"),
            InlineKeyboardButton("🎬 720p",  callback_data=f"72|{key}")
        )
        markup.row(
            InlineKeyboardButton("🎬 480p",      callback_data=f"48|{key}"),
            InlineKeyboardButton("🎵 صوت MP3", callback_data=f"aud|{key}")
        )
    return markup

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

def download_with_ytdlp(url, q_code):
    quality_map = {
        '10':  'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '72':  'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '48':  'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'vid': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'aud': 'bestaudio/best'
    }
    filename = f"/tmp/{uuid.uuid4()}"
    ydl_opts = {
        'format': quality_map.get(q_code, 'best'),
        'outtmpl': filename + '.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'http_headers': {'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12) gzip'},
    }
    if q_code == "aud":
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'فيديو')
    files = glob.glob(filename + '.*')
    if not files:
        raise Exception("الملف مش موجود بعد التحميل")
    return files[0], title

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

        bot.edit_message_text("⬇️ جاري التحميل...", call.message.chat.id, call.message.message_id)

        filepath, title = download_with_ytdlp(url, q_code)
        file_size = os.path.getsize(filepath)

        if file_size > 50 * 1024 * 1024 and q_code not in ['aud', '48']:
            os.remove(filepath)
            bot.edit_message_text("⬇️ الحجم كبير، بحاول جودة أقل...", call.message.chat.id, call.message.message_id)
            filepath, title = download_with_ytdlp(url, '48')
            file_size = os.path.getsize(filepath)

        if file_size > 50 * 1024 * 1024:
            os.remove(filepath)
            bot.edit_message_text(
                "❌ الفيديو أكبر من 50MB.\nجرب: 🎵 صوت MP3 بدل الفيديو.",
                call.message.chat.id, call.message.message_id
            )
            return

        bot.edit_message_text("📤 جاري الرفع على تيليجرام...", call.message.chat.id, call.message.message_id)

        with open(filepath, 'rb') as f:
            if q_code == "aud":
                bot.send_audio(call.message.chat.id, f, caption=f"🎵 {title}")
            else:
                bot.send_video(call.message.chat.id, f, caption=f"🎬 {title}", supports_streaming=True)

        os.remove(filepath)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        err = str(e)
        if "Sign in" in err or "age" in err.lower():
            msg = "❌ الفيديو محمي أو يحتاج تسجيل دخول."
        elif "private" in err.lower():
            msg = "❌ الفيديو خاص ومش متاح."
        elif "blocked" in err.lower() or "429" in err:
            msg = "❌ السيرفر محجوب مؤقتاً. جرب جودة أقل."
        else:
            msg = "❌ فشل التحميل، جرب مرة تانية."
        try:
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id)
        except:
            pass

bot.infinity_polling(skip_pending=True)
