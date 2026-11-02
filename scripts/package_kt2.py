"""Собрать ZIP КТ2 и проверить запуск из распакованного комплекта."""

import ast
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / 'kt2'
    files = [
        'report.docx',
        'models/bpmn.bpmn', 'models/bpmn.png',
        'models/er_logical.drawio', 'models/er_logical.png',
        'models/algo_1.drawio', 'models/algo_1.png',
        'models/algo_2.drawio', 'models/algo_2.png',
        'src/README.md', 'src/main.py', 'src/test_main.py', 'src/examples/data.json',
        'vcs/git_log.txt', 'vcs/repo_url.txt',
    ]
    log = subprocess.check_output(
        ['git', 'log', '--all', '--date=iso', '--pretty=format:%h %ad %an %s'], cwd=root)
    (source / 'vcs/git_log.txt').write_bytes(log + b'\n')
    url = (source / 'vcs/repo_url.txt').read_text().strip()
    if not url.startswith('https://github.com/') or any(c.isspace() for c in url):
        raise ValueError('Некорректный адрес репозитория')
    for name in files:
        path = source / name
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Отсутствует {name}')
        if path.suffix == '.png':
            assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), name
        if path.suffix in ('.bpmn', '.drawio'):
            ET.parse(path)
        if path.suffix == '.py':
            tree = ast.parse(path.read_text(encoding='utf-8'))
            assert not any(isinstance(node, (ast.ClassDef, ast.Global)) for node in ast.walk(tree))
    with ZipFile(source / 'report.docx') as report:
        assert report.testzip() is None
        xml = report.read('word/document.xml').decode()
        for heading in ('5 Аналитический раздел', '5.1 Модель бизнес-процесса',
                        '5.2 Логическая модель данных', '5.3 Алгоритмы',
                        '5.4 Процедурная реализация'):
            assert heading in xml, heading
    bpmn = ET.parse(source / 'models/bpmn.bpmn')
    ns = {'b': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
    assert len(bpmn.findall('.//b:startEvent', ns)) == 1
    assert len(bpmn.findall('.//b:endEvent', ns)) >= 1
    tasks = {node.get('name') for node in bpmn.findall('.//b:userTask', ns)}
    assert {'Сверить конфигурацию со спецификацией', 'Проверить готовность протокола',
            'Сформировать протокол'} <= tasks
    archive = root / 'ИКБО-10-24_НовожиловВА_КТ2.zip'
    report_name = 'Отчет_ИКБО-10-24_НовожиловВА_КТ2.docx'
    archive_names = [report_name if name == 'report.docx' else name for name in files]
    with ZipFile(archive, 'w', ZIP_DEFLATED) as zipped:
        for name, archive_name in zip(files, archive_names):
            zipped.write(source / name, archive_name)
    with ZipFile(archive) as zipped, tempfile.TemporaryDirectory(prefix='kt2-check-') as folder:
        assert zipped.namelist() == archive_names and zipped.testzip() is None
        zipped.extractall(folder)
        work = Path(folder) / 'src'
        subprocess.run([sys.executable, 'test_main.py'], cwd=work, check=True)
        passed = subprocess.run([sys.executable, 'main.py', 'examples/data.json', '--run', '2'],
                                cwd=work, capture_output=True, text=True, check=True)
        assert 'Предварительный допуск: ДА' in passed.stdout
        failed = subprocess.run([sys.executable, 'main.py', 'examples/data.json', '--run', '1'],
                                cwd=work, capture_output=True, text=True)
        assert failed.returncode == 1 and 'Тест 2: fail' in failed.stdout
    print(f'Архив проверен: {archive}')
    print(f'Файлов: {len(files)}; размер: {archive.stat().st_size} байт')


if __name__ == '__main__':
    main()
