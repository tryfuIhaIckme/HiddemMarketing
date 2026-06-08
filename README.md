# Telegram Bot for "Style & Warmth" Store 

Умный Telegram-бот для магазина одежды с поддержкой голосовых сообщений, распознаванием намерений, генерацией нативной рекламы и админ-панелью.

## Что умеет бот?

- **Обработка текста и голоса**: понимает текстовые и голосовые сообщения (STT/TTS через Google API).
- **Классификация намерений (Intent Classification)**: определяет, что хочет пользователь (ищет куртку на зиму, ветровку от дождя или строгий тренч), используя NLP и ML.
- **Болталка (Fallback Model)**: поддерживает простой диалог с помощью собственной базы ответов.
- **Нативная реклама**: рекомендует товары на основе:
  - Интента пользователя.
  - Текущей погоды (подключается к OpenWeather API).
- **Админ-панель**: веб-интерфейс на Flask для отслеживания логов диалогов и статистики (NLU rate, популярные интенты).

## Стек технологий

- Python 3.10+
- `python-telegram-bot` (v20+)
- NLP и ML: `natasha`, `nltk`, `scikit-learn`
- Голос: `SpeechRecognition`, `gTTS`, `pydub`
- Веб: `Flask`

## Установка и запуск

1. Склонируйте репозиторий и перейдите в папку:
   ```bash
   git clone https://github.com/your-username/hidden-marketing-bot.git
   cd hidden-marketing-bot
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
   *Убедитесь, что в системе установлен `ffmpeg` (нужен для pydub).*

3. Создайте файл `.env` на основе `.env.example` и укажите токены:
   ```env
   TELEGRAM_TOKEN=ваш_токен_от_botfather
   WEATHER_API_KEY=ваш_ключ_openweathermap
   DEFAULT_CITY=Moscow
   ```

4. Запустите бота:
   ```bash
   python main.py
   ```

5. Для запуска админ-панели (в отдельном окне):
   ```bash
   python admin_app.py
   ```

## Архитектура

- `main.py` — запуск приложения и пайплайн обработки сообщений.
- `bot_config.json` — конфигурация намерений (intents).
- `nlp_preprocessing.py` — предобработка и лемматизация (natasha).
- `intent_classifier.py` — модель классификации интентов.
- `fallback_model.py` — поиск ответов-заглушек (dialogues.txt).
- `ad_engine.py` — логика подбора рекомендаций (товаров) по интенту/погоде.
- `voice_manager.py` — обертки для STT и TTS.
- `admin_app.py` — дашборд.
