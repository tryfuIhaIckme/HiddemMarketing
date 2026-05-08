import compatibility
import os
import logging
import tempfile
import csv
import random
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Современные асинхронные импорты python-telegram-bot v20+
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Наши модули
from nlp_preprocessing import preprocess_text
from intent_classifier import IntentClassifier
from fallback_model import DialogueFallbackModel
from ad_engine import AdScenarioEngine, get_weather_condition
from voice_manager import VoiceManager

# ... (logging setup unchanged)

load_dotenv()

# --- Инициализация ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Moscow")
CONFIG_PATH = "bot_config.json"

# Модели
classifier = IntentClassifier(CONFIG_PATH)
classifier.train(preprocess_text)

fallback_model = DialogueFallbackModel("dialogues.txt")
fallback_model.load_dataset(preprocess_text)

ad_engine = AdScenarioEngine()
voice_manager = VoiceManager()

def log_interaction(user_text: str, intent: str, response: str) -> None:
    """Логирование в CSV."""
    log_file = "bot_log.csv"
    file_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "User Text", "Intent", "Bot Response"])
        writer.writerow([
            datetime.now().strftime("%H:%M:%S"),
            user_text,
            intent if intent else "None (Fallback)",
            response.replace("\n", " ")
        ])

def process_pipeline(user_text: str) -> str:
    """Основная бизнес-логика (Конвейер)."""
    cleaned_text = preprocess_text(user_text)
    if not cleaned_text:
        return classifier.get_failure_phrase()

    intent = classifier.classify(cleaned_text, preprocess_text)
    
    # 1. СЦЕНАРИЙ А: Реклама по интенту (как было)
    if intent:
        base_response = classifier.get_response(intent)
        product_key = ad_engine.get_product_by_intent(intent)
        if product_key:
            ad_message = ad_engine.generate_ad_message(product_key)
            return f"{base_response}\n\n{ad_message}"
        return base_response

    # 2. СЦЕНАРИЙ Б: Fallback-ответ (Болталка)
    fallback_response = fallback_model.generate_answer(user_text, preprocess_text)
    if fallback_response:
        # --- НОВАЯ ФИЧА: Реклама по реальной погоде (API) ---
        # Чтобы не спамить погодой каждый раз, сделаем шанс срабатывания, например, 30%
        if random.random() < 0.3:
            # Делаем запрос к API
            weather_data = get_weather_condition(DEFAULT_CITY, WEATHER_API_KEY) 
            product_key_weather = ad_engine.get_product_by_weather(weather_data)
            
            if product_key_weather:
                weather_ad = ad_engine.generate_ad_message(product_key_weather)
                # Добавляем переходную фразу
                transition = f"\n\nКстати, у нас в {DEFAULT_CITY} сейчас {weather_data['temp']}°C. "
                return f"{fallback_response}{transition}{weather_ad}"
        
        return fallback_response

    # 3. Если ничего не подошло
    return classifier.get_failure_phrase()

# --- Асинхронные хэндлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start."""
    await update.message.reply_text("Привет! Я современный бот магазина «Стиль & Тепло». Чем могу помочь?")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текста."""
    user_text = update.message.text
    
    # Определяем интент для лога
    cleaned_text = preprocess_text(user_text)
    intent = classifier.classify(cleaned_text, preprocess_text)
    
    response_text = process_pipeline(user_text)
    await update.message.reply_text(response_text)
    
    log_interaction(user_text, intent, response_text)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка голоса."""
    ogg_path = None
    mp3_path = None
    
    try:
        # Скачивание
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg:
            ogg_path = tmp_ogg.name
            await voice_file.download_to_drive(custom_path=ogg_path)
        
        # STT
        recognized_text = voice_manager.voice_to_text(ogg_path)
        if not recognized_text:
            await update.message.reply_text("Не удалось распознать речь.")
            return

        # Интент для лога
        cleaned_text = preprocess_text(recognized_text)
        intent = classifier.classify(cleaned_text, preprocess_text)
        
        response_text = process_pipeline(recognized_text)
        
        # TTS
        mp3_path = voice_manager.text_to_voice(response_text)
        
        with open(mp3_path, 'rb') as voice_audio:
            await update.message.reply_voice(voice=voice_audio)
            
        log_interaction(f"[Voice] {recognized_text}", intent, response_text)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Ошибка при обработке голоса.")
    finally:
        if ogg_path and os.path.exists(ogg_path): os.remove(ogg_path)
        if mp3_path and os.path.exists(mp3_path): os.remove(mp3_path)

def main() -> None:
    """Запуск приложения."""
    if not TOKEN:
        print("Set TELEGRAM_TOKEN in .env!")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("--- Бот запущен (v20+) ---")
    application.run_polling()

if __name__ == '__main__':
    main()
