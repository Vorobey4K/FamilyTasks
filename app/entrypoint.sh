#!/bin/sh

echo "Ждём БД..."
sleep 3

echo "Заполняем базу..."
python fill_db.py

echo "Запускаем Flask..."
python main.py

exec "$@"