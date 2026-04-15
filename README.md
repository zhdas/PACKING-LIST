# Веб-интерфейс для распознавания MRZ и VIN с выгрузкой в Excel

## Что делает приложение
- Открывает сайт с полями:
  - номер контейнера
  - номер пломбы
  - количество автомобилей от 1 до 10
- После выбора количества авто автоматически показывает блоки загрузки файлов:
  - фото паспорта
  - фото VIN-стикера
- После нажатия на кнопку создаёт Excel-файл.

## Структура
- `app.py` — Flask сервер и генерация Excel
- `services.py` — распознавание паспорта и VIN на основе Dynamsoft
- `templates/index.html` — интерфейс сайта

## Запуск
```bash
cd container_ui_app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install dynamsoft-capture-vision-bundle
python app.py
```

После запуска откройте:
```text
http://127.0.0.1:5000
```

## Важно
В файле `services.py` нужно вставить вашу лицензию в строку:
```python
"PUT_YOUR_DYNAMSOFT_LICENSE_HERE"
```

## Что можно улучшить дальше
- добавить предпросмотр фото перед отправкой
- сохранять итоговый Excel в базу или папку архива
- делать отдельный лист Excel для каждого авто
- добавлять режим распознавания VIN из barcode и из текста
