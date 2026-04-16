Import telebot
import requests
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

# التوكن الخاص بك
API_TOKEN = '8622655341:AAHToV_spEtWShH-yV2XNw6M50TzEq2BUOA'
bot = telebot.TeleBot(API_TOKEN)

# دالة الأزرار (استخدام رموز قصيرة لتجنب خطأ تليجرام)
def get_quality_markup(url):
    markup = InlineKeyboardMarkup()
    # الصف الأول: جودات عالية
    markup.row(
        InlineKeyboardButton("🎬 1080p", callback_data=f"10|{url}"),
        InlineKeyboardButton("🎬 720p", callback_data=f"72|{url}")
    )
    # الصف الثاني: جودة متوسطة وصوت
    markup.row(
        InlineKeyboardButton("🎬 480p", callback_data=f"48|{url}"),
        InlineKeyboardButton("🎵 MP3 (صوت)", callback_data=f"aud|{url}")
    )
    return markup

@bot.message_handler(func=lambda m: True)
def handle_links(message):
    url = message.text
    # التأكد من أن الرابط يوتيوب أو تيك توك
    if any(x in url for x in ["tiktok.com", "youtu.be", "youtube.com"]):
        bot.reply_to(message, "⚙️ اختر الجودة المطلوبة (سحب سريع):", reply_markup=get_quality_markup(url))

@bot.callback_query_handler(func=lambda call: True)
def process_download(call):
    data_parts = call.data.split('|')
    q_code = data_parts[0]
    url = data_parts[1]
    
    # خريطة الجودات للمحرك الأول
    quality_map = {
        '10': 'bestvideo[height<=1080]+bestaudio/best',
        '72': 'bestvideo[height<=720]+bestaudio/best',
        '48': 'bestvideo[height<=480]+bestaudio/best',
        'aud': 'bestaudio/best'
    }
    
    bot.edit_message_text("🚀 جاري سحب الرابط المباشر بالجودة المختارة...", call.message.chat.id, call.message.message_id)
    
    try:
        # 1. قسم تيك توك (صور وفيديو سريع)
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

        # 2. قسم يوتيوب (محرك السحب المباشر السريع)
        ydl_opts = {
            'format': quality_map.get(q_code, 'best'),
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info['url']
            
            if q_code == "aud":
                bot.send_audio(call.message.chat.id, direct_url, caption="✅ تم سحب الصوت")
            else:
                bot.send_video(call.message.chat.id, direct_url, caption=f"✅ جودة {info.get('height', q_code)}p جاهزة")
        
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception:
        bot.edit_message_text("❌ عذراً، هذه الجودة غير متاحة لهذا الفيديو أو الرابط محمي.", call.message.chat.id, call.message.message_id)

bot.remove_webhook()
print("📡 البوت شغال الآن بأزرار الجودات وأقصى سرعة...")
bot.infinity_polling(skip_pending=True)
