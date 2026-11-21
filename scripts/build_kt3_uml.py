"""Build a UML class diagram from compiled signatures and explicit domain relations."""
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'kt3/src/java'
OUT=ROOT/'kt3/models'

def simplified(text):
    for prefix in ['java.lang.','java.util.','java.math.','java.io.','practice.model.','practice.rules.','practice.io.','practice.service.','practice.']:
        text=text.replace(prefix,'')
    return text.replace('Map<String, List<Map<String, Object>>>','Rows').replace('Map<String, Object>','JsonObject')

def member(line,name):
    line=simplified(line.strip().rstrip(';'))
    if not line or line in ('{','}') or line.startswith('Compiled from') or '{' in line or 'lambda$' in line:return None
    visibility='+' if line.startswith('public ') else '#' if line.startswith('protected ') else '-'
    static='{static} ' if ' static ' in ' '+line else ''
    abstract='{abstract} ' if ' abstract ' in ' '+line else ''
    clean=re.sub(r'\b(public|private|protected|static|final|abstract)\s+','',line)
    if '(' in clean:
        before,params=clean.split('(',1)
        params=params.rstrip(')')
        # Compiler-generated Object methods are common to all records.
        if any(before.endswith(' '+n) for n in ('toString','hashCode','equals')):return None
        parts=before.rsplit(' ',1)
        if len(parts)==1:return None # constructors described in legend, omit long signatures
        typ,method=parts
        return f'  {visibility}{static}{abstract}{method}({params}) : {typ}'
    typ,field=clean.rsplit(' ',1)
    return f'  {visibility}{static}{field} : {typ}'

packages={}
for path in sorted((JAVA/'src').rglob('*.java')):
    fq='.'.join(path.relative_to(JAVA/'src').with_suffix('').parts)
    package=fq.rsplit('.',1)[0];name=path.stem
    sig=subprocess.check_output(['javap','-private','-cp',str(JAVA/'out'),fq],text=True)
    kind='interface' if 'public interface ' in sig else 'abstract class' if 'public abstract class ' in sig else 'class'
    stereotype=' <<record>>' if 'extends java.lang.Record' in sig else ''
    members=[m for line in sig.splitlines() if (m:=member(line,name))]
    fields=[m for m in members if '(' not in m]; methods=[m for m in members if '(' in m]
    block=f'{kind} {name}{stereotype} {{\n'+'\n'.join(fields)+'\n--\n'+'\n'.join(methods)+'\n}'
    packages.setdefault(package,[]).append(block)
header='''@startuml classes
!pragma layout smetana
skinparam backgroundColor white
skinparam shadowing false
skinparam classAttributeIconSize 0
skinparam defaultFontName Arial
skinparam defaultFontSize 14
skinparam packageStyle rectangle
skinparam linetype polyline
skinparam nodesep 45
skinparam ranksep 60
skinparam dpi 130
hide empty members
title
КТ3 — учёт сборки и приёмочных испытаний сервера
Классы реализации Java 17
endtitle
'''
text=header
for package,blocks in packages.items():
    text+=f'package "{package}" {{\n'+'\n'.join(blocks)+'\n}\n'
text+='''
AcceptanceRule <|.. AbstractAcceptanceRule
AbstractAcceptanceRule <|-- ConfigurationRule
AbstractAcceptanceRule <|-- ProtocolRule
ProtocolService "0..*" o-- "1..*" AcceptanceRule : rules
ProtocolService "0..*" --> "1" DataSet : data
ProtocolService ..> RunContext : context()
Main ..> ProtocolService : creates
Main ..> Json : JSON I/O
Main ..> DataSet : creates
Main ..> ConfigurationRule : creates
Main ..> ProtocolRule : creates
DataSet ..> DataValidator : validate()
ProtocolRule ..> Json : blank()
AcceptanceRule ..> RunContext : check(context)
RunContext "0..*" --> "1" Order : order
RunContext "0..*" --> "1" TestPlan : plan
RunContext "0..*" --> "1" TestRun : run
RunContext "0..*" o-- "0..*" SpecificationItem : specification
RunContext "0..*" o-- "0..*" Component : components
RunContext "0..*" o-- "0..*" TestResult : results
RunContext "0..*" o-- "0..*" Defect : defects
Order "1" -- "1..*" SpecificationItem : order_id
ComponentModel "1" -- "0..*" SpecificationItem : model_id
Order "1" -- "0..*" TestRun : order_id
TestPlan "1" -- "0..*" TestRun : plan_id
TestPlan "1" -- "1..*" PlanTest : plan_id
TestDefinition "1" -- "0..*" PlanTest : test_id
ComponentModel "1" -- "0..*" Component : model_id
TestRun "1" -- "0..*" RunComponent : run_id
Component "1" -- "0..*" RunComponent : component_id
TestRun "1" -- "0..*" TestResult : run_id
TestDefinition "1" -- "0..*" TestResult : test_id
TestRun "1" -- "0..*" Defect : run_id
legend bottom left
  + public; - private; # protected; подчёркивание = static
  Полый треугольник: наследование; пунктир с треугольником: реализация интерфейса.
  Полый ромб: агрегация. Правила и сущности могут существовать вне сервиса/контекста.
  Ассоциации с *_id разрешаются по ключам в DataSet/ProtocolService; это не поля-ссылки Java.
  DataSet хранит 11 типизированных List, перечисленных в атрибутах; линии к каждому списку опущены.
  Record: поля private final, публичные аксессоры; конструкторы и стандартные Object-методы опущены.
  JsonObject = Map<String, Object>; Rows = Map<String, List<Map<String, Object>>>.
  Тестовый SelfTest не входит в структуру производственного приложения.
endlegend
@enduml
'''
(OUT/'classes.puml').write_text(text,encoding='utf-8')
subprocess.run(['plantuml','-charset','UTF-8','-tpng',str(OUT/'classes.puml')],check=True)
print('Generated',OUT/'classes.png')
