# КТ3 — учёт комплектации и приёмочных испытаний на Java

ООП-версия процедурной программы `kt2/src/main.py`. Входная модель содержит те же 11 наборов сущностей. На одинаковых корректных данных совпадают полный JSON-протокол, порядок причин отказа, текст результата в консоли и код завершения.

## Среда и сборка

JDK 17 или новее; проверено на Amazon Corretto OpenJDK **17.0.15**. Инструмент сборки — `javac`, целевая версия Java 17. Сторонних библиотек и сетевых загрузок нет. Все команды ниже выполняются из `kt3/src/java/` в репозитории или `src/java/` будущего архива.

Linux/macOS, POSIX shell:

```sh
sh build.sh
java -cp out practice.Main examples/data.json --run 2
```

Эквивалентная ручная сборка:

```sh
mkdir -p out
find src -name '*.java' | sort > out/sources.txt
javac -encoding UTF-8 --release 17 -Xlint:all -d out @out/sources.txt
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force out | Out-Null
Get-ChildItem src -Recurse -Filter *.java | ForEach-Object { $_.FullName } | Set-Content -Encoding ascii out/sources.txt
javac -encoding UTF-8 --release 17 -Xlint:all -d out '@out/sources.txt'
java -Dfile.encoding=UTF-8 -cp out practice.Main examples/data.json --run 2
```

Для пути проекта с пробелами в PowerShell оберните каждую строку `sources.txt` в двойные кавычки. Linux/macOS-скрипт использует относительные пути исходников без пробелов.

## Вход и вывод

Полный пример — `examples/data.json`, побайтовая копия примера КТ2. В нём одна заявка, три модели, четыре компонента, шесть обязательных проверок, два прогона и один закрытый дефект. Прогон 1 содержит неуспешную проверку памяти, прогон 2 — шесть успешных проверок.

```sh
java -cp out practice.Main examples/data.json --run 2 --output out/protocol.json
```

Ожидаемый вывод и код завершения 0:

```text
Заявка: REQ-001; сервер: SRV-001; прогон: 2
Спецификация: SPEC-1; план: PLAN-1
Предварительный допуск: ДА
```

```sh
java -cp out practice.Main examples/data.json --run 1
```

Ожидаемый вывод и код завершения 1:

```text
Заявка: REQ-001; сервер: SRV-001; прогон: 1
Спецификация: SPEC-1; план: PLAN-1
Предварительный допуск: НЕТ
- Тест 2: fail
```

Коды завершения: `0` — допуск, `1` — отказ по правилам, `2` — ошибка аргументов, `64` — ошибка файла, JSON, модели или неизвестный прогон. `--help` показывает команду запуска. JSON сохраняет значения и порядок элементов списков КТ2; пробелы и отступы сериализации могут различаться. Диагностические формулировки ошибок ввода в двух языках могут различаться.

## Модель и ограничения

| Набор JSON | Класс | Поля |
| --- | --- | --- |
| orders | Order | id, number, purpose, spec_version, server_serial |
| models | ComponentModel | id, kind, name |
| spec_items | SpecificationItem | order_id, model_id, quantity |
| plans | TestPlan | id, version |
| tests | TestDefinition | id, code, name |
| plan_tests | PlanTest | plan_id, test_id |
| runs | TestRun | id, order_id, plan_id, number, engineer, bios, bmc |
| components | Component | id, serial, model_id |
| run_components | RunComponent | run_id, component_id |
| results | TestResult | run_id, test_id, status, log_ref, parameters, performed_at |
| defects | Defect | id, run_id, description, status |

ID, ссылки, количество и номер прогона — положительные целые `BigInteger`; остальные значения — строки. `results.status`: `pass`, `fail`, `pending`; `defects.status`: `open`, `closed`. Точный набор таблиц и полей обязателен. PK/AK и FK совпадают с КТ2, результат должен относиться к тесту из плана своего прогона. У каждой заявки есть спецификация, у каждого плана — хотя бы один тест.

Карточка прогона создаётся при регистрации заявки, до проверки деталей. Для раннего отказа допустимы пустые состав и результаты; до включения BIOS/BMC обозначаются строкой `не определено`. Открытые дефекты **любого прогона той же заявки** блокируют допуск. Прежние результаты и комплектация не изменяются. Проверяется наличие журнала и времени, но не содержимое внешних журналов и не календарная корректность строк — как в КТ2.

Сущности — Java record-классы с закрытыми final-полями и публичными аксессорами. `DataSet` проверяет и копирует вход, `RunContext` хранит неизменяемую выборку. Прямые конструкторы сущностей — внутренний доверенный API; внешний JSON проходит `DataValidator`.

`AcceptanceRule` имеет две конкретные реализации через `AbstractAcceptanceRule`: `ConfigurationRule` и `ProtocolRule`. База проверяет контекст и делает результат неизменяемым; подклассы переопределяют `evaluate()` и реализуют разные проверки. `ProtocolService` использует `List<AcceptanceRule>`, поэтому вызывает правила полиморфно. Новое правило передаётся через конструктор сервиса, без изменения существующих алгоритмов.

`ConfigurationRule` сохраняет вложенный цикл КТ2: O(n·m+n+m+1). `ProtocolRule` делает последовательные проходы: O(r+d+1); объединение с e замечаниями конфигурации — O(r+d+e+1). Оценки даны для ограниченной длины чисел и строк. Полный запуск включает разбор JSON, валидацию и выборку; ему не приписывается линейная сложность второго алгоритма.

JSON-кодек ограничивает глубину вложенности 256 уровнями для контролируемого отказа; корректная модель проекта существенно мельче. Повторяющиеся поля, NaN/Infinity, неверные escape-последовательности и повреждённый UTF-8 отклоняются.

## Тесты

Автономные проверки Java:

```sh
sh test.sh
```

Ожидается `PASS: 44 Java checks`. Проверяются два результата, неизменяемость снимков, полиморфизм, добавление правила, ключи, ранний отказ, старый дефект, JSON и Unicode.

В PowerShell после сборки:

```powershell
javac -encoding UTF-8 --release 17 -Xlint:all -cp out -d out test/SelfTest.java
java -Dfile.encoding=UTF-8 -cp out SelfTest
```

Сравнение с Python выполняется **из корня репозитория**, где сохранена версия КТ2:

```sh
python3 scripts/check_kt3_parity.py
```

Ожидается `PASS: 150 differential cases; 7 additional CLI checks`. Для корректного входа сравниваются все поля JSON и stdout, для ошибочного — код отказа. Включены 30 сценариев с фиксированным seed, 11 таблиц, все FK, неуспешные и пропущенные тесты, чужая заявка, большие числа, Unicode. Результаты сохраняются в `docs/kt3/parity_results.json`. Python не нужен для работы Java-программы и её автономных тестов; процедурные исходники повторно в архив КТ3 не включаются.

UML: `kt3/models/classes.puml` и `classes.png`. Скомпилированные файлы находятся только в `out/`, который исключён из Git.
