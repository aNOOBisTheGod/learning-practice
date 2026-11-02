"""Проверки без сторонних библиотек и собственных классов: python3 test_main.py."""

import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from main import build_protocol, check_configuration, evaluate_protocol, validate_data


def fixture():
    return json.loads((Path(__file__).parent / 'examples/data.json').read_text(encoding='utf-8'))


def must_reject(data):
    try:
        validate_data(data)
    except ValueError:
        return
    raise AssertionError('Ошибочные данные приняты')


def test_success_and_history():
    data = fixture()
    before = copy.deepcopy(data)
    assert build_protocol(data, 2)['ready']
    assert not build_protocol(data, 1)['ready']
    assert data == before
    early = fixture()
    early['runs'] = [early['runs'][0]]
    early['runs'][0].update(bios='не определено', bmc='не определено')
    early['run_components'] = []
    early['results'] = []
    early['defects'][0].update(status='open', description='Деталь не соответствует документации')
    protocol = build_protocol(early, 1)
    assert not protocol['ready']
    assert any('Открыт дефект' in reason for reason in protocol['reasons'])
    assert any('Пропущено обязательных тестов: 6' == reason for reason in protocol['reasons'])


def test_configuration():
    spec = [{'model_id': 1, 'quantity': 2}, {'model_id': 2, 'quantity': 1}]
    good = [{'model_id': 1, 'serial': 'a'}, {'model_id': 1, 'serial': 'b'}, {'model_id': 2, 'serial': 'c'}]
    assert check_configuration(spec, good) == []
    assert len(check_configuration(spec, good[:1])) == 2
    assert 'Лишний' in check_configuration(spec, good + [{'model_id': 3, 'serial': 'd'}])[-1]
    assert len(check_configuration(spec, [])) == 2
    assert len(check_configuration([], good)) == 3
    assert check_configuration([], []) == []
    assert 'найдено 3' in check_configuration(spec, good + [good[0]])[0]


def test_missing_failed_pending_and_logs():
    for status in ('fail', 'pending'):
        data = fixture()
        data['results'][-1]['status'] = status
        assert not build_protocol(data, 2)['ready']
    data = fixture()
    data['results'].pop()
    assert build_protocol(data, 2)['reasons'] == ['Пропущено обязательных тестов: 1']
    data = fixture()
    data['results'] = [r for r in data['results'] if r['run_id'] != 2]
    assert '6' in build_protocol(data, 2)['reasons'][0]
    for field in ('log_ref', 'performed_at'):
        data = fixture()
        data['results'][-1][field] = '   '
        assert not build_protocol(data, 2)['ready']


def test_previous_open_defect_blocks():
    data = fixture()
    data['defects'][0]['status'] = 'open'
    assert not build_protocol(data, 2)['ready']
    data['defects'][0]['status'] = 'closed'
    assert build_protocol(data, 2)['ready']


def test_validation():
    for table in ('orders', 'models', 'spec_items', 'plans', 'tests', 'plan_tests',
                  'runs', 'components', 'run_components', 'results', 'defects'):
        data = fixture()
        data[table].append(copy.deepcopy(data[table][0]))
        must_reject(data)
    for table, field in (('spec_items', 'model_id'), ('runs', 'order_id'),
                         ('run_components', 'component_id'), ('results', 'run_id'),
                         ('defects', 'run_id')):
        data = fixture()
        data[table][0][field] = 999
        must_reject(data)
    for value in (True, 0, -1, '2', 1.5):
        data = fixture()
        data['spec_items'][0]['quantity'] = value
        must_reject(data)
    for value in ('unknown', '', None, []):
        data = fixture()
        data['results'][0]['status'] = value
        must_reject(data)
    data = fixture()
    data['plan_tests'] = []
    must_reject(data)
    data = fixture()
    data['spec_items'] = []
    must_reject(data)
    for value in ([], {}, {'orders': None}):
        must_reject(value)
    data = fixture()
    data['plan_tests'].pop()
    must_reject(data)  # Результат существующего теста, но вне плана.


def test_other_order_isolation():
    data = fixture()
    data['orders'].append({**data['orders'][0], 'id': 2, 'number': 'REQ-002', 'server_serial': 'SRV-002'})
    data['spec_items'].append({'order_id': 2, 'model_id': 1, 'quantity': 1})
    data['runs'].append({**data['runs'][0], 'id': 3, 'order_id': 2})
    data['defects'].append({'id': 2, 'run_id': 3, 'description': 'Чужой дефект', 'status': 'open'})
    assert build_protocol(data, 2)['ready']


def test_full_report_and_snapshot():
    data = fixture()
    data['run_components'] = [r for r in data['run_components'] if not (r['run_id'] == 2 and r['component_id'] == 3)]
    first = build_protocol(data, 1)
    second = build_protocol(data, 2)
    assert len(first['configuration']) == 4
    assert len(second['configuration']) == 3
    assert any('Модель 2' in r for r in second['reasons'])
    assert all(key in second for key in ('results', 'defects', 'bios', 'bmc', 'engineer', 'plan'))
    try:
        build_protocol(data, 999)
    except ValueError:
        pass
    else:
        raise AssertionError('Несуществующий прогон принят')


def test_all_reasons():
    result = evaluate_protocol(
        [{'test_id': 1, 'status': 'fail', 'log_ref': '', 'performed_at': ''}], 2,
        [{'id': 1, 'status': 'open', 'description': 'Дефект'}], ['Состав неверен'])
    assert not result['ready'] and len(result['reasons']) == 5


def test_cli():
    root = Path(__file__).parent.resolve()
    def run(*args):
        return subprocess.run([sys.executable, str(root / 'main.py'), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        out = folder / 'protocol.json'
        ok = run(root / 'examples/data.json', '--run', 2, '--output', out)
        assert ok.returncode == 0 and 'допуск: ДА' in ok.stdout
        assert json.loads(out.read_text())['run_id'] == 2
        assert run(root / 'examples/data.json', '--run', 1).returncode == 1
        assert run(root / 'examples/data.json', '--run', 999).returncode == 64
        assert run(folder / 'absent.json', '--run', 1).returncode == 64
        assert run().returncode == 2
        for text in ('{', '{"orders": NaN}', '{"orders": [], "orders": []}', '[]'):
            bad = folder / 'bad.json'
            bad.write_text(text)
            assert run(bad, '--run', 1).returncode == 64


def test_procedural_style():
    for path in Path(__file__).parent.glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        assert not any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
        assert not any(isinstance(node, ast.Global) for node in ast.walk(tree))


def main():
    tests = (test_success_and_history, test_configuration, test_missing_failed_pending_and_logs,
             test_previous_open_defect_blocks, test_validation, test_other_order_isolation,
             test_full_report_and_snapshot, test_all_reasons, test_cli, test_procedural_style)
    for test in tests:
        test()
        print('OK', test.__name__)
    print(f'Пройдено: {len(tests)} групп проверок')


if __name__ == '__main__':
    main()
