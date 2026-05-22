import compatibility
from flask import Flask, render_template_string, jsonify
import csv
import os
from collections import Counter

app = Flask(__name__)

LOG_FILE = "bot_log.csv"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Style & Warmth | Admin Panel</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <style>
        .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
        .intent-badge { background-color: #e1f5fe; color: #01579b; }
        .fallback-badge { background-color: #fff3e0; color: #e65100; }
        header { padding: 20px 0; border-bottom: 1px solid #eee; margin-bottom: 30px; }
        .stats-card { text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; }
    </style>
</head>
<body>
    <main class="container">
        <header>
            <hgroup>
                <h1>Админ-панель бота «Стиль & Тепло»</h1>
                <p>Мониторинг сообщений и аналитика интентов в реальном времени</p>
            </hgroup>
        </header>

        <section id="stats">
            <div class="grid">
                <div class="stats-card">
                    <strong>Всего сообщений</strong>
                    <h2 id="total-messages">{{ stats.total }}</h2>
                </div>
                <div class="stats-card">
                    <strong>Популярный интент</strong>
                    <h2 id="top-intent">{{ stats.top_intent }}</h2>
                </div>
                <div class="stats-card">
                    <strong>Успешность (NLU)</strong>
                    <h2 id="nlu-rate">{{ stats.nlu_rate }}%</h2>
                </div>
            </div>
        </section>

        <section id="log-table">
            <figure>
                <table role="grid">
                    <thead>
                        <tr>
                            <th>Время</th>
                            <th>Текст пользователя</th>
                            <th>Интент (Intent)</th>
                            <th>Ответ бота</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in logs %}
                        <tr>
                            <td>{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td>
                                <span class="status-badge {{ 'intent-badge' if row[2] != 'None (Fallback)' else 'fallback-badge' }}">
                                    {{ row[2] }}
                                </span>
                            </td>
                            <td>{{ row[3] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </figure>
        </section>
        
        <footer>
            <small><a href="/">Обновить данные</a> | Запущено на localhost</small>
        </footer>
    </main>
</body>
</html>
"""

def get_logs_and_stats():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            logs = list(reader)
    
    logs.reverse()

    total = len(logs)
    intents = [row[2] for row in logs if row[2] != "None (Fallback)"]
    top_intent = Counter(intents).most_common(1)[0][0] if intents else "N/A"
    
    nlu_count = len(intents)
    nlu_rate = round((nlu_count / total * 100), 1) if total > 0 else 0

    stats = {
        "total": total,
        "top_intent": top_intent,
        "nlu_rate": nlu_rate
    }
    
    return logs, stats

@app.route('/')
def index():
    logs, stats = get_logs_and_stats()
    return render_template_string(HTML_TEMPLATE, logs=logs, stats=stats)

if __name__ == '__main__':
    print("--- Web Admin Panel запущен на http://127.0.0.1:5000 ---")
    app.run(host='0.0.0.0', port=5000, debug=True)
