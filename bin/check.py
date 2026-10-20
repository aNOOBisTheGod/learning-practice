import json
import sys
from pathlib import Path


REQUIRED_CHECKS = ('cpu', 'memory', 'storage', 'network', 'cooling', 'power')


def evaluate(data):
    if not isinstance(data, dict):
        raise ValueError('Ожидался объект JSON')
    for field in ('order', 'serial', 'plan'):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f'Не заполнено поле {field}')
    if (type(data.get('configuration_matches')) is not bool
            or type(data.get('open_defects')) is not int
            or data['open_defects'] < 0
            or not isinstance(data.get('checks'), dict)):
        raise ValueError('Неверная конфигурация, число дефектов или checks')
    checks = data['checks']
    for name, status in checks.items():
        if name not in REQUIRED_CHECKS or status not in ('pass', 'fail', 'pending'):
            raise ValueError(f'Неизвестная проверка или результат: {name}')
    reasons = []
    if not data['configuration_matches']:
        reasons.append('Комплектация не соответствует спецификации')
    if data['open_defects']:
        reasons.append('Есть незакрытые дефекты')
    for name in REQUIRED_CHECKS:
        if checks.get(name) != 'pass':
            reasons.append(f'{name}: {checks.get(name, "missing")}')
    return {**{field: data[field] for field in ('order', 'serial', 'plan')},
            'ready': not reasons, 'reasons': reasons}


def reject_constant(value):
    raise ValueError(f'Недопустимое значение JSON: {value}')


def main(args):
    if len(args) != 1:
        print('Использование: python3 bin/check.py <протокол.json>', file=sys.stderr)
        return 64
    try:
        data = json.loads(Path(args[0]).read_text(encoding='utf-8'),
                          parse_constant=reject_constant)
        result = evaluate(data)
    except (ValueError, UnicodeError) as error:
        print(f'Ошибка входных данных: {error}', file=sys.stderr)
        return 64
    except OSError as error:
        print(f'Не удалось прочитать файл: {error}', file=sys.stderr)
        return 64
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
