import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

root = Path(__file__).resolve().parent.parent
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.left_margin, sec.right_margin = Mm(30), Mm(10)
sec.top_margin = sec.bottom_margin = Mm(20)
sec.footer_distance = Mm(10)
sec.different_first_page_header_footer = True
for name in ['Normal', 'Title', 'Heading 1', 'Heading 2', 'TOC Heading']:
    style = doc.styles[name]
    style.font.name = 'Times New Roman'
    style.font.size = Pt(14)
    style.font.color.rgb = RGBColor(0, 0, 0)
    fmt = style.paragraph_format
    fmt.line_spacing = 1.5
    fmt.space_after = Pt(5)
    fmt.space_before = Pt(0)
    fmt.widow_control = True
normal = doc.styles['Normal'].paragraph_format
normal.first_line_indent = Mm(12.5)
normal.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
for name in ['Heading 1', 'Heading 2']:
    fmt = doc.styles[name].paragraph_format
    fmt.first_line_indent = Mm(0)
    fmt.keep_with_next = True
    doc.styles[name].font.bold = True
    fmt.space_after = Pt(12)
doc.styles['Heading 1'].paragraph_format.page_break_before = True
doc.styles['Heading 1'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.styles['Heading 2'].paragraph_format.space_before = Pt(10)
lang = OxmlElement('w:lang'); lang.set(qn('w:val'), 'ru-RU')
doc.styles['Normal'].element.get_or_add_rPr().append(lang)

def para(text, align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=5, bold=False, style=None):
    p = doc.add_paragraph(text, style)
    p.alignment = align
    p.paragraph_format.first_line_indent = Mm(0)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if bold:
        for r in p.runs: r.bold = True
    return p

def field(p, instruction, placeholder=''):
    r = p.add_run()
    begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = instruction
    sep = OxmlElement('w:fldChar'); sep.set(qn('w:fldCharType'), 'separate')
    text = OxmlElement('w:t'); text.text = placeholder
    end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end')
    for el in [begin, instr, sep, text, end]: r._r.append(el)

p = sec.footer.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Mm(0)
field(p, ' PAGE ', '2')
for text in ['МИНОБРНАУКИ РОССИИ', 'Федеральное государственное бюджетное образовательное учреждение высшего образования', '«МИРЭА - Российский технологический университет»', '(РТУ МИРЭА)']:
    para(text)
para('ОТЧЁТ ПО УЧЕБНОЙ ПРАКТИКЕ', before=55, bold=True, style='Title')
para('КТ1 Исследовательский этап')
para('Тема', before=15)
para('Сборка и тестирование серверного оборудования', bold=True, after=30)
for text in ['Выполнил: Новожилов Василий Алексеевич', 'Группа: ИКБО-10-24', 'Место практики: ООО «Бюджетные и Финансовые Технологии»', 'Руководитель от университета: Синицын Анатолий Васильевич', 'Руководитель от предприятия: Жиркова М. И.']:
    para(text, WD_ALIGN_PARAGRAPH.LEFT)
para('Москва 2026', before=40)
doc.add_page_break()
para('Содержание', bold=True, after=15)
p = doc.add_paragraph()
p.paragraph_format.first_line_indent = Mm(0)
field(p, ' TOC \\o "1-1" \\h \\z ', 'Обновить содержание')
for block in (root / 'docs/report.txt').read_text().strip().split('\n\n'):
    if block.startswith('# '): doc.add_heading(block[2:], 1)
    elif block.startswith('## '): doc.add_heading(block[3:], 2)
    else: doc.add_paragraph(block.replace('\n', ' '))
doc.add_heading('Список использованных источников', 1)
for s in json.loads((root / 'docs/sources.json').read_text()):
    p = doc.add_paragraph(f"{s['id']}. {s['reference']} - URL: {s['url']} (дата обращения: 05.10.2026).")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Mm(0)
    p.paragraph_format.space_after = Pt(10)
doc.core_properties.author = 'Новожилов Василий Алексеевич'
doc.core_properties.title = 'Сборка и тестирование серверного оборудования'
doc.core_properties.subject = 'Отчёт по учебной практике КТ1'
doc.core_properties.comments = ''
out = root / 'submission/Отчет_ИКБО-10-24_НовожиловВА_КТ1.docx'
doc.save(out)
print(out)
