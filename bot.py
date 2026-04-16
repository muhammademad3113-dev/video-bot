import telebot
import requests

# التوكن بتاعك
API_TOKEN = '8622655341:AAHToV_spEtWShH-yV2XNw6M50TzEq2BUOA'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ أهلاً بك! ابعت رابط تيك توك أو يوتيوب وهحملهولك فوراً.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    url = message.text
    
    # --- قسم تيك توك (سريع جداً ومضمون) ---
    if "tiktok.com" in url:
        bot.reply_to(message, "⏳ جاري تحميل فيديو تيك توك...")
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            res = requests.get(api_url).json()
            video_link = res['data']['play']
            bot.send_video(message.chat.id, video_link, caption="✅ تم تحميل تيك توك بنجاح!")
        except:
            bot.reply_to(message, "❌ فشل تحميل تيك توك، تأكد من الرابط.")
        return

    # --- قسم يوتيوب (القديم) ---
    if "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "⏳ جاري معالجة رابط يوتيوب...")
        # هنا ممكن يوتيوب يحظر السيرفر زي ما حصل قبل كدة
        bot.reply_to(message, "❌ يوتيوب غالباً حاظر السيرفر ده، جرب تيك توك هيشتغل معاك.")

bot.infinity_polling(skip_pending=True)
