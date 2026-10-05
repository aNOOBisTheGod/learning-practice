import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description='Собрать архив КТ1')
parser.add_argument('--repo-url', help='Ссылка на созданный репозиторий')
parser.add_argument('--draft', action='store_true', help='Допустить незаполненную ссылку')
args = parser.parse_args()
folder = root / 'submission'
url_file = folder / 'vcs/repo_url.txt'
url = args.repo_url if args.repo_url is not None else url_file.read_text().strip()
if url:
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.netloc or not parsed.path.strip('/') or any(c.isspace() for c in url):
        parser.error('Нужна одна HTTPS-ссылка на репозиторий')
elif not args.draft:
    parser.error('Заполните vcs/repo_url.txt или передайте --repo-url. Пока можно собрать только --draft.')

sources = json.loads((root / 'docs/sources.json').read_text())
assert len(sources) >= 15
assert sum(s['domestic'] for s in sources) * 2 >= len(sources)
assert sum(s['peer'] for s in sources) >= 5
assert all(s.get('standard') or s['year'] >= 2022 for s in sources)
citations = set(map(int, re.findall(r'\[(\d+)\]', (root / 'docs/report.txt').read_text())))
assert citations == {s['id'] for s in sources}, 'Не все источники упомянуты в отчёте'
log = subprocess.check_output(['git', 'log', '--all', '--date=iso',
                              '--pretty=format:%h %ad %an %s'], cwd=root)
dates = subprocess.check_output(['git', 'log', '--all', '--format=%ad', '--date=short'], cwd=root).splitlines()
assert len(dates) >= 3 and len(set(dates)) >= 3, 'В истории меньше трёх дат'
report = 'Отчет_ИКБО-10-24_НовожиловВА_КТ1.pdf'
files = [report, 'translation/original.pdf', 'vcs/git_log.txt', 'vcs/repo_url.txt']
for name in [report, 'translation/original.pdf']:
    assert (folder / name).read_bytes().startswith(b'%PDF-'), f'Неверный PDF: {name}'
url_file.write_text(url + '\n' if url else '')
(folder / 'vcs/git_log.txt').write_bytes(log)
archive = root / 'ИКБО-10-24_НовожиловВА_КТ1.zip'
with ZipFile(archive, 'w', ZIP_DEFLATED) as zipped:
    for name in files:
        zipped.write(folder / name, name)
with ZipFile(archive) as zipped:
    assert zipped.namelist() == files
    assert zipped.testzip() is None
print(archive)
print(f'Источники: {len(sources)}, отечественные: {sum(s["domestic"] for s in sources)}, рецензируемые: {sum(s["peer"] for s in sources)}')
if not url:
    print('ЧЕРНОВОЙ КОМПЛЕКТ: repo_url.txt пуст. Перед сдачей добавьте ссылку и пересоберите архив.')
else:
    print('Архив собран. Доступность репозитория и фактические дни работы этим скриптом не проверяются.')
