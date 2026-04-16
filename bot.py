import telebot
import requests
import yt_dlp

# التوكن بتاعك (تأكد إنه هو اللي شغال)
API_TOKEN = '8622655341:AAHToV_spEtWShH-yV2XNw6M50TzEq2BUOA'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ البوت شغال يا باشا! ابعت رابط فيديو وهحاول أسحبهولك.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    url = message.text
    if "youtube.com" in url or "youtu.be" in url or "tiktok.com" in url:
        bot.reply_to(message, "⏳ جاري المعالجة... انتظر ثواني.")
        try:
            ydl_opts = {'format': 'best', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info['url']
                bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل بنجاح!")
        except Exception as e:
            bot.reply_to(message, "❌ عذراً، يوتيوب حظر السيرفر أو الفيديو ضخم جداً.")

bot.infinity_polling(skip_pending=True)
