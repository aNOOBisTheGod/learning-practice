"""Build a minimal peer-review bundle. This is NOT the final SDO submission."""
from pathlib import Path
import hashlib
import json
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'b4be7f6d78585331e4f4928b7324899a3f13789b'
PREFIXES = ('kt3/src/java/', 'kt3/models/', 'kt2/src/', 'kt2/models/')
EXTRA = {'docs/kt3/comparison.md', 'docs/kt3/packages.puml', 'docs/kt3/packages.png',
         'docs/kt3/parity_results.json', 'scripts/check_kt3_parity.py'}
GUIDES = ('docs/kt3/reviewer.md', 'docs/kt3/review_form.md')

def main():
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASELINE], cwd=ROOT, text=True).splitlines()
    selected = [p for p in tracked if p.startswith(PREFIXES) or p in EXTRA]
    content = {p: subprocess.check_output(['git', 'show', f'{BASELINE}:{p}'], cwd=ROOT) for p in selected}
    for p in GUIDES:
        content[p] = (ROOT / p).read_bytes()
    content['README.md'] = ('# Комплект КТ3 для рецензента\n\n'
        'Автор: Новожилов Василий Алексеевич, ИКБО-10-24.\n\n'
        'Начни с [инструкции рецензента](docs/kt3/reviewer.md). '
        'Для замечаний — [форма](docs/kt3/review_form.md).\n\n'
        f'Проверяемый коммит: `{BASELINE}`.\n\n'
        'Нужен JDK 17+, для сравнения с КТ2 — Python 3.12+. '
        'Все команды выполняются из этой папки:\n\n'
        '```sh\nsh kt3/src/java/test.sh\npython3 scripts/check_kt3_parity.py\n```\n\n'
        'Это автономный комплект для взаимного ревью, не архив сдачи в СДО.\n').encode()
    manifest = {'baseline': BASELINE, 'sha256': {p: hashlib.sha256(data).hexdigest() for p, data in sorted(content.items())}}
    content['manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    archive = ROOT / 'ИКБО-10-24_НовожиловВА_КТ3_для_рецензии.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
        for name, data in sorted(content.items()):
            assert not any(part in ('.git', 'out', '__pycache__', '.env') for part in Path(name).parts)
            assert not name.endswith(('.class', '.pyc'))
            z.writestr(name, data)
    print(f'{archive}\nFiles: {len(content)}')

if __name__ == '__main__':
    main()
