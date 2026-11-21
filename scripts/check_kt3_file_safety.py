"""Regression for peer review R1: output must never alias input."""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'kt3/src/java'
subprocess.run(['sh', str(JAVA / 'build.sh')], check=True)
commands = {
    'Python': [sys.executable, str(ROOT / 'kt2/src/main.py')],
    'Java': ['java', '-cp', str(JAVA / 'out'), 'practice.Main'],
}
count = 0
for name, command in commands.items():
    with tempfile.TemporaryDirectory() as folder:
        directory = Path(folder)
        source = directory / 'input.json'
        original = (JAVA / 'examples/data.json').read_bytes()
        source.write_bytes(original)
        (directory / 'sub').mkdir()
        (directory / 'symbolic.json').symlink_to(source)
        (directory / 'hard.json').hardlink_to(source)
        for output in ['input.json', str(source), 'sub/../input.json', 'symbolic.json', 'hard.json']:
            result = subprocess.run(command + ['input.json', '--run', '2', '--output', output],
                                    cwd=directory, capture_output=True, text=True)
            assert result.returncode == 64, (name, output, result.stderr)
            assert 'Выходной файл совпадает со входным' in result.stderr
            assert source.read_bytes() == original, (name, output, 'input changed')
            count += 1
        result = subprocess.run(command + ['input.json', '--run', '2', '--output', 'result.json'],
                                cwd=directory, capture_output=True, text=True)
        assert result.returncode == 0 and (directory / 'result.json').is_file()
        assert source.read_bytes() == original
        count += 1
print(f'PASS: {count} file safety checks (Python and Java)')
