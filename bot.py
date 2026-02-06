import os
import logging
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from youtubesearchpython import VideosSearch

# تحميل متغيرات البيئة
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# الحصول على توكن البوت
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("❌ لم يتم تعيين TELEGRAM_TOKEN في متغيرات البيئة")
    sys.exit(1)

# قاموس لتخزين عمليات البحث لكل مستخدم
user_searches = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة ترحيبية"""
    user = update.effective_user
    welcome_message = (
        f"🎵 **مرحبًا {user.first_name}!**\n\n"
        "أنا بوت للبحث عن الأغاني والمقاطع في اليوتيوب 🎶\n\n"
        "🔍 **كيفية الاستخدام:**\n"
        "اكتب **ناصر** متبوعة باسم الأغنية\n\n"
        "📝 **أمثلة:**\n"
        "• ناصر أغنية حبيبي\n"
        "• ناصر عبدالمجيد عبدالله\n"
        "• ناصر طلعوا الصحاب\n\n"
        "استخدم /help للمساعدة"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة المساعدة"""
    help_text = (
        "🎵 **كيفية استخدام البوت:**\n\n"
        "**الطريقة 1:** اكتب `ناصر` ثم اسم الأغنية\n"
        "مثال: `ناصر أغنية حبيبي`\n\n"
        "**الطريقة 2:** اكتب اسم الأغنية مباشرة\n"
        "مثال: `أغنية حبيبي`\n\n"
        "🎮 **الأوامر المتاحة:**\n"
        "/start - بدء البوت\n"
        "/help - هذه الرسالة\n"
        "/search - بحث مباشر\n\n"
        "🚀 **جرب الآن:** اكتب `ناصر` وأي أغنية تريدها!"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البحث باستخدام الأمر /search"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ الرجاء كتابة اسم الأغنية بعد الأمر /search\n"
            "مثال: `/search أغنية حبيبي`",
            parse_mode='Markdown'
        )
        return
    
    query = ' '.join(context.args)
    await perform_search(update, query)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    message_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # تحضير سجل البحث للمستخدم إذا لم يكن موجود
    if user_id not in user_searches:
        user_searches[user_id] = []
    
    # التحقق مما إذا كانت الرسالة تبدأ بـ "ناصر"
    if message_text.lower().startswith('ناصر'):
        # استخراج اسم الأغنية
        if len(message_text) > 5:
            query = message_text[5:].strip()
        else:
            query = message_text[3:].strip() if len(message_text) > 3 else ""
        
        if not query:
            await update.message.reply_text(
                "🎵 **اكتب اسم الأغنية بعد 'ناصر'**\n\n"
                "مثال:\n"
                "• `ناصر أغنية حبيبي`\n"
                "• `ناصر عبدالمجيد عبدالله`",
                parse_mode='Markdown'
            )
            return
        
        # حفظ البحث في السجل
        user_searches[user_id].append(query)
        if len(user_searches[user_id]) > 10:
            user_searches[user_id].pop(0)
        
        await perform_search(update, query)
    
    # أي نص آخر
    else:
        await update.message.reply_text(
            "🎶 **للبحث عن أغنية:**\n\n"
            "اكتب `ناصر` متبوعة باسم الأغنية\n\n"
            "**مثال:**\n"
            "`ناصر أغنية حبيبي`\n"
            "`ناصر طلعوا الصحاب`\n\n"
            "استخدم /help للمساعدة",
            parse_mode='Markdown'
        )

async def perform_search(update: Update, query: str):
    """تنفيذ البحث وعرض النتائج"""
    try:
        # إعلام المستخدم بالبحث
        search_message = await update.message.reply_text(
            f"🔍 **جاري البحث عن:** `{query}`\n\n⏳ يرجى الانتظار...", 
            parse_mode='Markdown'
        )
        
        # البحث باستخدام youtube-search-python
        videos_search = VideosSearch(query, limit=5)
        results = videos_search.result()
        
        if not results['result']:
            await search_message.edit_text(
                f"❌ **لم أجد نتائج لـ:** `{query}`\n\n"
                "💡 **جرب:**\n"
                "• اسمًا آخر\n"
                "• أضف اسم المطرب\n"
                "• كلمات مختلفة",
                parse_mode='Markdown'
            )
            return
        
        # عرض النتائج
        results_text = f"🎵 **نتائج البحث لـ:** `{query}`\n\n"
        
        keyboard = []
        for i, video in enumerate(results['result'], 1):
            title = video['title']
            duration = video.get('duration', 'غير معروف')
            channel = video['channel']['name']
            video_id = video['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # تقصير العنوان إذا كان طويلاً
            if len(title) > 50:
                title = title[:47] + "..."
            
            results_text += f"**{i}. {title}**\n"
            results_text += f"   ⏱️ {duration} | 📺 {channel}\n"
            results_text += f"   🔗 {video_url}\n\n"
            
        results_text += "💡 **للبحث مجددًا:** اكتب `ناصر` وأسم الأغنية"
        
        await search_message.edit_text(results_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        await update.message.reply_text(
            "❌ **حدث خطأ أثناء البحث**\n\n"
            "💡 **حاول:**\n"
            "1. مرة أخرى بعد قليل\n"
            "2. بحثًا مختلفًا\n",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logger.error(f"حدث خطأ: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ حدث خطأ. الرجاء المحاولة مرة أخرى.",
                parse_mode='Markdown'
            )
        except:
            pass

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    try:
        # إنشاء التطبيق
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # إضافة معالجات الأوامر
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("search", search_command))
        
        # إضافة معالج الرسائل النصية
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # إضافة معالج الأخطاء
        application.add_error_handler(error_handler)
        
        # بدء البوت
        logger.info("🚀 بدء تشغيل بوت تلجرام...")
        logger.info("✅ إصدار python-telegram-bot: 20.7")
        logger.info("🔍 يستخدم youtube-search-python للبحث")
        
        # استخدام Polling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
            
    except Exception as e:
        logger.error(f"❌ فشل تشغيل البوت: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()