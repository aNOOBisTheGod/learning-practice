"""Учёт комплектации и приёмочных испытаний. Python 3.12+, стандартная библиотека."""

import argparse
import json
import sys
from pathlib import Path


def schema():
    """Поля логической модели; неизменяемых глобальных данных также не требуется."""
    return {
        'orders': ('id', 'number', 'purpose', 'spec_version', 'server_serial'),
        'models': ('id', 'kind', 'name'),
        'spec_items': ('order_id', 'model_id', 'quantity'),
        'plans': ('id', 'version'),
        'tests': ('id', 'code', 'name'),
        'plan_tests': ('plan_id', 'test_id'),
        'runs': ('id', 'order_id', 'plan_id', 'number', 'engineer', 'bios', 'bmc'),
        'components': ('id', 'serial', 'model_id'),
        'run_components': ('run_id', 'component_id'),
        'results': ('run_id', 'test_id', 'status', 'log_ref', 'parameters', 'performed_at'),
        'defects': ('id', 'run_id', 'description', 'status'),
    }


def unique(rows, fields, table):
    seen = set()
    for row in rows:
        key = tuple(row[field] for field in fields)
        if key in seen:
            raise ValueError(f'{table}: повторяется ключ {key}')
        seen.add(key)


def validate_data(data):
    """Проверка структуры, ключей, ссылок и правил предметной области до расчёта."""
    definitions = schema()
    if not isinstance(data, dict) or set(data) != set(definitions):
        raise ValueError('Нужен объект JSON с одиннадцатью наборами сущностей из README')
    for table, fields in definitions.items():
        rows = data[table]
        if not isinstance(rows, list):
            raise ValueError(f'{table}: нужен список')
        for row in rows:
            if not isinstance(row, dict) or set(row) != set(fields):
                raise ValueError(f'{table}: неверный набор полей')
            for field, value in row.items():
                integer = field == 'id' or field.endswith('_id') or field == 'quantity'
                integer = integer or (table == 'runs' and field == 'number')
                if integer:
                    if type(value) is not int or value <= 0:
                        raise ValueError(f'{table}.{field}: нужно целое положительное число')
                elif not isinstance(value, str):
                    raise ValueError(f'{table}.{field}: нужна строка')
                elif field not in ('log_ref', 'performed_at') and not value.strip():
                    raise ValueError(f'{table}.{field}: пустое значение')
    keys = {
        'orders': ('id',), 'models': ('id',), 'spec_items': ('order_id', 'model_id'),
        'plans': ('id',), 'tests': ('id',), 'plan_tests': ('plan_id', 'test_id'),
        'runs': ('id',), 'components': ('id',),
        'run_components': ('run_id', 'component_id'),
        'results': ('run_id', 'test_id'), 'defects': ('id',),
    }
    for table, fields in keys.items():
        unique(data[table], fields, table)
    for table, fields in (
        ('orders', ('number',)), ('orders', ('server_serial',)),
        ('models', ('kind', 'name')), ('plans', ('version',)),
        ('tests', ('code',)), ('runs', ('order_id', 'number')),
        ('components', ('model_id', 'serial')),
    ):
        unique(data[table], fields, table)
    refs = (
        ('spec_items', 'order_id', 'orders'), ('spec_items', 'model_id', 'models'),
        ('plan_tests', 'plan_id', 'plans'), ('plan_tests', 'test_id', 'tests'),
        ('runs', 'order_id', 'orders'), ('runs', 'plan_id', 'plans'),
        ('components', 'model_id', 'models'),
        ('run_components', 'run_id', 'runs'), ('run_components', 'component_id', 'components'),
        ('results', 'run_id', 'runs'), ('results', 'test_id', 'tests'),
        ('defects', 'run_id', 'runs'),
    )
    for table, field, target in refs:
        ids = {row['id'] for row in data[target]}
        for row in data[table]:
            if row[field] not in ids:
                raise ValueError(f'{table}.{field}: отсутствует связанная запись')
    plans = {(row['plan_id'], row['test_id']) for row in data['plan_tests']}
    runs = {row['id']: row for row in data['runs']}
    for row in data['results']:
        if row['status'] not in ('pass', 'fail', 'pending'):
            raise ValueError('results.status: допустимы pass, fail, pending')
        if (runs[row['run_id']]['plan_id'], row['test_id']) not in plans:
            raise ValueError('Результат относится к тесту вне плана своего прогона')
    for row in data['defects']:
        if row['status'] not in ('open', 'closed'):
            raise ValueError('defects.status: допустимы open, closed')
    for order in data['orders']:
        if not any(row['order_id'] == order['id'] for row in data['spec_items']):
            raise ValueError('У заявки нет спецификации')
    for plan in data['plans']:
        if not any(row['plan_id'] == plan['id'] for row in data['plan_tests']):
            raise ValueError('План не может быть пустым')
    return data


def check_configuration(spec_items, components):
    """Алгоритм 1: сравнить модели и количества, выявить лишние компоненты."""
    issues = []
    matched = [False] * len(components)
    for item in spec_items:
        actual = 0
        for j, component in enumerate(components):
            if component['model_id'] == item['model_id']:
                actual += 1
                matched[j] = True
        if actual != item['quantity']:
            issues.append(
                f"Модель {item['model_id']}: нужно {item['quantity']}, "
                f"найдено {actual}")
    for j, component in enumerate(components):
        if not matched[j]:
            issues.append(f"Лишний компонент: {component['serial']}")
    return issues


def evaluate_protocol(results, required_count, defects, configuration_issues):
    """Алгоритм 2. Вход прошёл validate_data; результаты одного прогона уникальны."""
    reasons = list(configuration_issues)
    for result in results:
        if result['status'] != 'pass':
            reasons.append(f"Тест {result['test_id']}: {result['status']}")
        if not result['log_ref'].strip() or not result['performed_at'].strip():
            reasons.append(f"Тест {result['test_id']}: нет журнала или времени")
    missing = required_count - len(results)
    if missing > 0:
        reasons.append(f'Пропущено обязательных тестов: {missing}')
    for defect in defects:
        if defect['status'] == 'open':
            reasons.append(
                f"Открыт дефект {defect['id']}: {defect['description']}")
    return {'ready': not reasons, 'reasons': reasons}


def build_protocol(data, run_id):
    """Сформировать протокол из связанных сущностей, не изменяя историю."""
    validate_data(data)
    run = next((row for row in data['runs'] if row['id'] == run_id), None)
    if run is None:
        raise ValueError(f'Не найден прогон {run_id}')
    order = next(row for row in data['orders'] if row['id'] == run['order_id'])
    plan = next(row for row in data['plans'] if row['id'] == run['plan_id'])
    specification = [row for row in data['spec_items'] if row['order_id'] == order['id']]
    component_ids = {row['component_id'] for row in data['run_components'] if row['run_id'] == run_id}
    components = [row for row in data['components'] if row['id'] in component_ids]
    results = [row for row in data['results'] if row['run_id'] == run_id]
    # Открытый дефект прежнего прогона того же изделия также блокирует приёмку.
    order_run_ids = {row['id'] for row in data['runs'] if row['order_id'] == order['id']}
    defects = [row for row in data['defects'] if row['run_id'] in order_run_ids]
    required = [row for row in data['plan_tests'] if row['plan_id'] == plan['id']]
    issues = check_configuration(specification, components)
    decision = evaluate_protocol(results, len(required), defects, issues)
    return {
        'order': order['number'], 'serial': order['server_serial'],
        'spec_version': order['spec_version'], 'plan': plan['version'],
        'run_id': run_id, 'run_number': run['number'], 'engineer': run['engineer'],
        'bios': run['bios'], 'bmc': run['bmc'],
        'configuration': components, 'results': results, 'defects': defects,
        **decision,
    }


def reject_constant(value):
    raise ValueError(f'Недопустимая константа JSON: {value}')


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Повторяющееся поле JSON: {key}')
        result[key] = value
    return result


def main(argv):
    parser = argparse.ArgumentParser(description='Проверить комплектацию и сформировать протокол')
    parser.add_argument('data', type=Path, help='JSON с сущностями логической модели')
    parser.add_argument('--run', type=int, required=True, help='Идентификатор прогона')
    parser.add_argument('--output', type=Path, help='Сохранить полный протокол в JSON')
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.data.read_text(encoding='utf-8'),
                          parse_constant=reject_constant, object_pairs_hook=unique_json_object)
        protocol = build_protocol(data, args.run)
        if args.output:
            args.output.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (ValueError, OSError, UnicodeError) as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        return 64
    print(f"Заявка: {protocol['order']}; сервер: {protocol['serial']}; прогон: {protocol['run_number']}")
    print(f"Спецификация: {protocol['spec_version']}; план: {protocol['plan']}")
    print('Предварительный допуск: ' + ('ДА' if protocol['ready'] else 'НЕТ'))
    for reason in protocol['reasons']:
        print('- ' + reason)
    return 0 if protocol['ready'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
