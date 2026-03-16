#!/bin/sh

echo "Заполняем базу..."
python fill_db.py
echo "База успешно заполнена!"

echo "Запускаем Flask..."
python main.py
echo "Flask сервер запущен!"

exec "$@"