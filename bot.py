import telebot
import requests
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

# التوكن بتاعك
API_TOKEN = '8622655341:AAHToV_spEtWShH-yV2XNw6M50TzEq2BUOA'
bot = telebot.TeleBot(API_TOKEN)

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
    bot.reply_to(message, "✅ البوت شغال يا وحش! ابعت رابط تيك توك (فيديو أو صور) أو يوتيوب.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    url = message.text
    if "tiktok.com" in url or "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "⚙️ اختار الجودة أو نوع التحميل:", reply_markup=get_markup(url))

@bot.callback_query_handler(func=lambda call: True)
def download(call):
    data = call.data.split('|')
    q_code, url = data[0], data[1]
    bot.edit_message_text("🚀 جاري الفحص والسحب...", call.message.chat.id, call.message.message_id)
    
    try:
        # --- قسم تيك توك (يدعم الصور والفيديو) ---
        if "tiktok.com" in url:
            res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
            t_data = res['data']
            
            # لو الرابط فيه صور (Slideshow)
            if t_data.get('images'):
                bot.edit_message_text("📸 تم اكتشاف ألبوم صور، جاري الرفع...", call.message.chat.id, call.message.message_id)
                photos = [InputMediaPhoto(img) for img in t_data['images'][:10]] # بيبعت أول 10 صور
                bot.send_media_group(call.message.chat.id, photos)
                bot.delete_message(call.message.chat.id, call.message.message_id)
                return

            # لو فيديو عادي أو صوت
            link = t_data['music'] if q_code == "aud" else t_data['play']
            if q_code == "aud": 
                bot.send_audio(call.message.chat.id, link, caption="🎵 صوت التيك توك")
            else: 
                bot.send_video(call.message.chat.id, link, caption="🎬 فيديو تيك توك")
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return

        # --- قسم يوتيوب ---
        quality_map = {'10': 'bestvideo[height<=1080]+bestaudio/best', '72': 'bestvideo[height<=720]+bestaudio/best', '48': 'bestvideo[height<=480]+bestaudio/best', 'aud': 'bestaudio/best'}
        ydl_opts = {'format': quality_map.get(q_code, 'best'), 'quiet': True, 'no_warnings': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if q_code == "aud":
                bot.send_audio(call.message.chat.id, info['url'], caption=f"🎵 {info['title']}")
            else:
                bot.send_video(call.message.chat.id, info['url'], caption=f"🎬 {info['title']}")
        
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text("❌ فشل السحب. تأكد من الرابط أو جرب جودة تانية.", call.message.chat.id, call.message.message_id)

bot.infinity_polling(skip_pending=True)
    
