import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


BOT_TOKEN = os.environ['BOT_TOKEN']
API_URL = "https://tikwm.com/api/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📹 TikTok Video Downloader Bot\nОтправьте ссылку на видео TikTok для скачивания.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **TikTok Video Downloader**

Просто отправьте ссылку на видео TikTok в одном из форматов:
• https://vm.tiktok.com/XYZ123/
• https://www.tiktok.com/@user/video/123456789

⚡ Бот работает даже при блокировке TikTok в РФ
    """
    await update.message.reply_text(help_text)

async def handle_video_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    
    if not any(domain in url for domain in ['tiktok.com', 'vm.tiktok.com']):
        await update.message.reply_text("❌ Пожалуйста, отправьте действительную ссылку на видео TikTok.")
        return

    try:
        processing_msg = await update.message.reply_text("⏳ Скачиваю видео...")
        
        
        params = {"url": url, "hd": 1}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        
        response = requests.post(API_URL, data=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 and data.get("data"):
                video_url = data["data"].get("play")
                if video_url:
                    
                    if video_url.startswith("//"):
                        video_url = "https:" + video_url
                    elif video_url.startswith("/"):
                        video_url = "https://tikwm.com" + video_url
                    
                    caption = f"🎵 {data['data'].get('title', 'TikTok Video')}"
                    
                    
                    await update.message.reply_video(
                        video=video_url,
                        caption=caption,
                        supports_streaming=True
                    )
                    await processing_msg.delete()
                    return
        
        await processing_msg.edit_text("❌ Не удалось скачать видео. Проверьте ссылку.")
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке видео.")

def main():
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_url))
    
   
    logging.info("🤖 Бот запущен на Railway!")
    application.run_polling()

if __name__ == "__main__":
    main()
