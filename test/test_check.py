import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    'Python': [sys.executable, str(ROOT / 'bin/check.py')],
    'Java': ['java', '-jar', str(ROOT / 'java/target/protocol-check.jar')],
}


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.sample = json.loads((ROOT / 'examples/protocol.json').read_text())

    def run_case(self, content, code, reasons=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'protocol.json'
            path.write_bytes(content)
            for language, command in COMMANDS.items():
                with self.subTest(language=language):
                    result = subprocess.run(command + [str(path)], capture_output=True)
                    self.assertEqual(result.returncode, code, result.stderr.decode())
                    if code == 64:
                        self.assertFalse(result.stdout)
                        self.assertTrue(result.stderr)
                    else:
                        self.assertFalse(result.stderr)
                        self.assertEqual(json.loads(result.stdout), {
                            'order': self.sample['order'],
                            'serial': self.sample['serial'],
                            'plan': self.sample['plan'],
                            'ready': code == 0, 'reasons': reasons,
                        })

    def check_data(self, data, code, reasons=None):
        self.run_case(json.dumps(data, ensure_ascii=False).encode(), code, reasons)

    def test_ready(self):
        self.check_data(self.sample, 0, [])

    def test_failed_pending_missing(self):
        for status in ('fail', 'pending', None):
            data = copy.deepcopy(self.sample)
            if status is None:
                del data['checks']['memory']
            else:
                data['checks']['memory'] = status
            with self.subTest(status=status):
                self.check_data(data, 1, [f'memory: {status or "missing"}'])

    def test_combined_reasons(self):
        data = {**self.sample, 'configuration_matches': False,
                'open_defects': 2, 'checks': {'cpu': 'fail'}}
        self.check_data(data, 1, [
            'Комплектация не соответствует спецификации',
            'Есть незакрытые дефекты', 'cpu: fail', 'memory: missing',
            'storage: missing', 'network: missing', 'cooling: missing', 'power: missing',
        ])

    def test_invalid_schema(self):
        invalid = [None, [], {}, {**self.sample, 'checks': {'cpu': 'ok'}},
                   {**self.sample, 'checks': {'gpu': 'pass'}}]
        for field, values in {
            'order': [None, 1, ''], 'serial': [' ', '\u00a0'], 'plan': [False],
            'configuration_matches': [None, 1, 'true'],
            'open_defects': [-1, True, 0.0, '0', None],
            'checks': [None, [], {'cpu': None}, {'cpu': []}],
        }.items():
            invalid.extend({**self.sample, field: value} for value in values)
        for data in invalid:
            with self.subTest(data=data):
                self.check_data(data, 64)

    def test_invalid_json(self):
        for content in (b'', b'{', b'{} {}', b'{"x":NaN}', b'{"x":1,}',
                        b'{/* comment */}', b'\xff'):
            with self.subTest(content=content):
                self.run_case(content, 64)

    def test_unicode(self):
        self.sample['order'] = 'Заказ-001'
        self.check_data(self.sample, 0, [])

    def test_usage_and_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            for language, command in COMMANDS.items():
                for args in ([], ['a', 'b'], [str(Path(folder) / 'missing.json')]):
                    with self.subTest(language=language, args=args):
                        result = subprocess.run(command + args, capture_output=True)
                        self.assertEqual(result.returncode, 64)
                        self.assertFalse(result.stdout)
                        self.assertTrue(result.stderr)


if __name__ == '__main__':
    unittest.main()
