import telebot
import requests
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# التوكن الخاص بك
API_TOKEN = '8622655341:AAHToV_spEtWShH-yV2XNw6M50TzEq2BUOA'
bot = telebot.TeleBot(API_TOKEN)

# دالة أزرار الجودة والصوت
def get_markup(url):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎬 1080p", callback_data=f"10|{url}"),
        InlineKeyboardButton("🎬 720p", callback_data=f"72|{url}")
    )
    markup.row(
        InlineKeyboardButton("🎬 480p", callback_data=f"48|{url}"),
        InlineKeyboardButton("🎵 MP3 (صوت)", callback_data=f"aud|{url}")
    )
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "✅ البوت شغال يا وحش! ابعت الرابط واختار الجودة اللي تريحك.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    url = message.text
    if "tiktok.com" in url or "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "⚙️ اختار الجودة أو الصوت:", reply_markup=get_markup(url))

@bot.callback_query_handler(func=lambda call: True)
def download(call):
    data = call.data.split('|')
    q_code, url = data[0], data[1]
    
    bot.edit_message_text("🚀 جاري السحب والتجهيز... انتظر ثواني", call.message.chat.id, call.message.message_id)
    
    try:
        # --- لو الرابط تيك توك (سريع ومضمون) ---
        if "tiktok.com" in url:
            res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
            link = res['data']['music'] if q_code == "aud" else res['data']['play']
            if q_code == "aud": bot.send_audio(call.message.chat.id, link, caption="🎵 تيك توك صوت")
            else: bot.send_video(call.message.chat.id, link, caption="🎬 تيك توك فيديو")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return

        # --- لو الرابط يوتيوب (جودات وصوت) ---
        quality_map = {
            '10': 'bestvideo[height<=1080]+bestaudio/best',
            '72': 'bestvideo[height<=720]+bestaudio/best',
            '48': 'bestvideo[height<=480]+bestaudio/best',
            'aud': 'bestaudio/best'
        }
        
        ydl_opts = {
            'format': quality_map.get(q_code, 'best'),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 600
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if q_code == "aud":
                bot.send_audio(call.message.chat.id, info['url'], caption=f"🎵 {info['title']}")
            else:
                bot.send_video(call.message.chat.id, info['url'], caption=f"🎬 {info['title']}")
        
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text("❌ فشل السحب. غالباً يوتيوب حاظر السيرفر أو الرابط غلط.", call.message.chat.id, call.message.message_id)

bot.infinity_polling(skip_pending=True)
