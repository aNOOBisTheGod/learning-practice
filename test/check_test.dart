import 'dart:convert';
import 'dart:io';

import '../bin/check.dart';

void require(bool condition) {
  if (!condition) throw StateError('Проверка не пройдена');
}

void main() {
  Map<String, dynamic> sample() =>
      jsonDecode(File('examples/protocol.json').readAsStringSync())
          as Map<String, dynamic>;
  require(evaluate(sample())['ready'] == true);
  for (final status in ['fail', 'pending', null]) {
    final data = sample();
    if (status == null) {
      (data['checks'] as Map).remove('memory');
    } else {
      data['checks']['memory'] = status;
    }
    require(evaluate(data)['ready'] == false);
  }
  require(
    evaluate({...sample(), 'configuration_matches': false})['ready'] == false,
  );
  require(evaluate({...sample(), 'open_defects': 1})['ready'] == false);
  for (final bad in [
    null,
    [],
    {...sample(), 'serial': ' '},
    {...sample(), 'open_defects': -1},
    {
      ...sample(),
      'checks': {'cpu': 'ok'},
    },
  ]) {
    var rejected = false;
    try {
      evaluate(bad);
    } on FormatException {
      rejected = true;
    }
    require(rejected);
  }
  print('Проверки пройдены');
}
