# Bridge MVP v0.1

Bridge is a structured conversation prototype focused on:
- understanding
- respectful disagreement
- accurate representation of another viewpoint

## What this MVP includes
- Questionnaire with editable JSON questions
- Simple moderate-disagreement matchmaking
- Private anonymous conversation screen (non-realtime)
- Midpoint reminder to summarize the other perspective
- Reflection step after conversation
- Hidden simple reputation score

## Anti-features (intentionally excluded)
- Public feeds, followers, likes, upvotes
- Virality mechanics or debate winners
- Authentication providers
- Realtime sockets/video

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

## Notes
- SQLite database file (`bridge.db`) is created automatically.
- No auth in this first iteration. User identity is passed in URL/query for demo simplicity.
- TODO: Improve reflection quality scoring with richer rubric.
