import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
BOT_TOKEN = "YOUR TOKEN"
API_URL = "https://tikwm.com/api/"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте ссылку на видео TikTok для скачивания.")
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📹 **TikTok Video Downloader Bot**

Просто отправьте мне ссылку на видео из TikTok, и я скачаю его для вас!

🔗 **Примеры поддерживаемых ссылок:**
- https://vm.tiktok.com/XYZ123/
- https://www.tiktok.com/@username/video/123456789
- https://tiktok.com/@username/video/123456789

⚡ **Бот работает даже при блокировке TikTok в РФ**
    """
    await update.message.reply_text(help_text)
async def handle_video_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not any(domain in url for domain in ['tiktok.com', 'vm.tiktok.com']):
        await update.message.reply_text("❌ Пожалуйста, отправьте действительную ссылку на видео TikTok.")
        return

    try:
        processing_msg = await update.message.reply_text("⏳ Скачиваю видео...")
        params = {
            "url": url,
            "count": 12,
            "cursor": 0,
            "web": 1,
            "hd": 1
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.post(API_URL, data=params, headers=headers, timeout=30)

        if response.status_code != 200:
            await processing_msg.edit_text("❌ Ошибка при подключении к сервису. Попробуйте позже.")
            return

        data = response.json()

        if data.get("code") == 0 and data.get("data"):
            video_data = data["data"]
            video_url = video_data.get("play")

            if video_url:
                if video_url.startswith("//"):
                    video_url = "https:" + video_url
                elif video_url.startswith("/"):
                    video_url = "https://tikwm.com" + video_url

                await processing_msg.edit_text("📤 Отправляю видео...")


                caption = f"🎵 {video_data.get('title', 'Без описания')}"
                await update.message.reply_video(
                    video=video_url,
                    caption=caption,
                    supports_streaming=True
                )
                await processing_msg.delete()

            else:
                await processing_msg.edit_text("❌ Не удалось получить ссылку на видео.")
        else:
            await processing_msg.edit_text("❌ Видео не найдено или ссылка неверна.")

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ Таймаут запроса. Попробуйте позже.")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text("🔌 Ошибка сети. Попробуйте позже.")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")



async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Я понимаю только ссылки на TikTok. Используйте /help для справки.")



def main():

    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), handle_video_url))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_url))
    app.add_handler(MessageHandler(filters.ALL, unknown_message))


    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
