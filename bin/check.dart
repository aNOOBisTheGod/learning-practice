import 'dart:convert';
import 'dart:io';

const requiredChecks = [
  'cpu',
  'memory',
  'storage',
  'network',
  'cooling',
  'power',
];

Map<String, Object> evaluate(Object? input) {
  if (input is! Map<String, dynamic>) {
    throw const FormatException('Ожидался объект JSON');
  }
  for (final field in ['order', 'serial', 'plan']) {
    if (input[field] is! String || (input[field] as String).trim().isEmpty) {
      throw FormatException('Не заполнено поле $field');
    }
  }
  if (input['configuration_matches'] is! bool ||
      input['open_defects'] is! int ||
      (input['open_defects'] as int) < 0 ||
      input['checks'] is! Map<String, dynamic>) {
    throw const FormatException(
      'Неверная конфигурация, число дефектов или checks',
    );
  }
  final checks = input['checks'] as Map<String, dynamic>;
  for (final entry in checks.entries) {
    if (!requiredChecks.contains(entry.key) ||
        !['pass', 'fail', 'pending'].contains(entry.value)) {
      throw FormatException('Неизвестная проверка или результат: ${entry.key}');
    }
  }
  final reasons = <String>[];
  if (input['configuration_matches'] == false) {
    reasons.add('Комплектация не соответствует спецификации');
  }
  if (input['open_defects'] != 0) reasons.add('Есть незакрытые дефекты');
  for (final name in requiredChecks) {
    if (checks[name] != 'pass') {
      reasons.add('$name: ${checks[name] ?? 'missing'}');
    }
  }
  return {
    'order': input['order'] as String,
    'serial': input['serial'] as String,
    'plan': input['plan'] as String,
    'ready': reasons.isEmpty,
    'reasons': reasons,
  };
}

Future<void> main(List<String> args) async {
  if (args.length != 1) {
    stderr.writeln('Использование: dart run bin/check.dart <протокол.json>');
    exitCode = 64;
    return;
  }
  try {
    final input = jsonDecode(await File(args.single).readAsString());
    final result = evaluate(input);
    stdout.writeln(const JsonEncoder.withIndent('  ').convert(result));
    if (result['ready'] == false) exitCode = 1;
  } on FormatException catch (error) {
    stderr.writeln('Ошибка входных данных: ${error.message}');
    exitCode = 64;
  } on FileSystemException catch (error) {
    stderr.writeln('Не удалось прочитать файл: ${error.message}');
    exitCode = 64;
  }
}
