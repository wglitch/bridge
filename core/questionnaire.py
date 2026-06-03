import json
from datetime import datetime

from core.storage import get_connection


def load_questions(path="config/questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_user_with_answers(pseudonym, answers):
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO users (pseudonym, created_at) VALUES (?, ?)", (pseudonym, now))
    user_id = cur.lastrowid

    for question_key, score in answers.items():
        cur.execute(
            "INSERT INTO responses (user_id, question_key, score) VALUES (?, ?, ?)",
            (user_id, question_key, int(score)),
        )

    conn.commit()
    conn.close()
    return user_id


def validate_answers(questions, form_data):
    answers = {}
    errors = []

    for question in questions:
        key = question["key"]
        raw_value = form_data.get(key)

        if raw_value is None:
            errors.append(f"Missing answer for: {question['text']}")
            continue

        try:
            score = int(raw_value)
        except ValueError:
            errors.append(f"Invalid numeric answer for: {question['text']}")
            continue

        if score < 1 or score > 10:
            errors.append(f"Answer must be between 1 and 10 for: {question['text']}")
            continue

        answers[key] = score

    return answers, errors
