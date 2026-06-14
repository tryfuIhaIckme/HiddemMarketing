import compatibility
import os
import logging
import tempfile
import csv
import random
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from collections import defaultdict

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from nlp_preprocessing import preprocess_text, extract_city_entity
from intent_classifier import IntentClassifier
from sentiment_analyzer import analyze_sentiment
from fallback_model import DialogueFallbackModel
from ad_engine import AdScenarioEngine, get_weather_condition, PRODUCTS
from voice_manager import VoiceManager

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Moscow")
CONFIG_PATH = "bot_config.json"

classifier = IntentClassifier(CONFIG_PATH)
classifier.train(preprocess_text)

fallback_model = DialogueFallbackModel("dialogues.txt")
fallback_model.load_dataset(preprocess_text)

ad_engine = AdScenarioEngine()
voice_manager = VoiceManager()

USER_MEMORY = defaultdict(lambda: {
    "last_product": None,
    "last_intent": None,
    "history": [],
    "hist_theme": []
})

def update_context(user_id: int, intent: Optional[str], product_key: Optional[str], user_text: str):
    state = USER_MEMORY[user_id]
    
    if product_key:
        state["last_product"] = product_key
    if intent:
        state["last_intent"] = intent
        
    state["history"].append(user_text)
    if len(state["history"]) > 5:
        state["history"].pop(0)

def log_interaction(user_text: str, intent: str, response: str, sentiment_score: float = 0.0) -> None:
    log_file = "bot_log.csv"
    file_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "User Text", "Intent", "Bot Response", "Sentiment"])
        writer.writerow([
            datetime.now().strftime("%H:%M:%S"),
            user_text,
            intent if intent else "None (Fallback)",
            response.replace("\n", " "),
            sentiment_score
        ])

def classify_intent_with_theme(replica: str, current_themes: list, preprocess_func, classifier) -> Optional[str]:
    # Сначала пытаемся классифицировать стандартным образом
    predicted_intent = classifier.classify(replica, preprocess_func)
    if not predicted_intent:
        return None
        
    intent_data = classifier.config["intents"].get(predicted_intent, {})
    theme_app = intent_data.get("theme_app", None)
    
    # Проверка применимости интента к текущей теме
    if theme_app is None:
        # Интент общего назначения
        return predicted_intent
        
    if "*" in theme_app:
        # Применимо к любой теме
        return predicted_intent
        
    # Проверяем, есть ли текущая активная тема в списке разрешенных для интента
    for theme in current_themes:
        if theme in theme_app:
            return predicted_intent
            
    # Если интент не подходит под текущую тему, игнорируем его предсказание 
    # (или ищем следующий подходящий)
    return None

def process_pipeline(user_text: str, user_id: int) -> tuple[str, Optional[str], float]:
    cleaned_text = preprocess_text(user_text)
    sentiment_score = analyze_sentiment(cleaned_text) if cleaned_text else 0.0
    
    if not cleaned_text:
        return classifier.get_failure_phrase(), None, sentiment_score

    current_themes = USER_MEMORY[user_id]["hist_theme"]
    intent = classify_intent_with_theme(cleaned_text, current_themes, preprocess_text, classifier)
    
    if intent:
        intent_data = classifier.config["intents"].get(intent, {})
        theme_gen = intent_data.get("theme_gen")
        if theme_gen:
            USER_MEMORY[user_id]["hist_theme"].append(theme_gen)
            if len(USER_MEMORY[user_id]["hist_theme"]) > 5:
                USER_MEMORY[user_id]["hist_theme"].pop(0)
    
    prefix = ""
    if sentiment_score <= -0.4:
        prefix = "Мне очень жаль, что вы столкнулись с такой неприятной погодой или настроением. Позвольте предложить немного тепла:\n\n"
    elif sentiment_score >= 0.5:
        prefix = "Рад вашему отличному настроению! Давайте сделаем ваш день еще ярче:\n\n"
    
    if intent:
        if intent == "weather_info":
            user_city = extract_city_entity(user_text)
            target_city = user_city if user_city else DEFAULT_CITY
            weather_data = get_weather_condition(target_city, WEATHER_API_KEY)
            return prefix + f"Сейчас в городе {target_city}: {weather_data['temp']}°C, {weather_data['condition']}.", intent, sentiment_score
            
        base_response = classifier.get_response(intent)
        product_key = ad_engine.get_product_by_intent(intent)
        if product_key:
            ad_message = ad_engine.generate_ad_message(product_key)
            return prefix + f"{base_response}\n\n{ad_message}", intent, sentiment_score
        return prefix + base_response, intent, sentiment_score

    fallback_response = fallback_model.generate_answer(user_text, preprocess_text)
    if fallback_response:
        if random.random() < 0.3:
            user_city = extract_city_entity(user_text)
            target_city = user_city if user_city else DEFAULT_CITY
            weather_data = get_weather_condition(target_city, WEATHER_API_KEY) 
            product_key_weather = ad_engine.get_product_by_weather(weather_data)
            
            if product_key_weather:
                weather_ad = ad_engine.generate_ad_message(product_key_weather)
                transition = f"\n\nКстати, у нас в {target_city} сейчас {weather_data['temp']}°C. "
                return prefix + f"{fallback_response}{transition}{weather_ad}", intent, sentiment_score
        
        return prefix + fallback_response, intent, sentiment_score

    return prefix + classifier.get_failure_phrase(), intent, sentiment_score

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я современный бот магазина «Стиль & Тепло». Чем могу помочь?")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_text = update.message.text
    
    response_text, intent, sentiment_score = process_pipeline(user_text, user_id)
    
    product_key = ad_engine.get_product_by_intent(intent) if intent else None
    
    if intent == "sizes_info" and USER_MEMORY[user_id]["last_product"]:
        last_prod = USER_MEMORY[user_id]["last_product"]
        prod_name = PRODUCTS[last_prod]["name"]
        base_response = f"Для нашей модели **{prod_name}** размерная сетка стандартная (от XS до XXL). Какой размер вам обычно подходит?"
        await update.message.reply_text(base_response)
        
        update_context(user_id, intent, last_prod, user_text)
        log_interaction(user_text, intent, base_response, sentiment_score)
        return

    if intent == "price_info" and USER_MEMORY[user_id]["last_product"]:
        last_prod = USER_MEMORY[user_id]["last_product"]
        prod_name = PRODUCTS[last_prod]["name"]
        base_response = f"Модель **{prod_name}** сейчас доступна по специальной цене. Уточнить наличие вашего размера?"
        await update.message.reply_text(base_response)
        
        update_context(user_id, intent, last_prod, user_text)
        log_interaction(user_text, intent, base_response, sentiment_score)
        return
    
    mentioned_product = None
    for prod_k in PRODUCTS.keys():
        if prod_k in response_text or PRODUCTS[prod_k]["name"] in response_text:
            mentioned_product = prod_k
            break
            
    update_context(user_id, intent, mentioned_product or product_key, user_text)
    
    await update.message.reply_text(response_text)
    log_interaction(user_text, intent, response_text, sentiment_score)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ogg_path = None
    mp3_path = None
    
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg:
            ogg_path = tmp_ogg.name
            await voice_file.download_to_drive(custom_path=ogg_path)
        
        recognized_text = voice_manager.voice_to_text(ogg_path)
        if not recognized_text:
            await update.message.reply_text("Не удалось распознать речь.")
            return

        user_id = update.message.from_user.id
        response_text, intent, sentiment_score = process_pipeline(recognized_text, user_id)
        
        mp3_path = voice_manager.text_to_voice(response_text)
        
        with open(mp3_path, 'rb') as voice_audio:
            await update.message.reply_voice(voice=voice_audio)
            
        log_interaction(f"[Voice] {recognized_text}", intent, response_text, sentiment_score)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Ошибка при обработке голоса.")
    finally:
        if ogg_path and os.path.exists(ogg_path): os.remove(ogg_path)
        if mp3_path and os.path.exists(mp3_path): os.remove(mp3_path)

def main() -> None:
    if not TOKEN:
        print("Set TELEGRAM_TOKEN in .env!")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    application.run_polling()

if __name__ == '__main__':
    main()
