"""Reproducible source counts; physical lines include blanks and comments."""
import ast
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'kt2/src/main.py'
files=sorted((ROOT/'kt3/src/java/src').rglob('*.java'))
metrics={
    'python': {'production_files':1, 'functions':sum(isinstance(n,ast.FunctionDef) for n in ast.walk(ast.parse(source.read_text()))), 'classes':0, 'lines':len(source.read_text().splitlines())},
    'java': {'production_files':len(files), 'types':len(files), 'records':sum('public record ' in p.read_text() for p in files), 'interfaces':sum('public interface ' in p.read_text() for p in files), 'classes':sum(bool(re.search(r'public (?:final |abstract )?class ',p.read_text())) for p in files), 'lines':sum(len(p.read_text().splitlines()) for p in files)}
}
(ROOT/'docs/kt3/code_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(metrics,ensure_ascii=False))
