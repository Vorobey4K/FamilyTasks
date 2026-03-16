import json

from models import Tasks, Navigation, Steps, Why_us
from extensions import db
from main import app

models_map = {
    "tasks": Tasks,
    "navigation": Navigation,
    "steps": Steps,
    "why_us": Why_us
}

with open("db.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Важное исправление — контекст приложения
with app.app_context():
    for table_name, rows in data.items():
        Model = models_map.get(table_name)
        if not Model:
            continue

        for row in rows:
            db.session.add(Model(**row))

    db.session.commit()