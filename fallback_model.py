import os
import nltk
from typing import Optional, Callable, Dict, List, Set, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class DialogueFallbackModel:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.questions: List[str] = []
        self.answers: List[str] = []
        self.vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
        self.X_matrix = None

    def load_dataset(self, preprocess_func: Callable[[str], str]) -> None:
        if not os.path.exists(self.dataset_path):
            print(f"Ошибка: Файл датасета не найден: {self.dataset_path}")
            return

        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return

        blocks = content.split("\n\n")
        temp_questions = []
        temp_answers = []
        seen = set()

        for block in blocks[:20000]:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if len(lines) < 2:
                continue
            
            question = lines[0].lstrip("- ").strip()
            answer = lines[1].lstrip("- ").strip()
            
            cleaned_q = preprocess_func(question)
            if cleaned_q and cleaned_q not in seen:
                seen.add(cleaned_q)
                temp_questions.append(cleaned_q)
                temp_answers.append(answer)

        self.questions = temp_questions
        self.answers = temp_answers

        if self.questions:
            self.X_matrix = self.vectorizer.fit_transform(self.questions)
            print(f"Успешно индексировано вопросов для Fallback: {len(self.questions)}")

    def generate_answer(self, text: str, preprocess_func: Callable[[str], str]) -> Optional[str]:
        if self.X_matrix is None or not self.questions:
            return None

        cleaned_query = preprocess_func(text)
        if not cleaned_query:
            return None

        query_vec = self.vectorizer.transform([cleaned_query])
        similarities = cosine_similarity(query_vec, self.X_matrix).flatten()
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        if best_score > 0.45:
            return self.answers[best_idx]
            
        return None


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
