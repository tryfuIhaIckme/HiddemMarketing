import random
import requests
from typing import Optional, Dict, List, Any

# База товаров с шаблонами нативной рекламы (Native Advertising)
PRODUCTS = {
    "parka": {
        "name": "Зимняя парка 'Arctic Pro'",
        "description": "защита до -30°C, мембранная ткань",
        "ad_templates": [
            "Кстати, чтобы не замерзнуть в такую погоду, рекомендую присмотреться к нашей парке Arctic Pro. Она держит тепло даже в -30!",
            "Для таких холодов у нас есть легендарная парка Arctic Pro. С ней никакой мороз не страшен.",
            "Если планируете долго гулять на холоде, обратите внимание на нашу парку Arctic Pro — она как раз для таких случаев."
        ]
    },
    "windbreaker": {
        "name": "Ветровка 'Storm Breaker'",
        "description": "водоотталкивающая, легкая, защита от ветра",
        "ad_templates": [
            "В такую сырую погоду очень выручает ветровка Storm Breaker. Она не промокает и отлично защищает от ветра.",
            "Кстати, наша ветровка Storm Breaker создана специально для защиты от дождя и ветра. Очень рекомендую!",
            "Чтобы не промокнуть и не простудиться, посмотрите на Storm Breaker — это идеальная ветровка для непогоды."
        ]
    },
    "trench": {
        "name": "Тренч 'Urban Style'",
        "description": "деловой стиль, итальянская ткань",
        "ad_templates": [
            "Кстати, для прогулок в такую приятную погоду идеально подойдет наш классический тренч Urban Style. Выглядит очень элегантно!",
            "Если хотите подчеркнуть свой стиль в городе, рекомендую присмотреться к нашему тренчу Urban Style из итальянской ткани.",
            "Для деловых встреч и стильных выходов у нас есть отличный тренч Urban Style. В такую ясную погоду он — то, что нужно."
        ]
    }
}


def get_weather_condition(city: str, api_key: str = "") -> Dict[str, Any]:
    """
    Получение текущей погоды через Weather API или симуляция (Mocking).

    Args:
        city (str): Название города.
        api_key (str): Ключ API OpenWeatherMap.

    Returns:
        Dict[str, Any]: Словарь с температурой (temp) и состоянием (condition).
    """
    if not api_key:
        # Mock-данные для тестирования без ключа
        mock_data = [
            {"temp": -15, "condition": "Clear"},
            {"temp": 5, "condition": "Rain"},
            {"temp": 12, "condition": "Clear"}
        ]
        return random.choice(mock_data)

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "temp": int(data["main"]["temp"]),
            "condition": data["weather"][0]["main"]
        }
    except Exception as e:
        print(f"Weather API Error: {e}")
        return {"temp": 0, "condition": "Unknown"}


class AdScenarioEngine:
    """
    Движок для управления триггерами рекламы на основе интентов и погоды.
    """

    def __init__(self):
        """Инициализация движка с отслеживанием истории (History tracking)."""
        self.last_shown_product: Optional[str] = None

    def get_product_by_intent(self, intent: str) -> Optional[str]:
        """Сопоставление интентов (Intents) с конкретными товарами."""
        intent_mapping = {
            "winter_cold": "parka",
            "rain_wind": "windbreaker",
            "style_business": "trench"
        }
        return intent_mapping.get(intent)

    def get_product_by_weather(self, weather_data: Dict[str, Any]) -> Optional[str]:
        """Выбор товара на основе данных о погоде (Weather-based triggering)."""
        temp = weather_data.get("temp", 0)
        condition = weather_data.get("condition", "Clear")

        if temp < -5:
            return "parka"
        
        if condition in ["Rain", "Thunderstorm", "Drizzle", "Mist"]:
            return "windbreaker"
        
        if 5 <= temp <= 18 and condition == "Clear":
            return "trench"
            
        return None

    def generate_ad_message(self, product_key: str) -> str:
        """Генерация случайного рекламного сообщения (Ad message)."""
        if product_key not in PRODUCTS:
            return ""

        templates = PRODUCTS[product_key]["ad_templates"]
        ad_message = random.choice(templates)
        
        self.last_shown_product = product_key
        return ad_message


if __name__ == "__main__":
    engine = AdScenarioEngine()
    print(f"Тест Ad by Intent: {engine.generate_ad_message('parka')}")
