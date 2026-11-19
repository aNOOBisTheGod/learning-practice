"""Generate explicit immutable Java entities from the unchanged KT2 schema."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kt2/src'))
from main import schema
names=dict(zip(schema(),['Order','ComponentModel','SpecificationItem','TestPlan','TestDefinition','PlanTest','TestRun','Component','RunComponent','TestResult','Defect']))
def typ(t,f):return 'BigInteger' if f=='id' or f.endswith('_id') or f=='quantity' or (t=='runs' and f=='number') else 'String'
base=ROOT/'kt3/src/java/src/practice/model'
base.mkdir(parents=True, exist_ok=True)
(ROOT/'tmp/kt3').mkdir(parents=True, exist_ok=True)
for table,fields in schema().items():
    name=names[table]
    args=', '.join(f'{typ(table,f)} {f}' for f in fields)
    lines=['package practice.model;','','import java.math.BigInteger;','import java.util.LinkedHashMap;','import java.util.Map;','',f'/** Immutable row of {table}; references retain the keys of KT2. */',f'public record {name}({args}) {{','    public Map<String, Object> toMap() {','        Map<String, Object> row = new LinkedHashMap<>();']
    lines += [f'        row.put("{f}", {f});' for f in fields]
    lines += ['        return row;','    }','}']
    (base/f'{name}.java').write_text('\n'.join(lines)+'\n')
lines=['package practice.model;','','import java.math.BigInteger;','import java.util.*;','import practice.io.DataValidator;','','/** Validated snapshot. Collections cannot be modified through this API. */','public final class DataSet {']
for table,name in names.items():lines.append(f'    private final List<{name}> {table};')
lines += ['','    public DataSet(Object input) {','        Map<String, List<Map<String, Object>>> data = new DataValidator().validate(input);']
for table,fields in schema().items():
    args=', '.join(f'({typ(table,f)}) row.get("{f}")' for f in fields)
    lines.append(f'        {table} = data.get("{table}").stream().map(row -> new {names[table]}({args})).toList();')
lines += ['    }']
for table,name in names.items():lines.append(f'    public List<{name}> {table}() {{ return {table}; }}')
lines+=['}']
(base/'DataSet.java').write_text('\n'.join(lines)+'\n')
# Machine-readable schema for the boundary validator (not a runtime dependency).
lines=['    private Map<String, List<String>> schema() {','        Map<String, List<String>> fields = new LinkedHashMap<>();']
for table,fields in schema().items():lines.append(f'        fields.put("{table}", List.of('+', '.join('"'+f+'"' for f in fields)+'));')
lines+=['        return fields;','    }']
(ROOT/'tmp/kt3/schema_java.txt').write_text('\n'.join(lines))
