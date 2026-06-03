from core.storage import get_connection
from config import settings


def average_position_for_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT AVG(score) AS avg_score FROM responses WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return float(row["avg_score"]) if row and row["avg_score"] is not None else None


def find_match_for_user(user_id):
    base_avg = average_position_for_user(user_id)
    if base_avg is None:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT u.id, u.pseudonym, AVG(r.score) AS avg_score
        FROM users u
        JOIN responses r ON u.id = r.user_id
        WHERE u.id != ?
        GROUP BY u.id, u.pseudonym
        """,
        (user_id,),
    )

    candidates = []
    for row in cur.fetchall():
        candidate_avg = float(row["avg_score"])
        distance = abs(candidate_avg - base_avg)
        if settings.DISAGREEMENT_MIN_DISTANCE <= distance <= settings.DISAGREEMENT_MAX_DISTANCE:
            candidates.append(
                {
                    "id": row["id"],
                    "pseudonym": row["pseudonym"],
                    "avg_score": round(candidate_avg, 2),
                    "distance": round(distance, 2),
                }
            )

    conn.close()
    candidates.sort(key=lambda c: c["distance"])
    return candidates[0] if candidates else None
