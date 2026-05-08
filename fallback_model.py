import os
import nltk
from typing import Optional, Callable, Dict, List, Set, Tuple

class DialogueFallbackModel:
    """
    Модель генерации ответов на основе поиска по датасету (Retrieval-based).
    Использует инвертированный индекс (Inverted Index) для быстрого поиска 
    и расстояние Левенштейна для выбора лучшего кандидата.
    """

    def __init__(self, dataset_path: str):
        """
        Инициализация модели.

        Args:
            dataset_path (str): Путь к файлу dialogues.txt.
        """
        self.dataset_path = dataset_path
        # Структурированный словарь для быстрого поиска по словам
        self.dialogues_structured_cut: Dict[str, List[Tuple[str, str]]] = {}

    def load_dataset(self, preprocess_func: Callable[[str], str]) -> None:
        """
        Загрузка и парсинг датасета, построение инвертированного индекса.

        Args:
            preprocess_func (Callable[[str], str]): Функция нормализации текста.
        """
        if not os.path.exists(self.dataset_path):
            print(f"Ошибка: Файл датасета не найден: {self.dataset_path}")
            return

        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return

        # Разбиение на блоки по двойному переносу строки
        blocks = content.split("\n\n")
        seen_questions: Set[str] = set()
        temp_index: Dict[str, List[Tuple[str, str]]] = {}

        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if len(lines) < 2:
                continue
            
            # Извлечение вопроса и ответа, удаление маркеров "- "
            question = lines[0].lstrip("- ").strip()
            answer = lines[1].lstrip("- ").strip()
            
            # Предобработка вопроса (Normalization)
            preprocessed_q = preprocess_func(question)
            if not preprocessed_q or preprocessed_q in seen_questions:
                continue
                
            seen_questions.add(preprocessed_q)
            
            # Токенизация (Tokenization) на слова для построения индекса
            words = set(preprocessed_q.split())
            for word in words:
                if word not in temp_index:
                    temp_index[word] = []
                temp_index[word].append((preprocessed_q, answer))

        # Оптимизация индекса: ограничение до 1000 пар на слово для производительности
        for word, pairs in temp_index.items():
            sorted_pairs = sorted(pairs, key=lambda x: len(x[0]))
            self.dialogues_structured_cut[word] = sorted_pairs[:1000]

    def generate_answer(self, text: str, preprocess_func: Callable[[str], str]) -> Optional[str]:
        """
        Поиск лучшего ответа в мини-датасете (Mini-dataset) через Levenshtein Distance.

        Args:
            text (str): Фраза пользователя.
            preprocess_func (Callable[[str], str]): Функция нормализации.

        Returns:
            Optional[str]: Найденный ответ или None.
        """
        preprocessed_text = preprocess_func(text)
        if not preprocessed_text:
            return None
            
        words = set(preprocessed_text.split())
        mini_dataset: Set[Tuple[str, str]] = set()
        
        # Сбор кандидатов из инвертированного индекса по словам запроса
        for word in words:
            if word in self.dialogues_structured_cut:
                mini_dataset.update(self.dialogues_structured_cut[word])
        
        candidates: List[Tuple[float, str]] = []
        
        for q, a in mini_dataset:
            len_q = len(q)
            if len_q == 0:
                continue
                
            # 1. Проверка разницы длин фраз (Threshold 0.5)
            if abs(len(preprocessed_text) - len_q) / len_q > 0.5:
                continue
                
            # 2. Расчет взвешенного расстояния Левенштейна (Weighted Distance)
            distance = nltk.edit_distance(preprocessed_text, q)
            distance_weighted = distance / len_q
            
            # 3. Фильтрация по порогу уверенности (Threshold 0.5)
            if distance_weighted < 0.5:
                candidates.append((distance_weighted, a))
                
        if not candidates:
            return None
            
        # Возвращаем ответ кандидата с минимальной дистанцией (Best match)
        best_candidate = min(candidates, key=lambda x: x[0])
        return best_candidate[1]


if __name__ == "__main__":
    def dummy_preprocess(text: str) -> str:
        """Заглушка для тестирования."""
        import re
        text = text.lower()
        text = re.sub(r'[^а-яё\-\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    # Генерация тестового датасета
    dataset_file = "dialogues.txt"
    sample_dialogues = "- привет\n- Здравствуйте!\n\n- как дела\n- Все отлично!\n"
    with open(dataset_file, "w", encoding="utf-8") as f:
        f.write(sample_dialogues)
    
    model = DialogueFallbackModel(dataset_file)
    model.load_dataset(dummy_preprocess)
    print(f"Тест Fallback: {model.generate_answer('как деля', dummy_preprocess)}")
