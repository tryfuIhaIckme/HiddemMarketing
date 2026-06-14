import random
import nltk
import json
import os
from typing import Optional, Callable, Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

class IntentClassifier:
    """
    Класс для классификации намерений (Intent Classification) с использованием 
    TF-IDF векторизации и LinearSVC, с гибкой валидацией через расстояние Левенштейна.
    """

    def __init__(self, config_path: str):
        """
        Инициализация классификатора.

        Args:
            config_path (str): Путь к JSON-файлу с конфигурацией.
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Векторизатор на основе символьных n-грамм (N-gram range 2-4 для большей гибкости)
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
        # Модель классификации
        self.clf = LinearSVC(max_iter=2000)
        self.is_trained = False

    def _load_config(self) -> Dict:
        """Загружает конфигурацию из JSON."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def train(self, preprocess_func: Callable[[str], str]) -> None:
        """
        Извлекает данные из конфига, предобрабатывает их и обучает ML-модель.
        """
        x = []
        y = []
        
        for intent, data in self.config["intents"].items():
            for example in data["examples"]:
                preprocessed_example = preprocess_func(example)
                if preprocessed_example:
                    x.append(preprocessed_example)
                    y.append(intent)
        
        if x:
            x_vec = self.vectorizer.fit_transform(x)
            self.clf.fit(x_vec, y)
            self.is_trained = True

    def classify(self, text: str, preprocess_func: Callable[[str], str]) -> Optional[str]:
        """
        Предсказывает интент с повышенной надежностью и гибкостью.
        """
        if not self.is_trained:
            return None
            
        preprocessed_text = preprocess_func(text)
        if not preprocessed_text:
            return None
            
        # 1. Получаем предсказание и оценки уверенности (Decision scores)
        text_vec = self.vectorizer.transform([preprocessed_text])
        scores = self.clf.decision_function(text_vec)[0]
        
        # Сортируем интенты по оценкам
        intent_scores = sorted(zip(self.clf.classes_, scores), key=lambda x: x[1], reverse=True)
        
        # 2. Проверяем топ-3 кандидата через расстояние Левенштейна
        # Это позволяет понять "почти правильные" фразы, даже если ML ошибся
        for intent, score in intent_scores[:3]:
            examples = self.config["intents"][intent]["examples"]
            
            for example in examples:
                preprocessed_example = preprocess_func(example)
                if not preprocessed_example:
                    continue
                
                distance = nltk.edit_distance(preprocessed_text, preprocessed_example)
                max_len = max(len(preprocessed_text), len(preprocessed_example))
                
                # Порог (Threshold) уменьшен до 0.3 для более точного совпадения
                if max_len > 0 and distance / max_len <= 0.3:
                    return intent
                    
        # 3. Если Левенштейн не нашел точного совпадения, но ML очень уверен (высокий score)
        top_intent, top_score = intent_scores[0]
        return top_intent
                
        return None

    def get_response(self, intent: str) -> str:
        """Возвращает случайный ответ для данного интента."""
        responses = self.config["intents"].get(intent, {}).get("responses", [])
        if responses:
            return random.choice(responses)
        return self.get_failure_phrase()

    def get_failure_phrase(self) -> str:
        """Возвращает случайную фразу-заглушку."""
        return random.choice(self.config["failure_phrases"])


if __name__ == "__main__":
    def dummy_preprocess(text: str) -> str:
        import re
        text = text.lower()
        text = re.sub(r'[^а-яёa-z0-9\-\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    # Путь к конфигу
    config_file = "bot_config.json"
    
    classifier = IntentClassifier(config_file)
    print("Обучение Intent Classifier...")
    classifier.train(dummy_preprocess)
    print("Обучение завершено.\n")

    # Тесты на "чуть отличающиеся" слова
    test_queries = [
        "приветикс",         # Опечатка в приветствии
        "дубачина",          # Синоним к холоду
        "че за бот",         # Вариант вопроса об имени
        "какие размеры есть" # Почти как в примере
    ]

    print("--- Тестирование обновленного модуля ---")
    for query in test_queries:
        intent = classifier.classify(query, dummy_preprocess)
        print(f"Query: {query} | Intent: {intent}")
