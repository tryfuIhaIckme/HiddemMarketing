import compatibility
import os
import random
import string
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
from typing import Optional


class VoiceManager:
    """
    Модуль для обработки голоса: STT (Speech-to-Text) и TTS (Text-to-Speech).
    
    Примечание: Требуется установленный 'ffmpeg' в системе для работы pydub.
    """

    def __init__(self):
        """Инициализация объекта Recognizer для распознавания речи."""
        self.recognizer = sr.Recognizer()

    def _convert_ogg_to_wav(self, ogg_path: str) -> str:
        """
        Конвертация аудио из .ogg в .wav (требуется для SpeechRecognition).

        Args:
            ogg_path (str): Путь к файлу .ogg.

        Returns:
            str: Путь к созданному временному .wav файлу.
        """
        # Загрузка файла через pydub
        audio = AudioSegment.from_ogg(ogg_path)
        
        # Создание временного файла для .wav
        fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # Экспорт (Export) в формат wav
        audio.export(wav_path, format="wav")
        return wav_path

    def voice_to_text(self, ogg_path: str) -> Optional[str]:
        """
        Преобразование голосового сообщения в текст (STT) через Google API.

        Args:
            ogg_path (str): Путь к файлу голосового сообщения.

        Returns:
            Optional[str]: Распознанный текст или None при ошибке.
        """
        wav_path = None
        try:
            # 1. Конвертация (Conversion)
            wav_path = self._convert_ogg_to_wav(ogg_path)
            
            # 2. Распознавание (Recognition)
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data, language="ru-RU")
                return text
                
        except sr.UnknownValueError:
            print("VoiceManager: Речь не распознана")
            return None
        except sr.RequestError as e:
            print(f"VoiceManager: Ошибка сервиса Google; {e}")
            return None
        except Exception as e:
            print(f"VoiceManager: Неожиданная ошибка: {e}")
            return None
        finally:
            # 3. Очистка временных файлов (Cleanup)
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)

    def text_to_voice(self, text: str) -> str:
        """
        Преобразование текста в голос (TTS) с сохранением в MP3.

        Args:
            text (str): Текст ответа бота.

        Returns:
            str: Путь к сгенерированному аудиофайлу.
        """
        # Генерация речи через Google Text-to-Speech
        tts = gTTS(text=text, lang="ru", slow=False)
        
        # Уникальное имя файла (Unique filename generation)
        random_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        filename = f"response_{random_id}.mp3"
        
        file_path = os.path.join(tempfile.gettempdir(), filename)
        
        # Сохранение (Save)
        tts.save(file_path)
        return file_path


if __name__ == "__main__":
    vm = VoiceManager()
    path = vm.text_to_voice("Проверка синтеза речи")
    print(f"Файл создан: {path}")
    if os.path.exists(path): os.remove(path)
