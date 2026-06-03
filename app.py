from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for

from config import settings
from core.matchmaking import find_match_for_user
from core.questionnaire import create_user_with_answers, load_questions, validate_answers
from core.reputation import store_reflection, update_user_reputation
from core.storage import get_connection, init_db

app = Flask(__name__)


@app.before_request
def ensure_db():
    init_db()


@app.get("/")
def home():
    return render_template("home.html")


@app.route("/questionnaire", methods=["GET", "POST"])
def questionnaire():
    questions = load_questions()

    if request.method == "POST":
        pseudonym = request.form.get("pseudonym", "").strip()
        if not pseudonym:
            return render_template("questionnaire.html", questions=questions, errors=["Pseudonym is required."])

        answers, errors = validate_answers(questions, request.form)
        if errors:
            return render_template("questionnaire.html", questions=questions, errors=errors)

        user_id = create_user_with_answers(pseudonym, answers)
        return redirect(url_for("match", user_id=user_id))

    return render_template("questionnaire.html", questions=questions, errors=[])


@app.get("/match/<int:user_id>")
def match(user_id):
    candidate = find_match_for_user(user_id)
    return render_template("match.html", user_id=user_id, candidate=candidate)


@app.post("/match/<int:user_id>/start")
def start_conversation(user_id):
    partner_id = int(request.form["partner_id"])
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversations (user_a_id, user_b_id, started_at, duration_minutes) VALUES (?, ?, ?, ?)",
        (user_id, partner_id, now, settings.CONVERSATION_MINUTES),
    )
    conversation_id = cur.lastrowid
    conn.commit()
    conn.close()

    return redirect(url_for("conversation", conversation_id=conversation_id, as_user=user_id))


@app.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
def conversation(conversation_id):
    as_user = int(request.args.get("as_user", request.form.get("as_user", 0)))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    convo = cur.fetchone()

    if convo is None:
        conn.close()
        return "Conversation not found", 404

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            cur.execute(
                "INSERT INTO messages (conversation_id, sender_user_id, body, created_at) VALUES (?, ?, ?, ?)",
                (conversation_id, as_user, body, datetime.utcnow().isoformat()),
            )
            conn.commit()

    cur.execute(
        """
        SELECT m.*, u.pseudonym
        FROM messages m
        JOIN users u ON u.id = m.sender_user_id
        WHERE m.conversation_id = ?
        ORDER BY m.created_at ASC
        """,
        (conversation_id,),
    )
    messages = cur.fetchall()

    cur.execute("SELECT id, pseudonym FROM users WHERE id IN (?, ?)", (convo["user_a_id"], convo["user_b_id"]))
    participants = cur.fetchall()
    conn.close()

    return render_template(
        "conversation.html",
        conversation_id=conversation_id,
        as_user=as_user,
        duration_minutes=convo["duration_minutes"],
        messages=messages,
        participants=participants,
    )


@app.route("/reflection/<int:conversation_id>", methods=["GET", "POST"])
def reflection(conversation_id):
    as_user = int(request.args.get("as_user", request.form.get("as_user", 0)))

    if request.method == "POST":
        strongest_point = request.form.get("strongest_point", "")
        summary_of_other = request.form.get("summary_of_other", "")
        felt_understood = int(request.form.get("felt_understood", "0"))
        was_respectful = int(request.form.get("was_respectful", "0"))

        store_reflection(
            conversation_id,
            as_user,
            strongest_point,
            summary_of_other,
            felt_understood,
            was_respectful,
        )
        score = update_user_reputation(as_user)
        return redirect(url_for("done", conversation_id=conversation_id, as_user=as_user, score=score))

    return render_template("reflection.html", conversation_id=conversation_id, as_user=as_user)


@app.get("/done/<int:conversation_id>")
def done(conversation_id):
    as_user = int(request.args.get("as_user", "0"))
    score = request.args.get("score", "0")
    return render_template("result.html", conversation_id=conversation_id, as_user=as_user, score=score)


if __name__ == "__main__":
    app.run(debug=True)
