"""Дополнить исправленный отчёт КТ1 аналитическим разделом."""
from copy import deepcopy
import inspect
import json
from pathlib import Path
import sys

from docx import Document
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kt2/src'))
from main import check_configuration, evaluate_protocol


def build():
    doc=Document(ROOT/'docs/kt1_corrected.docx')
    # Сохранить исходное заключение и список литературы для переноса после главы 5.
    tail=[];capture=False
    for child in list(doc.element.body):
        text=''.join(child.itertext()) if False else ''.join(child.xpath('.//w:t/text()'))
        if text=='Заключение':capture=True
        if capture and child.tag!=qn('w:sectPr'):
            tail.append(deepcopy(child));doc.element.body.remove(child)
    for p in doc.paragraphs:
        if p.text=='КТ1 — Исследовательский этап':
            p.runs[0].text='КТ2 — Аналитический этап'
            for run in p.runs[1:]:run.text=''
    for name in ('Normal','Heading 1','Heading 2','Heading 3'):
        st=doc.styles[name];st.font.name='Times New Roman';st.font.size=Pt(14);st.font.color.rgb=RGBColor(0,0,0)
        fonts=st.element.get_or_add_rPr().find(qn('w:rFonts'))
        for key in list(fonts.attrib):
            if 'theme' in key.lower():del fonts.attrib[key]
        for key in ('ascii','hAnsi','eastAsia','cs'):fonts.set(qn('w:'+key),'Times New Roman')
    def p(text):
        para=doc.add_paragraph(text)
        fmt=para.paragraph_format;fmt.line_spacing=1.5;fmt.first_line_indent=Mm(12.5);fmt.space_after=Pt(0);fmt.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        return para
    def h(text,level=2):
        para=doc.add_heading(text,level)
        para.paragraph_format.keep_with_next=True
        return para
    def page():doc.add_page_break()
    def section(kind='portrait'):
        sec=doc.add_section(WD_SECTION_START.NEW_PAGE)
        sec.orientation=WD_ORIENT.PORTRAIT if kind=='portrait' else WD_ORIENT.LANDSCAPE
        sec.page_width,sec.page_height=(Mm(210),Mm(297)) if kind=='portrait' else ((Mm(420),Mm(297)) if kind=='a3' else (Mm(297),Mm(210)))
        sec.left_margin=Mm(30);sec.right_margin=Mm(10);sec.top_margin=sec.bottom_margin=Mm(20)
        sec.different_first_page_header_footer=False
        return sec
    def cap(text):
        para=doc.add_paragraph(text);para.alignment=WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.first_line_indent=Mm(0);para.paragraph_format.line_spacing=1.5
        para.paragraph_format.space_after=Pt(6)
        return para
    def figure(name,title):
        section('a3')
        from PIL import Image
        im=Image.open(ROOT/'kt2/models'/name)
        width=min(380,225*im.width/im.height)
        para=doc.add_paragraph();para.alignment=WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.first_line_indent=Mm(0);para.paragraph_format.line_spacing=1
        para.paragraph_format.keep_with_next=True
        run=para.add_run();run.add_picture(str(ROOT/'kt2/models'/name),width=Mm(width))
        inline=run._r.xpath('.//wp:docPr')[0];inline.set('descr',title)
        cap(title)
    def table(headers,rows,widths):
        t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
        for col,w in zip(t.columns,widths):col.width=Mm(w)
        for cell,w,text in zip(t.rows[0].cells,widths,headers):cell.width=Mm(w);cell.text=text
        hdr=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(hdr)
        for row in rows:
            cells=t.add_row().cells
            for c,w,text in zip(cells,widths,row):c.width=Mm(w);c.text=text
        for i,row in enumerate(t.rows):
            trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
            for c in row.cells:
                for para in c.paragraphs:
                    para.paragraph_format.first_line_indent=Mm(0);para.paragraph_format.line_spacing=1.5
                    para.paragraph_format.space_after=Pt(3);para.paragraph_format.space_before=Pt(3)
                    para.alignment=WD_ALIGN_PARAGRAPH.LEFT
                    for r in para.runs:r.font.name='Times New Roman';r.font.size=Pt(14);r.bold=i==0
        return t
    def code(fn):
        # Фрагменты двух алгоритмов; полный CLI остаётся в src.
        lines=inspect.getsource(fn).splitlines()
        lines=[line for line in lines if '"""' not in line]
        for line in lines:
            para=doc.add_paragraph(line)
            para.alignment=WD_ALIGN_PARAGRAPH.LEFT
            para.paragraph_format.first_line_indent=Mm(0);para.paragraph_format.line_spacing=1.5
            para.paragraph_format.space_after=Pt(0);para.paragraph_format.keep_with_next=False
            for r in para.runs:r.font.name='Times New Roman';r.font.size=Pt(14)
    h('5 Аналитический раздел',1)
    p('На аналитическом этапе текстовое описание процесса из раздела 2 преобразовано в модель BPMN 2.0, логическую модель данных и процедурную программу. Сохраняются прежние границы: от передачи согласованной заявки и комплекта деталей до передачи сервера с протоколом либо возврата изделия на доработку. Программа проверяет состав оборудования и полноту результатов; окончательное решение остаётся за ответственным за приёмку.')
    h('5.1 Модель бизнес-процесса')
    p('Модель на рисунке 1 построена в нотации BPMN 2.0 по спецификации OMG [19]. Инициатор показан отдельным пулом, исполнители внутри процесса — четырьмя дорожками. Начальное событие означает получение заявки и комплекта; исходящий поток инициатора — сообщение, а внутри рабочего пула применяются потоки последовательности. У задач указаны действия и объекты, у исключающих шлюзов — условия и ветви «да»/«нет».')
    p('При регистрации заявки открывается карточка прогона. Затем инженер проверяет детали, собирает сервер и выполняет первое включение. При пригодном комплекте и успешном POST система сверяет обнаруженную конфигурацию. Затем инженер выполняет план испытаний, система проверяет готовность и формирует протокол. Ответственный рассматривает протокол: допуск ведёт к передаче, отказ — к фиксации несоответствий и возврату. Отказы на ранних проверках также направляются на доработку.')
    p('Возврат — граница текущего прохождения процесса, а не удаление результатов. После исправления начинается новый прогон с новым идентификатором и отдельным составом компонентов. Записи первого прогона сохраняются. Голубым отмечены три задачи с программной поддержкой; их названия дословно приведены в таблице 1.')
    figure('bpmn.png','Рисунок 1 — Сборка и приёмочное тестирование сервера в BPMN 2.0')
    section('landscape')
    cap('Таблица 1 — Автоматизируемые операции')
    table(['№','Операция на BPMN','Кто выполняет сейчас','Действие системы','Функция'],[
      ('1','Сверить конфигурацию со спецификацией','Инженер сборки вручную','Сопоставляет модели и количество; выявляет недостающие и лишние экземпляры.','check_configuration()'),
      ('2','Проверить готовность протокола','Инженер испытаний вручную','Находит пропуски и неуспешные тесты, отсутствие журнала или времени, открытые дефекты.','evaluate_protocol()'),
      ('3','Сформировать протокол','Инженер испытаний вручную','Объединяет заявку, состав выбранного прогона, план, результаты, дефекты и предварительное решение.','build_protocol()'),
    ],[10,57,45,85,60])
    p('Проверка совместимости по руководствам, физическая сборка, POST, запуск испытаний и подтверждение приёмки выполняются специалистами. CLI обрабатывает уже внесённые сведения. Формальный допуск не удостоверяет исправность оборудования и достоверность журналов.')
    section()
    h('5.2 Логическая модель данных')
    p('На рисунке 2 показаны одиннадцать связанных сущностей в единой нотации «вороньи лапки». PK обозначает первичный ключ, FK — внешний, AK — дополнительный уникальный ключ. Двойная черта означает ровно одну запись, кружок с лапкой — от нуля до многих, черта с лапкой — от одной до многих. Типы SQL, индексы и особенности PostgreSQL в этой модели не задаются; физическая схема будет разработана на КТ4.')
    p('Объекты данных на BPMN непосредственно задают сущности: «Заявка; спецификация» — orders и spec_items; «Каталог моделей» — models; «Компоненты; состав» — components и run_components; «План; состав; тесты» — plans, plan_tests и tests; «Карточка прогона» — runs; «Результаты» — results; «Дефекты» — defects. Протокол является вычисляемым представлением этих данных и отдельно не хранится.')
    p('Для КТ2 принят ограниченный контекст: одна заявка относится к одному серверу и одной утверждённой версии спецификации. Исполнитель фиксируется строкой-подписью engineer; отдельный справочник сотрудников пока не ведётся. Экземпляр компонента имеет неизменные модель и серийный номер, а его участие в разных прогонах отражается отдельной связью. Прогон открывается до проверки деталей, поэтому ранний дефект также имеет run_id. До первого включения bios и bmc содержат «не определено»; наборы состава и результатов могут быть пустыми. Такой прогон не получает допуск.')
    figure('er_logical.png','Рисунок 2 — Логическая модель данных в нотации «вороньи лапки»')
    section('landscape')
    cap('Таблица 2 — Сущности, атрибуты и ключи')
    rows=[
      ('Заявка (orders). Требования к одному серверу.','id; number; purpose; spec_version; server_serial','PK id. AK number и server_serial. FK нет.'),
      ('Модель (models). Каталог типов комплектующих.','id; kind; name','PK id. AK (kind, name). FK нет.'),
      ('Позиция (spec_items). Количество модели в заявке.','order_id; model_id; quantity','PK (order_id, model_id). FK order_id → orders; model_id → models.'),
      ('План (plans). Утверждённая версия плана.','id; version','PK id. AK version. FK нет.'),
      ('Тест (tests). Каталог проверок.','id; code; name','PK id. AK code. FK нет.'),
      ('Состав плана (plan_tests). Обязательные проверки.','plan_id; test_id','PK (plan_id, test_id). FK plan_id → plans; test_id → tests.'),
      ('Прогон (runs). Попытка сборки и приёмки.','id; order_id; plan_id; number; engineer; bios; bmc','PK id. AK (order_id, number). FK order_id → orders; plan_id → plans.'),
      ('Компонент (components). Физический экземпляр.','id; serial; model_id','PK id. AK (model_id, serial). FK model_id → models.'),
      ('Состав прогона (run_components). Установленные экземпляры.','run_id; component_id','PK (run_id, component_id). FK run_id → runs; component_id → components.'),
      ('Результат (results). Итог теста в данном прогоне.','run_id; test_id; status; log_ref; parameters; performed_at','PK (run_id, test_id). FK run_id → runs; test_id → tests.'),
      ('Дефект (defects). Несоответствие и текущее состояние.','id; run_id; description; status','PK id. FK run_id → runs.'),
    ]
    table(['Сущность и назначение','Атрибуты','Ключи и ссылки'],rows,[77,75,105])
    section()
    h('Связи и ограничения',3)
    p('Заявка имеет одну или несколько позиций спецификации и от нуля до многих прогонов. Каждая позиция принадлежит одной заявке и ссылается на одну модель; каждая модель может встречаться во многих заявках. Связь orders M:N models разрешена через spec_items, где quantity зависит от полной пары (order_id, model_id).')
    p('План содержит одну или несколько обязательных проверок. Тест может входить в разные планы. Связь plans M:N tests разрешена через plan_tests. Каждый прогон ссылается ровно на одну заявку и один план; каждая заявка и каждый план могут использоваться во многих прогонах.')
    p('Модель описывает от нуля до многих экземпляров компонентов. Один прогон содержит от нуля до многих компонентов, а один экземпляр может участвовать в нескольких прогонах. Эта связь M:N разрешена через run_components. Пустая фактическая комплектация разрешена как состояние учёта, но не соответствует непустой спецификации.')
    p('У прогона может быть от нуля до многих результатов и дефектов. Каждый результат относится ровно к одному прогону и одному тесту; один тест встречается во многих результатах. Пара (run_id, test_id) уникальна. Дополнительно тест результата обязан входить в план этого прогона. Отсутствующий результат означает пропуск, а не успешное выполнение.')
    p('Для results допустимы pass, fail, pending; для defects — open, closed. Номера, идентификаторы и количество положительны. Повтор PK/AK, ссылка на отсутствующий объект или результат вне плана отклоняются до запуска алгоритмов. Для допуска учитываются открытые дефекты всех прогонов той же заявки; закрытый дефект сохраняется. Идентификатор заявки в defects не дублируется: он определяется через runs.')
    h('Обоснование третьей нормальной формы',3).paragraph_format.page_break_before=True
    p('1НФ. Каждая запись содержит атомарные значения в контексте задачи; списки компонентов и тестов вынесены в самостоятельные отношения, повторяющихся групп столбцов нет. Все строки имеют первичный ключ [21]. parameters — единая строка параметров запуска, log_ref — одна ссылка на журнал.')
    p('2НФ. У сущностей с простым первичным ключом каждый неключевой атрибут зависит от этого ключа. У spec_items количество определяется полной парой «заявка, модель»; у results статус, журнал, параметры и время определяются полной парой «прогон, тест». plan_tests и run_components содержат только поля составного ключа, поэтому частичных зависимостей неключевых атрибутов нет.')
    p('3НФ. Неключевые атрибуты не определяют другие неключевые атрибуты в принятой предметной модели. Наименование модели хранится в models, версия плана — в plans, наименование теста — в tests, а связанные записи содержат только ссылки. Например, хранение name и kind в каждой позиции заявки создало бы зависимость model_id → name, kind и потребовало исправлять название во многих строках. Выделение models устраняет это дублирование.')
    p('Другой пример: в таблице (run_id, component_id, model_id, serial) модель и серийный номер зависели бы только от component_id — части ключа. Поэтому постоянные свойства вынесены в components, а run_components хранит только участие экземпляра в прогоне. В результате сохраняется история состава и не нарушается 2НФ. Дополнительные уникальные ключи также указаны в таблице 2.')
    h('5.3 Алгоритмы').paragraph_format.page_break_before=True
    p('Алгоритмы реализуют первые две операции таблицы 1. Оба работают после проверки структуры и связей входного JSON. Блок-схемы на рисунках 3 и 4 используют условные обозначения ГОСТ 19.701-90 [20]: терминатор, процесс, параллелограмм ввода-вывода, ромб решения и шестиугольник подготовки цикла. Выходы решений подписаны; счётчики на схемах соответствуют обходам for и enumerate в Python.')
    h('Алгоритм 1 — сверка конфигурации',3)
    p('Вход: позиции спецификации выбранной заявки и фактические экземпляры выбранного прогона. Для каждой модели подсчитывается фактическое количество, совпавшие экземпляры отмечаются в matched. После сравнения количеств отдельный проход добавляет лишние компоненты. Выход — список всех несоответствий; пустой список означает совпадение моделей и количеств. Инженер отдельно проверяет физическую совместимость.')
    figure('algo_1.png','Рисунок 3 — Алгоритм сверки конфигурации со спецификацией')
    section()
    h('Фрагмент процедурной реализации алгоритма 1',3)
    code(check_configuration)
    p('Пусть n — число позиций спецификации, m — число фактически установленных экземпляров. Внешний цикл выполняется n раз; внутренний просматривает все m элементов для каждой позиции без досрочного выхода, итого n·m сравнений. Инициализация matched и завершающий проход стоят O(m), проверки количества — O(n). Худшее время: O(n·m + n + m + 1), при n,m ≥ 1 — O(n·m). Пустой фактический список обрабатывается за O(n + 1).')
    p('Память: O(m) для matched и до O(n + m) замечаний, всего O(n + m + 1) с результатом. Уникальность (order_id, model_id) заранее исключает повторные позиции одной модели. Два вложенных цикла и проверки совпадения/количества обеспечивают требуемые ветвление и вложенность.')
    h('Алгоритм 2 — проверка готовности протокола',3).paragraph_format.page_break_before=True
    p('Вход: результаты одного прогона, число обязательных пунктов плана, дефекты всех прогонов той же заявки и замечания алгоритма 1. В одном проходе проверяются статус, журнал и время каждого результата. Число пропусков определяется разностью количества пунктов плана и результатов. Затем отдельный проход ищет открытые дефекты. Выход: ready и полный список причин отказа.')
    p('Разность корректна только после validate_data(): результаты уникальны по (run_id, test_id) и каждый тест входит в план. Поэтому число результатов не превышает число обязательных тестов и не может скрывать пропуск за счёт дубликата или постороннего теста. Проверки входного JSON не спрятаны в блок-схеме — они являются отдельным этапом подготовки.')
    figure('algo_2.png','Рисунок 4 — Алгоритм проверки готовности протокола')
    section()
    h('Фрагмент процедурной реализации алгоритма 2',3)
    code(evaluate_protocol)
    p('Пусть r — число результатов текущего прогона, d — число дефектов его заявки, e — число замечаний комплектации. Копирование list(configuration_issues) стоит O(e), цикл результатов — O(r), цикл дефектов — O(d), вычисление missing и len() — O(1). Циклы последовательны, поэтому худшее время O(r + d + e + 1) = O(N), где N = r + d + e + 1. Память с накопленным списком причин — O(N). Оценка линейная и отличается от произведения размеров в алгоритме 1 [22].')
    p('Для обоих алгоритмов оценки даны в модели единичной стоимости при ограниченной длине полей и идентификаторов. append() имеет амортизированную стоимость O(1), но суммарная стоимость всех добавлений линейна. strip() просматривает строку: для произвольной длины полей следует добавить O(L), где L — суммарная длина обработанных строк; память сообщений также зависит от L. Словари записей имеют фиксированное число имён полей; сортировка не вызывается.')
    p('Оценки относятся к указанным функциям, а не ко всей CLI-программе. Загрузка, проверка ключей и подготовка связанных выборок выполняются до них. Для T входных записей консервативная оценка подготовки в худшем случае O(T² + L), включая проверки наличия позиций и возможные коллизии хеш-таблиц. Таким образом, линейный обход второго алгоритма не означает линейность полного запуска.')
    h('5.4 Процедурная реализация')
    p('Реализация находится в src/main.py. Использован Python 3.14.3; код совместим с Python 3.12 и новее. Все зависимости входят в стандартную библиотеку: argparse, json, sys и pathlib. Собственных классов, dataclass, NamedTuple, Enum и глобальных изменяемых переменных нет. Сущности представлены словарями, наборы сущностей — списками; вспомогательные индексы и множества создаются внутри функций.')
    p('validate_data() проверяет поля, PK, AK, FK и правила модели. check_configuration() выполняет сверку, evaluate_protocol() формирует предварительное решение, build_protocol() связывает данные и возвращает полный протокол. main() отвечает за аргументы, чтение JSON, вывод и необязательное сохранение результата. Исходные данные функции не изменяют. Повторный прогон выбирается явно по идентификатору; результат предыдущего не подменяется.')
    p('Пример examples/data.json содержит одну заявку, три модели, четыре экземпляра, шесть обязательных тестов и два прогона. Первый прогон содержит fail проверки памяти; второй — шесть pass после исправления. Дефект первого прогона сохранён в состоянии closed. Это учебные данные; реальные аппаратные испытания и экономический эффект не заявляются.')
    p('Запуск из папки src: python3 main.py examples/data.json --run 2. Получается: «Заявка: REQ-001; сервер: SRV-001; прогон: 2», «Спецификация: SPEC-1; план: PLAN-1», «Предварительный допуск: ДА». При --run 1 выводится «Предварительный допуск: НЕТ» и причина «Тест 2: fail». Для сохранения полного JSON-протокола добавляется --output protocol.json.')
    p('Код завершения 0 означает предварительный допуск, 1 — отказ по условиям, 2 — ошибку аргументов, 64 — ошибку файла, JSON, модели или неизвестный прогон. Программа проверяет заполненность времени и ссылки на журнал, но не календарную корректность строки и не содержимое внешнего файла. Подключение PostgreSQL и интерфейс редактирования относятся к последующим этапам.')
    p('Команда python3 test_main.py успешно выполняет 10 групп проверок: допуск, ранний отказ и сохранность истории; дефицит, избыток и лишние модели; fail/pending и пропущенные тесты; отсутствие журнала и времени; открытый дефект прежнего прогона; ошибки ключей и ссылок; изоляция заявок; состав полного протокола; накопление всех причин; ошибки CLI и процедурный стиль. Отдельно проверен запуск из распакованного итогового комплекта.')
    p('Цепочка прослеживается по одним именам: задачи Config/Evaluate/Protocol в BPMN соответствуют трём строкам таблицы 1 и функциям check_configuration(), evaluate_protocol(), build_protocol(). Объекты данных BPMN раскрыты в таблице 2 и повторены без переименования в ключах JSON. Блок-схемы алгоритмов построены по управляющим ветвям этих функций. Исходники диаграмм и PNG находятся в models; история Git и адрес репозитория — в vcs.')
    # Возвращаем заключение и исходную библиографию.
    for child in tail:doc.element.body.insert(len(doc.element.body)-1,child)
    for para in doc.paragraphs:
        if para.text.startswith('Следующий этап — моделирование того же процесса'):
            para.text='На аналитическом этапе построены BPMN-модель того же процесса, логическая модель из одиннадцати сущностей с разрешёнными связями M:N и обоснованием 3НФ, а также две блок-схемы. Реализованы процедурные алгоритмы сверки комплектации и проверки протокола с различными оценками сложности. Проверки подтверждают обработку учебных сценариев и сохранность предыдущих прогонов. Следующий этап — объектно-ориентированная реализация на Java; физическая модель и подключение БД относятся к КТ4.'
    refs=[
      '19. Object Management Group. Business Process Model and Notation (BPMN). Version 2.0.2. — 2014. — URL: https://www.omg.org/spec/BPMN/2.0.2/ (дата обращения: 01.11.2026).',
      '20. ГОСТ 19.701-90 (ИСО 5807-85). Единая система программной документации. Схемы алгоритмов, программ, данных и систем. Обозначения условные и правила выполнения. — URL: https://protect.gost.ru/gost/details/0c85e066-f89e-433d-a6d3-b7f746bd0c7c (дата обращения: 01.11.2026).',
      '21. Агафонов, А. А. Основы технологий баз данных : учебное пособие / А. А. Агафонов, А. М. Белов. — Самара : Издательство Самарского университета, 2023. — 304 с. — ISBN 978-5-7883-1915-5. — URL: https://repo.ssau.ru/jspui/handle/123456789/57661 (дата обращения: 01.11.2026).',
      '22. Cormen, T. H. Introduction to Algorithms / T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein. — 4th ed. — Cambridge : MIT Press, 2022. — 1312 p. — URL: https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/ (дата обращения: 01.11.2026).',
    ]
    for ref in refs:
        para=p(ref);para.paragraph_format.first_line_indent=Mm(0);para.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for para in doc.paragraphs:
        if para.text.startswith('Основой доработки является коммит'):
            para.text=para.text.replace('Основой доработки является', 'Основой исправленной версии КТ1 являлся').replace('В данной редакции', 'В редакции КТ1').replace('История содержит', 'На момент КТ1 история содержала')
        if para.text.startswith('Выгрузка истории сформирована командой'):
            para.text='Выгрузка истории формируется командой git log --all --date=iso --pretty=format:"%h %ad %an %s" [13]. Она приложена как vcs/git_log.txt; адрес репозитория записан одной строкой в vcs/repo_url.txt. В комплекте КТ2 используются обновлённые материалы того же репозитория.'
    for para in doc.paragraphs:
        if 'Страницы 1 и 24 оригинала приложены как translation/original.pdf' in para.text:
            para.text=para.text.replace('Страницы 1 и 24 оригинала приложены как translation/original.pdf', 'Страницы 1 и 24 оригинала приложены к КТ1 как translation/original.pdf')
    # Перестроить статическое содержание по реальным заголовкам, сохранив титул.
    paragraphs=doc.paragraphs
    start=next(p for p in paragraphs if p.text=='СОДЕРЖАНИЕ')
    intro=next(p for p in paragraphs if p.text=='Введение' and p.style.name=='Heading 1')
    pos=start._p.getnext()
    while pos is not intro._p:
        nxt=pos.getnext();pos.getparent().remove(pos);pos=nxt
    page_map_path=ROOT/'docs/kt2_page_map.json'
    page_map=json.loads(page_map_path.read_text()) if page_map_path.exists() else {}
    headings=[p.text for p in doc.paragraphs if p.style.name in ('Heading 1','Heading 2')]
    for heading in headings:
        para=doc.add_paragraph(heading+'\t'+str(page_map.get(heading,'')))
        fmt=para.paragraph_format;fmt.first_line_indent=Mm(0);fmt.line_spacing=1.5;fmt.space_after=Pt(0);fmt.space_before=Pt(0)
        fmt.tab_stops.add_tab_stop(Mm(170),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        para.alignment=WD_ALIGN_PARAGRAPH.LEFT
        intro._p.addprevious(para._p)
    doc.core_properties.title='Сборка и тестирование серверного оборудования'
    doc.core_properties.subject='Учебная практика — КТ2 — Аналитический этап'
    doc.core_properties.author='Новожилов Василий Алексеевич'
    doc.core_properties.comments=''
    out=ROOT/'kt2/report.docx';doc.save(out);print(out)


if __name__=='__main__':build()
