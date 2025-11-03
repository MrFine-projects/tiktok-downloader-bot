import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ['BOT_TOKEN']

class TikTokDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def try_download_api(self, url):
        """Пробуем разные API сервисы"""
        apis = [
            {
                'name': 'TikWM',
                'url': 'https://www.tikwm.com/api/',
                'method': 'post',
                'data': {'url': url},
                'get_video': lambda data: data.get('data', {}).get('play')
            },
            {
                'name': 'TikDown',
                'url': f'https://api.tikdown.org/download?url={url}',
                'method': 'get',
                'get_video': lambda data: data.get('videoUrl')
            },
            {
                'name': 'TikMate',
                'url': 'https://api.tikmate.app/api/lookup',
                'method': 'post',
                'data': {'url': url},
                'get_video': lambda data: f"https://tikmate.app/download/{data.get('token')}/{data.get('id')}.mp4"
            },
            {
                'name': 'SSSTik',
                'url': 'https://ssstik.io/abc?url=dl',
                'method': 'post',
                'data': {'id': url},
                'get_video': lambda data: data.get('links', [{}])[0].get('a') if isinstance(data.get('links'), list) else None
            }
        ]
        
        for api in apis:
            try:
                logger.info(f"Пробуем API: {api['name']}")
                
                if api['method'] == 'post':
                    response = self.session.post(api['url'], data=api['data'], timeout=20)
                else:
                    response = self.session.get(api['url'], timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    video_url = api['get_video'](data)
                    
                    if video_url:
                       
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        elif video_url.startswith('/'):
                            video_url = 'https://tikwm.com' + video_url
                            
                        logger.info(f"Успех с {api['name']}: {video_url}")
                        return video_url
                        
            except Exception as e:
                logger.error(f"Ошибка в {api['name']}: {e}")
                continue
        
        return None
    
    def download_video(self, url):
        """Основной метод загрузки"""
        return self.try_download_api(url)


downloader = TikTokDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📹 TikTok Downloader Bot\nОтправьте ссылку на видео")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 TikTok Video Downloader

Отправьте ссылку в формате:
• https://vm.tiktok.com/XYZ123/
• https://www.tiktok.com/@user/video/123456789

⚡ Используем обходные сервисы
    """
    await update.message.reply_text(help_text)

async def handle_video_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not any(domain in url for domain in ['tiktok.com', 'vm.tiktok.com']):
        await update.message.reply_text("❌ Отправьте ссылку на TikTok")
        return

    try:
        processing_msg = await update.message.reply_text("⏳ Ищу способ скачать видео...")
        
        video_url = downloader.download_video(url)
        
        if video_url:
            await processing_msg.edit_text("📤 Нашел видео, отправляю...")
            
           
            try:
                await update.message.reply_video(
                    video=video_url,
                    caption="🎵 TikTok Video",
                    supports_streaming=True,
                    read_timeout=60,
                    write_timeout=60,
                    connect_timeout=60
                )
                await processing_msg.delete()
                
            except Exception as e:
                logger.error(f"Ошибка отправки: {e}")
                await processing_msg.edit_text("❌ Не удалось отправить видео. Ссылка: " + video_url)
        else:
            await processing_msg.edit_text("❌ Не удалось скачать видео через доступные сервисы")
        
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        await update.message.reply_text("❌ Ошибка обработки")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_url))
    
    logger.info("Бот запущен с обходными API!")
    application.run_polling()

if __name__ == "__main__":
    main()
