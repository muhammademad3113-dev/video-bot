import telebot
import yt_dlp
import requests

# التوكن الخاص بك
API_TOKEN = '8622655341:AAHToV_spEtWShH-yV2XNw6M50TzEq2BUOA'
bot = telebot.TeleBot(API_TOKEN)

def get_quality_markup(url):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🎬 720p", callback_data=f"72|{url}"),
        telebot.types.InlineKeyboardButton("🎬 480p", callback_data=f"48|{url}")
    )
    markup.row(telebot.types.InlineKeyboardButton("🎵 MP3 (صوت)", callback_data=f"aud|{url}"))
    return markup

@bot.message_handler(func=lambda m: True)
def handle_links(message):
    url = message.text
    if "youtube.com" in url or "youtu.be" in url or "tiktok.com" in url:
        bot.reply_to(message, "⚙️ جاري فحص الرابط (يدعم فيديوهات +1h):", reply_markup=get_quality_markup(url))

@bot.callback_query_handler(func=lambda call: True)
def process_download(call):
    data_parts = call.data.split('|')
    q_code, url = data_parts[0], data_parts[1]
    
    # محاولة حل مشكلة الحماية باستخدام متصفح وهمي
    ydl_opts = {
        'format': 'best' if q_code != 'aud' else 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
    }
    
    bot.edit_message_text("⏳ جاري استخراج الرابط المباشر... انتظر قليلًا", call.message.chat.id, call.message.message_id)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info['url']
            title = info.get('title', 'Video')
            
            if q_code == "aud":
                bot.send_audio(call.message.chat.id, direct_url, caption=f"✅ {title}")
            else:
                bot.send_video(call.message.chat.id, direct_url, caption=f"✅ {title}")
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.edit_message_text("❌ اليوتيوب حظر السيرفر مؤقتاً. جرب رابط آخر أو جرب التحميل كصوت MP3.", call.message.chat.id, call.message.message_id)

bot.infinity_polling()
