"""Compare KT2 Python and KT3 Java on the same JSON, including entire protocols."""
import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kt2/src'))
from main import build_protocol, schema
JAVA=ROOT/'kt3/src/java'

def main():
    subprocess.run(['sh',str(JAVA/'build.sh')],check=True)
    base=json.loads((JAVA/'examples/data.json').read_text())
    cases=[]
    def add(name,edit=None,run=2):
        data=copy.deepcopy(base)
        if edit:edit(data)
        cases.append((name,data,run))
    add('pass');add('historical_fail',run=1);add('unknown_run',run=999)
    for status in ('fail','pending','unknown','',None):
        add('status_'+str(status),lambda d,s=status:d['results'][-1].update(status=s))
    for value in ('', '   ', '\u00a0', '\u0085', '\u2003', '\t\n'):
        for field in ('log_ref','performed_at'):
            add('blank_'+field+'_'+repr(value),lambda d,f=field,v=value:d['results'][-1].update({f:v}))
    add('missing_test',lambda d:d['results'].pop())
    add('missing_all_tests',lambda d:d.update(results=[r for r in d['results'] if r['run_id']!=2]))
    add('old_open_defect',lambda d:d['defects'][0].update(status='open'))
    add('defect_bad_status',lambda d:d['defects'][0].update(status='bad'))
    add('incomplete_configuration',lambda d:d['run_components'].pop())
    add('empty_configuration',lambda d:d.update(run_components=[]))
    add('deficit',lambda d:d['spec_items'][0].update(quantity=20))
    add('excess',lambda d:d['spec_items'][1].update(quantity=1))
    add('extra_model',lambda d:d['spec_items'].pop())
    add('huge_quantity',lambda d:d['spec_items'][0].update(quantity=10**40))
    for table in schema():
        add('duplicate_'+table,lambda d,t=table:d[t].append(copy.deepcopy(d[t][0])))
        add('missing_field_'+table,lambda d,t=table:d[t][0].pop(next(iter(d[t][0]))))
        add('extra_field_'+table,lambda d,t=table:d[t][0].update(extra=1))
        add('not_list_'+table,lambda d,t=table:d.update({t:{}}))
    for table,field in [('spec_items','model_id'),('spec_items','order_id'),('plan_tests','plan_id'),('plan_tests','test_id'),('runs','order_id'),('runs','plan_id'),('components','model_id'),('run_components','run_id'),('run_components','component_id'),('results','run_id'),('results','test_id'),('defects','run_id')]:
        add('broken_fk_'+table+field,lambda d,t=table,f=field:d[t][0].update({f:999}))
    for value in (True,False,0,-1,'2',1.5,None,[],{}):
        add('bad_quantity_'+repr(value),lambda d,v=value:d['spec_items'][0].update(quantity=v))
    for table,fields in [('orders',['number']),('orders',['server_serial']),('models',['kind','name']),('plans',['version']),('tests',['code']),('runs',['order_id','number']),('components',['model_id','serial'])]:
        def duplicate_ak(d,t=table,fs=fields):
            r=copy.deepcopy(d[t][0]);r['id']=999
            d[t].append(r)
        add('alternate_key_'+table+str(fields),duplicate_ak)
    add('empty_spec',lambda d:d.update(spec_items=[]))
    add('empty_plan',lambda d:d.update(plan_tests=[]))
    add('result_outside_plan',lambda d:d['plan_tests'].pop())
    def early(d):
        d['runs']=d['runs'][:1];d['runs'][0].update(bios='не определено',bmc='не определено')
        d['run_components']=[];d['results']=[];d['defects'][0]['status']='open'
    add('early_refusal',early,1)
    def other_order(d):
        d['orders'].append({**d['orders'][0],'id':2,'number':'REQ-002','server_serial':'SRV-002'})
        d['spec_items'].append({'order_id':2,'model_id':1,'quantity':1})
        d['runs'].append({**d['runs'][0],'id':3,'order_id':2})
        d['defects'].append({'id':2,'run_id':3,'description':'Чужой дефект','status':'open'})
    add('other_order_isolation',other_order)
    def huge_ids(d):
        for table,rows in d.items():
            for row in rows:
                for f in row:
                    if f=='id' or f.endswith('_id'):row[f]+=10**30
    add('big_integer_ids',huge_ids,10**30+2)
    add('unicode_roundtrip',lambda d:d['runs'][1].update(engineer='Иван 😀\n"\\'))
    rng=random.Random(20261121)
    for i in range(30):
        def mutate(d):
            d['results']=[r for r in d['results'] if r['run_id']==1 or rng.random()>.3]
            for row in d['results']:
                row['status']=rng.choice(['pass','fail','pending'])
                row['log_ref']=rng.choice(['test.log','','\u00a0'])
            for row in d['spec_items']:row['quantity']=rng.randint(1,5)
            d['defects'][0]['status']=rng.choice(['open','closed'])
        add('seeded_'+str(i),mutate)
    result_rows=[]
    with tempfile.TemporaryDirectory(prefix='kt3-parity-') as directory:
        folder=Path(directory);input_path=folder/'data.json';output=folder/'result.json'
        def java(*args):
            return subprocess.run(['java','-cp',str(JAVA/'out'),'practice.Main',*map(str,args)],capture_output=True,text=True,encoding='utf-8')
        for name,data,run in cases:
            input_path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            before=copy.deepcopy(data)
            try: expected=build_protocol(data,run)
            except ValueError:expected=None
            got=java(input_path,'--run',run,'--output',output)
            if expected is None:
                assert got.returncode==64,(name,got.returncode,got.stderr)
            else:
                assert got.returncode==(0 if expected['ready'] else 1),(name,got.stderr)
                actual=json.loads(output.read_text(encoding='utf-8'))
                assert actual==expected,(name,actual,expected)
                py=subprocess.run([sys.executable,str(ROOT/'kt2/src/main.py'),str(input_path),'--run',str(run)],capture_output=True,text=True,encoding='utf-8')
                assert py.stdout==got.stdout,(name,py.stdout,got.stdout)
            assert data==before,name
            result_rows.append({'case':name,'exit_code':got.returncode,'match':True})
        malformed=['{','[]','null','{"orders":NaN}','{"orders":[],"orders":[]}', '{"x":01}', '{"x":1.}', '{"x":1e}', '{"x":"\\q"}', '{"x":"\\uZZZZ"}', '{"x":"\n"}']
        for i,text in enumerate(malformed):
            input_path.write_text(text,encoding='utf-8')
            got=java(input_path,'--run',2)
            py=subprocess.run([sys.executable,str(ROOT/'kt2/src/main.py'),str(input_path),'--run','2'],capture_output=True)
            assert got.returncode==py.returncode==64,(text,got.stderr)
            result_rows.append({'case':'malformed_'+str(i),'exit_code':64,'match':True})
        for args,code in [((),2),(('--run',),2),((input_path,'--run','x'),2),((input_path,'--run','0'),64),((folder/'absent','--run','2'),64),(('--help',),0)]:
            assert java(*args).returncode==code,args
        # Bad UTF-8 must not be silently replaced.
        input_path.write_bytes(b'\xff')
        assert java(input_path,'--run',2).returncode==64
    report={'comparison':'full JSON and stdout for valid data; exit codes for invalid data','cases':len(result_rows),'cli_checks':7,'results':result_rows}
    (ROOT/'docs/kt3/parity_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'PASS: {len(result_rows)} differential cases; 7 additional CLI checks')

if __name__=='__main__':main()
