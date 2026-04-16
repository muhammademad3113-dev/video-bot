import telebot
import requests
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

# التوكن الخاص بك
API_TOKEN = '8622655341:AAHToV_spEtWShH-yV2XNw6M50TzEq2BUOA'
bot = telebot.TeleBot(API_TOKEN)

# دالة الأزرار
def get_quality_markup(url):
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

@bot.message_handler(func=lambda m: True)
def handle_links(message):
    url = message.text
    if any(x in url for x in ["tiktok.com", "youtube.com", "youtu.be"]):
        bot.reply_to(message, "⚙️ اختر الجودة (يدعم الفيديوهات الطويلة 1h+):", reply_markup=get_quality_markup(url))

@bot.callback_query_handler(func=lambda call: True)
def process_download(call):
    data_parts = call.data.split('|')
    q_code = data_parts[0]
    url = data_parts[1]
    
    quality_map = {
        '10': 'bestvideo[height<=1080]+bestaudio/best',
        '72': 'bestvideo[height<=720]+bestaudio/best',
        '48': 'bestvideo[height<=480]+bestaudio/best',
        'aud': 'bestaudio/best'
    }
    
    bot.edit_message_text("🚀 جاري فحص الرابط ومعالجة الفيديو الطويل...", call.message.chat.id, call.message.message_id)
    
    try:
        # 1. قسم تيك توك
        if "tiktok.com" in url:
            res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
            t_data = res['data']
            if t_data.get('images'):
                bot.send_media_group(call.message.chat.id, [InputMediaPhoto(u) for u in t_data['images'][:10]])
            else:
                link = t_data['music'] if q_code == "aud" else t_data['play']
                if q_code == "aud": bot.send_audio(call.message.chat.id, link)
                else: bot.send_video(call.message.chat.id, link)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return

        # 2. قسم يوتيوب المطور للفيديوهات الطويلة
        ydl_opts = {
            'format': quality_map.get(q_code, 'best'),
            'quiet': True,
            'no_warnings': True,
            'source_address': '0.0.0.0',
            'socket_timeout': 600, # زيادة وقت الانتظار لـ 10 دقائق للفيديوهات الطويلة
            'retries': 10,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info['url']
            title = info.get('title', 'Video')
            duration = info.get('duration', 0)

            # لو الفيديو طويل نبعت رسالة تنبيه
            if duration > 3600:
                bot.send_message(call.message.chat.id, f"⏳ فيديو طويل اكتشفناه ({duration // 3600} ساعة).. جاري السحب.")

            if q_code == "aud":
                bot.send_audio(call.message.chat.id, direct_url, caption=f"✅ {title}\n🎵 تم سحب الصوت بنجاح")
            else:
                bot.send_video(call.message.chat.id, direct_url, caption=f"✅ {title}\n🎬 فيديو طويل جاهز")
        
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ عذراً، الرابط محمي أو الفيديو حجمه ضخم جداً على السيرفر المجاني.", call.message.chat.id, call.message.message_id)

bot.remove_webhook()
bot.infinity_polling(skip_pending=True)
        
