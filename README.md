# Сборка и тестирование серверного оборудования

Учебная практика. Новожилов Василий Алексеевич, ИКБО-10-24.

ООО «Бюджетные и Финансовые Технологии». Руководители: Синицын Анатолий Васильевич (от университета), Жиркова М. И. (от предприятия).

Проект для учёта сборки сервера и результатов приёмочных испытаний. На КТ1 сделана проверка протокола из JSON и подготовлена схема PostgreSQL. Подключение к базе будет на следующем этапе.

## Запуск

Прототип реализован на Python (процедурная часть) и Java (ООП).
Обе реализации принимают один и тот же JSON и выдают одинаковый результат.
Проверено на фактически установленных Python 3.14.3 и OpenJDK 17.0.15
(Amazon Corretto). Для сборки Java нужен Maven; зависимость Gson 2.11.0
скачивается автоматически.

Python — без сторонних зависимостей:

```sh
python3 bin/check.py examples/protocol.json
```

Java — модель `Protocol`, проверка `ProtocolEvaluator` и точка входа `Check`:

```sh
mvn -f java/pom.xml package
java -jar java/target/protocol-check.jar examples/protocol.json
```

Программа проверяет комплектность протокола и результаты испытаний. Возвращает 0, если всё прошло, 1 — если есть проблемы, 64 — если файл некорректный. В `examples/` лежат учебные данные.

Общие тесты обеих реализаций (после сборки Java):

```sh
python3 -m unittest discover -s test -p 'test_*.py' -v
```

Схема БД (проверена на PostgreSQL 16):

```sh
createdb server_checks
psql -d server_checks -v ON_ERROR_STOP=1 -f sql/schema.sql
```

## Материалы КТ1

В `docs/` — описание процесса, текст отчёта и источники. В `submission/` — отчёт DOCX, оригинал для перевода и файлы Git.

Собрать архив для СДО:

```sh
python3 scripts/package.py
```

Получится `ИКБО-10-24_НовожиловВА_КТ1.zip`.

Пересобрать DOCX из текста:

```sh
python3 -m venv tmp/report-env
tmp/report-env/bin/pip install -r scripts/report-requirements.txt
tmp/report-env/bin/python scripts/build_docx.py
```

После пересборки нужно обновить содержание в Word и сохранить документ.
