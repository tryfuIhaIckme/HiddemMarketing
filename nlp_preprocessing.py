import re
from typing import Optional
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)

# Инициализация компонентов Natasha для NLP-обработки
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)


def clean_text(text: str) -> str:
    """
    Очистка входного текста: удаление спецсимволов и лишних пробелов.
    Оставляет русские и английские буквы, цифры и дефисы.

    Args:
        text (str): Исходная сырая строка (Raw text).

    Returns:
        str: Очищенная строка в нижнем регистре (Lowercase).
    """
    if not text:
        return ""
        
    # Приведение к нижнему регистру (Lowercase)
    text = text.lower()
    
    # Обновленный Regex: оставляем а-я, a-z, цифры 0-9, дефис и пробел.
    # Это критично для распознавания брендов (Arctic Pro) и размеров (XL).
    text = re.sub(r'[^а-яёa-z0-9\-\s]', ' ', text)
    
    # Замена множественных пробелов на один и удаление пробелов по краям (Strip)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def lemmatize_text(text: str) -> str:
    """
    Лемматизация текста с использованием библиотеки Natasha.
    Приводит слова к их словарной форме (Lemma).

    Args:
        text (str): Очищенная входная строка.

    Returns:
        str: Строка, состоящая из лемм слов.
    """
    if not text:
        return ""
        
    doc = Doc(text)
    
    # Применение сегментации (Segmentation) и морфологического теггера (Morphological Tagger)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    
    # Лемматизация каждого токена (Token)
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        
    # Сборка лемм (Lemmas) обратно в одну строку через пробел
    lemmas = [token.lemma for token in doc.tokens]
    return " ".join(lemmas)


def preprocess_text(text: Optional[str]) -> str:
    """
    Главный оркестратор (Pipeline) предобработки: очистка + лемматизация.

    Args:
        text (Optional[str]): Сырой текст от пользователя.

    Returns:
        str: Полностью нормализованный текст, готовый для ML-модели.
    """
    if text is None or not text.strip():
        return ""
        
    cleaned = clean_text(text)
    lemmatized = lemmatize_text(cleaned)
    
    return lemmatized


if __name__ == "__main__":
    # Тестовые примеры для проверки модуля (включая английские термины и цифры)
    test_phrases = [
        "Привет!!! Как дела???",
        "Я хочу купить тёплую парку Arctic Pro размера XL",
        "Какая-то странная погодка сегодня... 2024 год"
    ]
    
    print("--- Тестирование модуля NLP Preprocessing (Обновленный) ---")
    for phrase in test_phrases:
        processed = preprocess_text(phrase)
        print(f"Original: {phrase}")
        print(f"Preprocessed: {processed}")
        print("-" * 40)
