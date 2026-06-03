from datetime import datetime

from core.storage import get_connection


def store_reflection(conversation_id, author_user_id, strongest_point, summary_of_other, felt_understood, was_respectful):
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO reflections
        (conversation_id, author_user_id, strongest_point, summary_of_other, felt_understood, was_respectful, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            conversation_id,
            author_user_id,
            strongest_point.strip(),
            summary_of_other.strip(),
            int(felt_understood),
            int(was_respectful),
            now,
        ),
    )

    conn.commit()
    conn.close()


def _summary_quality_score(text):
    length = len(text.strip())
    if length >= 220:
        return 5
    if length >= 140:
        return 4
    if length >= 80:
        return 3
    if length >= 30:
        return 2
    return 1


def update_user_reputation(user_id):
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT felt_understood, was_respectful, summary_of_other
        FROM reflections
        WHERE author_user_id = ?
        """,
        (user_id,),
    )
    rows = cur.fetchall()

    if not rows:
        score = 0.0
    else:
        felt_avg = sum(row["felt_understood"] for row in rows) / len(rows)
        respect_avg = sum(row["was_respectful"] for row in rows) / len(rows)
        summary_avg = sum(_summary_quality_score(row["summary_of_other"]) for row in rows) / len(rows)
        score = round((felt_avg * 0.4) + (respect_avg * 0.4) + (summary_avg * 0.2), 2)

    cur.execute("SELECT id FROM reputation WHERE user_id = ?", (user_id,))
    existing = cur.fetchone()

    if existing:
        cur.execute(
            "UPDATE reputation SET score = ?, updated_at = ? WHERE user_id = ?",
            (score, now, user_id),
        )
    else:
        cur.execute(
            "INSERT INTO reputation (user_id, score, updated_at) VALUES (?, ?, ?)",
            (user_id, score, now),
        )

    conn.commit()
    conn.close()
    return score
