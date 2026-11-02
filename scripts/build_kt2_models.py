"""Воспроизводимые BPMN 2.0 / draw.io и PNG из общих координат."""
from pathlib import Path
import math
import textwrap
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'kt2/models'
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'


def canvas(width, height):
    im = Image.new('RGB', (width * 2, height * 2), 'white')
    return im, ImageDraw.Draw(im)


def label(draw, text, box, size=19, align='center'):
    x,y,w,h=box
    font=ImageFont.truetype(FONT, size*2)
    lines=[]
    for line in text.split('\n'):
        words=line.split(' '); current=''
        for word in words:
            trial=(current+' '+word).strip()
            if draw.textlength(trial,font=font)>max(20,(w-12)*2) and current:
                lines.append(current); current=word
            else: current=trial
        lines.append(current)
    lh=size*2.5
    yy=y*2+(h*2-len(lines)*lh)/2
    for line in lines:
        xx=x*2+12 if align=='left' else (x+w/2)*2-draw.textlength(line,font=font)/2
        draw.text((xx,yy),line,font=font,fill='#172635')
        yy+=lh


def poly(draw, points, fill='white', width=2):
    p=[(x*2,y*2) for x,y in points]
    draw.polygon(p,fill=fill)
    draw.line(p+[p[0]],fill='#253746',width=width*2)


def shape(draw, kind, box, text='', fill='white', size=19):
    x,y,w,h=box; rect=(x*2,y*2,(x+w)*2,(y+h)*2)
    if kind in ('start','end','terminal'):
        draw.rounded_rectangle(rect,radius=min(w,h),fill=fill,outline='#253746',width=6 if kind=='end' else 3)
    elif kind=='decision': poly(draw,[(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)],fill)
    elif kind=='io': poly(draw,[(x+22,y),(x+w,y),(x+w-22,y+h),(x,y+h)],fill)
    elif kind=='loop': poly(draw,[(x+22,y),(x+w-22,y),(x+w,y+h/2),(x+w-22,y+h),(x+22,y+h),(x,y+h/2)],fill)
    elif kind=='data':
        poly(draw,[(x,y),(x+w-15,y),(x+w,y+15),(x+w,y+h),(x,y+h)],fill)
        draw.line([(2*(x+w-15),2*y),(2*(x+w-15),2*(y+15)),(2*(x+w),2*(y+15))],fill='#253746',width=3)
    elif kind=='task': draw.rounded_rectangle(rect,radius=20,fill=fill,outline='#253746',width=3)
    else: draw.rectangle(rect,fill=fill,outline='#253746',width=3)
    label(draw,text,box,size)


def edge(draw, points, text='', label_box=None, dash=False, crow=False, required=False, arrow=True):
    pts=[(x*2,y*2) for x,y in points]
    for a,b in zip(pts,pts[1:]):
        if dash:
            length=math.dist(a,b)
            for off in range(0,int(length),12):
                t=off/max(1,length); u=min(off+6,length)/max(1,length)
                draw.line([(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t),(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)],fill='#5a6a75',width=3)
        else: draw.line([a,b],fill='#334c60',width=3)
    def endmark(end, prev, many=False, one=False):
        dx=end[0]-prev[0];dy=end[1]-prev[1];length=max(1,math.hypot(dx,dy));ux=dx/length;uy=dy/length;vx=-uy;vy=ux
        if many:
            for sign in (-1,0,1):draw.line([end,(end[0]-ux*26+vx*sign*13,end[1]-uy*26+vy*sign*13)],fill='#334c60',width=3)
            cx=end[0]-ux*36;cy=end[1]-uy*36
            if required:draw.line([(cx+vx*10,cy+vy*10),(cx-vx*10,cy-vy*10)],fill='#334c60',width=3)
            else:draw.ellipse((cx-7,cy-7,cx+7,cy+7),fill='white',outline='#334c60',width=2)
        elif one:
            for back in (10,20):
                cx=end[0]-ux*back;cy=end[1]-uy*back
                draw.line([(cx+vx*10,cy+vy*10),(cx-vx*10,cy-vy*10)],fill='#334c60',width=3)
        else:
            draw.polygon([end,(end[0]-ux*17+vx*7,end[1]-uy*17+vy*7),(end[0]-ux*17-vx*7,end[1]-uy*17-vy*7)],fill='#334c60')
    if crow:
        endmark(pts[0],pts[1],one=True);endmark(pts[-1],pts[-2],many=True)
    elif arrow:endmark(pts[-1],pts[-2])
    if text:
        x,y,w,h=label_box
        draw.rectangle((x*2,y*2,(x+w)*2,(y+h)*2),fill='white')
        label(draw,text,label_box,17)


def drawio(name,title,nodes,edges,width,height,entity=False):
    root=ET.Element('mxfile',host='app.diagrams.net',version='24.7.17')
    dia=ET.SubElement(root,'diagram',id=name,name=title)
    model=ET.SubElement(dia,'mxGraphModel',dx=str(width),dy=str(height),grid='1',page='1',pageWidth=str(width),pageHeight=str(height))
    r=ET.SubElement(model,'root');ET.SubElement(r,'mxCell',id='0');ET.SubElement(r,'mxCell',id='1',parent='0')
    im,d=canvas(width,height)
    for eid,source,target,points,text,lb,*rest in edges:
        crow=bool(rest and rest[0]); req=bool(len(rest)>1 and rest[1])
        sty='edgeStyle=none;rounded=0;html=0;fontSize=17;strokeColor=#334c60;'
        sty+=('startArrow=ERone;endArrow='+('ERmany' if req else 'ERzeroToMany')+';') if crow else 'endArrow=block;'
        c=ET.SubElement(r,'mxCell',id=eid,value=text,style=sty,edge='1',parent='1',source=source,target=target)
        g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
        for pt,kind in ((points[0],'sourcePoint'),(points[-1],'targetPoint')):ET.SubElement(g,'mxPoint',x=str(pt[0]),y=str(pt[1]),**{'as':kind})
        if len(points)>2:
            a=ET.SubElement(g,'Array',**{'as':'points'})
            for x,y in points[1:-1]:ET.SubElement(a,'mxPoint',x=str(x),y=str(y))
        # Source and target port locations preserve routed endpoints in draw.io.
        boxes={n[0]:n[2] for n in nodes}
        for prefix,key,point in [('exit',source,points[0]),('entry',target,points[-1])]:
            x,y,w,h=boxes[key];c.set('style',c.get('style')+f'{prefix}X={(point[0]-x)/w};{prefix}Y={(point[1]-y)/h};{prefix}Perimeter=0;')
        edge(d,points,text,lb,crow=crow,required=req)
    styles={'terminal':'rounded=1;arcSize=50;','decision':'rhombus;','io':'shape=parallelogram;perimeter=parallelogramPerimeter;','loop':'shape=hexagon;perimeter=hexagonPerimeter;','process':'rounded=0;','entity':'shape=swimlane;startSize=36;horizontal=1;'}
    for ident,kind,box,text in nodes:
        x,y,w,h=box
        if kind=='entity':
            title,*attrs=text.split('\n')
            c=ET.SubElement(r,'mxCell',id=ident,value=title,style=styles[kind]+'html=0;fontFamily=Arial;fontSize=21;fillColor=#e8eef3;strokeColor=#253746;',vertex='1',parent='1')
            ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
            body=ET.SubElement(r,'mxCell',id=ident+'_fields',value='\n'.join(attrs),style='text;html=0;align=left;verticalAlign=top;spacingLeft=8;fontFamily=Arial;fontSize=20;',vertex='1',parent=ident)
            ET.SubElement(body,'mxGeometry',x='0',y='40',width=str(w),height=str(h-40),**{'as':'geometry'})
            shape(d,'process',box,'',size=20)
            shape(d,'process',(x,y,w,38),title,fill='#e8eef3',size=21)
            label(d,'\n'.join(attrs),(x+5,y+42,w-10,h-46),20,align='left')
        else:
            c=ET.SubElement(r,'mxCell',id=ident,value=text,style=styles[kind]+'whiteSpace=wrap;html=0;fontFamily=Arial;fontSize=19;fillColor=#ffffff;strokeColor=#253746;',vertex='1',parent='1')
            ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
            shape(d,kind,box,text)
    ET.indent(root);ET.ElementTree(root).write(OUT/(name+'.drawio'),encoding='utf-8',xml_declaration=True)
    im.save(OUT/(name+'.png'))


def algorithms():
    # Все проверки и циклы check_configuration, включая поиск лишних компонентов.
    nodes=[
        ('s','terminal',(370,20,240,50),'Начало'),
        ('in','io',(285,100,410,65),'Ввод spec_items, components'),
        ('init','process',(285,195,410,65),'issues = []; matched = [False] × m'),
        ('i0','loop',(370,290,240,55),'i = 0'),
        ('ic','decision',(370,385,240,95),'i < n?'),
        ('j0','loop',(370,520,240,65),'actual = 0; j = 0'),
        ('jc','decision',(370,625,240,95),'j < m?'),
        ('eq','decision',(340,765,300,110),'Модели item[i] и\ncomponent[j] равны?'),
        ('inc','process',(700,790,255,65),'actual += 1\nmatched[j] = True'),
        ('jinc','process',(370,920,240,55),'j += 1'),
        ('count','decision',(45,765,230,110),'actual ≠\nitem[i].quantity?'),
        ('issue','process',(35,925,250,75),'Добавить несоответствие\nколичества в issues'),
        ('iinc','process',(60,1070,210,55),'i += 1'),
        ('k0','loop',(1110,385,240,55),'j = 0'),
        ('kc','decision',(1110,490,240,95),'j < m?'),
        ('extra','decision',(1100,640,260,95),'matched[j] = False?'),
        ('add','process',(1390,650,250,75),'Добавить лишний\nсерийный номер в issues'),
        ('kinc','process',(1110,790,240,55),'j += 1'),
        ('out','io',(1110,970,240,65),'Вывод issues'),
        ('end','terminal',(1110,1080,240,50),'Конец'),
    ]
    e=[]
    def a(s,t,p,txt='',lb=None):e.append((f'e{len(e)}',s,t,p,txt,lb))
    a('s','in',[(490,70),(490,100)]);a('in','init',[(490,165),(490,195)]);a('init','i0',[(490,260),(490,290)]);a('i0','ic',[(490,345),(490,385)])
    a('ic','j0',[(490,480),(490,520)],'да',(500,483,40,25));a('ic','k0',[(610,432),(1030,432),(1030,412),(1110,412)],'нет',(730,400,50,25))
    a('j0','jc',[(490,585),(490,625)]);a('jc','eq',[(490,720),(490,765)],'да',(500,727,40,25));a('jc','count',[(370,672),(160,672),(160,765)],'нет',(230,640,50,25))
    a('eq','inc',[(640,820),(700,820)],'да',(650,785,40,25));a('eq','jinc',[(490,875),(490,920)],'нет',(500,885,50,25));a('inc','jinc',[(827,855),(827,947),(610,947)])
    a('jinc','jc',[(610,947),(995,947),(995,610),(490,610),(490,625)])
    a('count','issue',[(160,875),(160,925)],'да',(170,888,40,25));a('count','iinc',[(45,820),(20,820),(20,1097),(60,1097)],'нет',(23,1025,50,25));a('issue','iinc',[(160,1000),(160,1070)])
    a('iinc','ic',[(270,1097),(310,1097),(310,432),(370,432)])
    a('k0','kc',[(1230,440),(1230,490)]);a('kc','extra',[(1230,585),(1230,640)],'да',(1240,600,40,25))
    a('kc','out',[(1350,537),(1670,537),(1670,1002),(1350,1002)],'нет',(1440,505,50,25))
    a('extra','add',[(1360,687),(1390,687)],'да',(1360,612,40,25));a('extra','kinc',[(1230,735),(1230,790)],'нет',(1240,752,50,25));a('add','kinc',[(1515,725),(1515,817),(1350,817)])
    a('kinc','kc',[(1110,817),(1065,817),(1065,537),(1110,537)]);a('out','end',[(1230,1035),(1230,1080)])
    drawio('algo_1','Сверить конфигурацию со спецификацией',nodes,e,1710,1170)
    nodes=[
        ('s','terminal',(300,20,260,50),'Начало'),
        ('in','io',(190,105,480,80),'Ввод results, required_count,\ndefects, configuration_issues'),
        ('init','process',(230,225,400,60),'reasons = list(configuration_issues)'),
        ('i0','loop',(300,320,260,55),'i = 0'),
        ('ic','decision',(300,415,260,95),'i < len(results)?'),
        ('status','decision',(290,560,280,110),'results[i].status\n≠ pass?'),
        ('bad','process',(700,580,290,70),'Добавить причину:\nстатус теста'),
        ('log','decision',(250,735,360,130),'Пустой log_ref\nИЛИ performed_at\nпосле strip()?'),
        ('nlog','process',(700,765,290,70),'Добавить причину:\nнет журнала или времени'),
        ('inc','process',(300,935,260,55),'i += 1'),
        ('missing','process',(1140,110,400,70),'missing = required_count\n− len(results)'),
        ('mc','decision',(1210,225,260,100),'missing > 0?'),
        ('ma','process',(1580,235,270,80),'Добавить число\nпропущенных тестов'),
        ('j0','loop',(1210,370,260,55),'j = 0'),
        ('jc','decision',(1210,470,260,95),'j < len(defects)?'),
        ('open','decision',(1200,615,280,110),'defects[j].status\n= open?'),
        ('da','process',(1580,635,270,70),'Добавить причину:\nоткрытый дефект'),
        ('ji','process',(1210,800,260,55),'j += 1'),
        ('out','io',(1140,995,400,75),'Вывод {ready: not reasons,\nreasons: reasons}'),
        ('end','terminal',(1210,1110,260,50),'Конец'),
    ]
    e=[]
    a('s','in',[(430,70),(430,105)]);a('in','init',[(430,185),(430,225)]);a('init','i0',[(430,285),(430,320)]);a('i0','ic',[(430,375),(430,415)])
    a('ic','status',[(430,510),(430,560)],'да',(440,520,40,25));a('ic','missing',[(560,462),(1060,462),(1060,145),(1140,145)],'нет',(810,430,50,25))
    a('status','bad',[(570,615),(700,615)],'да',(605,582,40,25));a('status','log',[(430,670),(430,735)],'нет',(440,690,50,25));a('bad','log',[(845,650),(845,700),(430,700),(430,735)])
    a('log','nlog',[(610,800),(700,800)],'да',(630,765,40,25));a('log','inc',[(430,865),(430,935)],'нет',(440,890,50,25));a('nlog','inc',[(845,835),(845,962),(560,962)])
    a('inc','ic',[(300,962),(120,962),(120,462),(300,462)])
    a('missing','mc',[(1340,180),(1340,225)]);a('mc','ma',[(1470,275),(1580,275)],'да',(1500,240,40,25));a('mc','j0',[(1340,325),(1340,370)],'нет',(1350,335,50,25));a('ma','j0',[(1715,315),(1715,350),(1340,350),(1340,370)])
    a('j0','jc',[(1340,425),(1340,470)]);a('jc','open',[(1340,565),(1340,615)],'да',(1350,580,40,25));a('jc','out',[(1470,517),(1890,517),(1890,1032),(1540,1032)],'нет',(1690,480,50,25))
    a('open','da',[(1480,670),(1580,670)],'да',(1500,635,40,25));a('open','ji',[(1340,725),(1340,800)],'нет',(1350,748,50,25));a('da','ji',[(1715,705),(1715,827),(1470,827)])
    a('ji','jc',[(1210,827),(1100,827),(1100,517),(1210,517)]);a('out','end',[(1340,1070),(1340,1110)])
    drawio('algo_2','Проверить готовность протокола',nodes,e,1930,1200)


def er():
    nodes=[
      ('models','entity',(40,65,310,170),'Модель / models\nPK id\nkind\nname'),
      ('spec_items','entity',(440,65,330,170),'Позиция / spec_items\nPK, FK order_id\nPK, FK model_id\nquantity'),
      ('orders','entity',(870,65,330,230),'Заявка / orders\nPK id\nnumber (AK)\npurpose\nspec_version\nserver_serial (AK)'),
      ('plan_tests','entity',(1300,65,330,150),'Состав / plan_tests\nPK, FK plan_id\nPK, FK test_id'),
      ('tests','entity',(1730,65,300,170),'Тест / tests\nPK id\ncode (AK)\nname'),
      ('components','entity',(40,440,310,170),'Компонент / components\nPK id\nserial\nFK model_id'),
      ('run_components','entity',(440,440,330,170),'Состав / run_components\nPK, FK run_id\nPK, FK component_id'),
      ('runs','entity',(870,420,330,290),'Прогон / runs\nPK id\nFK order_id\nFK plan_id\nnumber\nengineer\nbios\nbmc'),
      ('plans','entity',(1300,440,330,145),'План / plans\nPK id\nversion (AK)'),
      ('defects','entity',(870,870,330,190),'Дефект / defects\nPK id\nFK run_id\ndescription\nstatus'),
      ('results','entity',(1300,810,400,260),'Результат / results\nPK, FK run_id\nPK, FK test_id\nstatus\nlog_ref\nparameters\nperformed_at'),
    ]
    e=[]
    def a(s,t,p,txt='',lb=None,req=False):e.append((f'e{len(e)}',s,t,p,txt,lb,True,req))
    a('models','spec_items',[(350,160),(440,160)])
    a('orders','spec_items',[(870,120),(770,120)],req=True)
    a('orders','runs',[(1035,295),(1035,420)])
    a('models','components',[(195,235),(195,440)])
    a('components','run_components',[(350,525),(440,525)])
    a('runs','run_components',[(870,525),(770,525)])
    a('plans','runs',[(1300,525),(1200,525)])
    a('plans','plan_tests',[(1465,440),(1465,215)],req=True)
    a('tests','plan_tests',[(1730,140),(1630,140)])
    a('runs','defects',[(1035,710),(1035,870)])
    a('runs','results',[(1200,640),(1250,640),(1250,880),(1300,880)])
    a('tests','results',[(1880,235),(1880,940),(1700,940)])
    # Обозначения ключей и связи M:N раскрыты в отчёте; только crow's foot.
    drawio('er_logical','Логическая модель данных',nodes,e,2080,1120,True)


def bpmn():
    ns={'bpmn':'http://www.omg.org/spec/BPMN/20100524/MODEL','bpmndi':'http://www.omg.org/spec/BPMN/20100524/DI','dc':'http://www.omg.org/spec/DD/20100524/DC','di':'http://www.omg.org/spec/DD/20100524/DI','xsi':'http://www.w3.org/2001/XMLSchema-instance','bioc':'http://bpmn.io/schema/bpmn/biocolor/1.0'}
    for k,v in ns.items():ET.register_namespace(k,v)
    def el(parent,tag,**attrs):
        pre,local=tag.split(':');return ET.SubElement(parent,'{'+ns[pre]+'}'+local,{k:str(v) for k,v in attrs.items()})
    root=ET.Element('{'+ns['bpmn']+'}definitions',id='Definitions_KT2',targetNamespace='https://example.org/server-acceptance')
    coll=el(root,'bpmn:collaboration',id='Collaboration')
    el(coll,'bpmn:participant',id='Initiator',name='Инициатор заявки')
    el(coll,'bpmn:participant',id='Team',name='Сборка и приёмочное тестирование сервера',processRef='Process')
    process=el(root,'bpmn:process',id='Process',name='Сборка и приёмочное тестирование сервера',isExecutable='false')
    lanes=el(process,'bpmn:laneSet',id='Lanes')
    lane_defs=[('Kit','Ответственный за комплектование',(50,120,1950,180)),('Build','Инженер сборки',(50,300,1950,340)),('Test','Инженер испытаний',(50,640,1950,390)),('Accept','Ответственный за приёмку',(50,1030,1950,230))]
    nodes=[
      ('Start','startEvent','Заявка и комплект получены','Kit',(250,185,40,40)),
      ('KitTask','manualTask','Передать комплект и документы','Kit',(430,170,165,80)),
      ('Register','userTask','Зарегистрировать заявку и прогон','Build',(240,350,165,80)),
      ('Inspect','manualTask','Проверить детали по документации','Build',(460,350,165,80)),
      ('Parts','exclusiveGateway','Комплект пригоден?','Build',(675,365,50,50)),
      ('Assemble','manualTask','Собрать сервер','Build',(775,350,165,80)),
      ('Power','manualTask','Выполнить первое включение','Build',(995,350,165,80)),
      ('Post','exclusiveGateway','POST успешен?','Build',(1210,365,50,50)),
      ('Config','userTask','Сверить конфигурацию со спецификацией','Build',(1320,345,190,90)),
      ('ConfigOK','exclusiveGateway','Совпадает?','Build',(1570,365,50,50)),
      ('Run','manualTask','Выполнить план испытаний','Test',(1510,690,190,90)),
      ('Evaluate','userTask','Проверить готовность протокола','Test',(1260,690,190,90)),
      ('Protocol','userTask','Сформировать протокол','Test',(1010,690,190,90)),
      ('Review','userTask','Рассмотреть протокол','Accept',(1010,1090,190,80)),
      ('Ready','exclusiveGateway','Допуск подтверждён?','Accept',(1270,1105,50,50)),
      ('Pass','endEvent','Сервер и протокол переданы','Accept',(1530,1110,40,40)),
      ('Defect','userTask','Зафиксировать несоответствия','Test',(755,870,190,80)),
      ('Return','endEvent','Возврат на доработку','Test',(520,890,40,40)),
    ]
    lane_elements={}
    for ident,name,box in lane_defs:lane_elements[ident]=el(lanes,'bpmn:lane',id=ident,name=name)
    node_elements={}
    for ident,kind,name,lane,box in nodes:
        el(lane_elements[lane],'bpmn:flowNodeRef').text=ident
        node_elements[ident]=el(process,'bpmn:'+kind,id=ident,name=name)
    el(node_elements['Start'],'bpmn:messageEventDefinition',id='Start_message')
    el(coll,'bpmn:messageFlow',id='RequestMessage',sourceRef='Initiator',targetRef='Start')
    flows=[]
    def f(s,t,p,name='',lb=None):flows.append((f'F{len(flows)}',s,t,p,name,lb))
    f('Start','KitTask',[(290,205),(430,205)])
    f('KitTask','Register',[(512,250),(512,280),(322,280),(322,350)])
    f('Register','Inspect',[(405,390),(460,390)])
    f('Inspect','Parts',[(625,390),(675,390)])
    f('Parts','Assemble',[(725,390),(775,390)],'да',(735,355,30,25))
    f('Assemble','Power',[(940,390),(995,390)])
    f('Power','Post',[(1160,390),(1210,390)])
    f('Post','Config',[(1260,390),(1320,390)],'да',(1275,355,30,25))
    f('Config','ConfigOK',[(1510,390),(1570,390)])
    f('ConfigOK','Run',[(1595,415),(1595,690)],'да',(1600,595,30,25))
    f('Run','Evaluate',[(1510,735),(1450,735)])
    f('Evaluate','Protocol',[(1260,735),(1200,735)])
    f('Protocol','Review',[(1105,780),(1105,1090)])
    f('Review','Ready',[(1200,1130),(1270,1130)])
    f('Ready','Pass',[(1320,1130),(1530,1130)],'да',(1390,1095,30,25))
    f('Parts','Defect',[(700,415),(700,600),(850,600),(850,870)],'нет',(705,520,40,25))
    f('Post','Defect',[(1235,415),(1235,575),(850,575),(850,870)],'нет',(1240,520,40,25))
    f('ConfigOK','Defect',[(1570,390),(1540,390),(1540,550),(850,550),(850,870)],'нет',(1510,510,40,25))
    f('Ready','Defect',[(1295,1105),(1295,1000),(850,1000),(850,950)],'нет',(1300,1040,40,25))
    f('Defect','Return',[(755,910),(560,910)])
    for ident,s,t,points,name,lb in flows:
        el(node_elements[s],'bpmn:outgoing').text=ident;el(node_elements[t],'bpmn:incoming').text=ident
        sf=el(process,'bpmn:sequenceFlow',id=ident,sourceRef=s,targetRef=t,name=name)
        if s in ('Parts','Post','ConfigOK','Ready'):
            cond=el(sf,'bpmn:conditionExpression');cond.set('{'+ns['xsi']+'}type','bpmn:tFormalExpression');cond.text=name
    for node in node_elements.values():
        children=list(node)
        for child in children:node.remove(child)
        for tag in ('incoming','outgoing','messageEventDefinition'):
            for child in children:
                if child.tag.endswith('}'+tag):node.append(child)
    data=[('DOrder','Заявка; спецификация\norders / spec_items',(245,470,50,65),'Register'),('DModels','Каталог моделей\nmodels',(480,470,50,65),'Inspect'),('DComponents','Компоненты; состав\ncomponents / run_components',(1710,420,50,65),'Config'),('DSpec','Спецификация\nspec_items',(1325,470,50,65),'Config'),('DPlan','План; состав; тесты\nplans / plan_tests / tests',(1810,660,50,65),'Run'),('DRun','Карточка прогона\nruns',(650,160,50,65),'Register'),('DResults','Результаты\nresults',(1335,850,50,65),'Evaluate'),('DDefects','Дефекты\ndefects',(630,720,50,65),'Defect'),('DProtocol','Протокол\n(представление)',(1050,880,50,65),'Review')]
    assocs=[]
    boxes={n[0]:n[4] for n in nodes}
    for ident,name,box,target in data:
        el(process,'bpmn:dataObject',id=ident+'_object')
        el(process,'bpmn:dataObjectReference',id=ident,name=name,dataObjectRef=ident+'_object')
        aid='A'+ident
        # Направление ассоциации отражает чтение/создание документа.
        output=ident in ('DRun','DComponents','DResults','DDefects','DProtocol')
        actual_target={'DComponents':'Assemble','DResults':'Run','DProtocol':'Protocol'}.get(ident,target)
        # Ассоциации без направления: документ используется или создаётся задачей.
        el(process,'bpmn:association',id=aid,sourceRef=ident,targetRef=actual_target,associationDirection='None')
        x,y,w,h=box;tx,ty,tw,th=boxes[actual_target]
        if ident=='DRun':points=[(700,192),(800,192),(800,320),(322,320),(322,350)]
        elif ident=='DComponents':points=[(x+25,y),(1735,310),(857,310),(857,350)]
        elif ident=='DResults':points=[(x+25,y),(1360,815),(1605,815),(1605,780)]
        else:points=[(x+w/2,y),(x+w/2,ty+th+20),(tx+tw/2,ty+th+20),(tx+tw/2,ty+th)]
        assocs.append((aid,points))
    for association in list(process.findall('{'+ns['bpmn']+'}association')):
        process.remove(association);process.append(association)
    diagram=el(root,'bpmndi:BPMNDiagram',id='Diagram');plane=el(diagram,'bpmndi:BPMNPlane',id='Plane',bpmnElement='Collaboration')
    im,d=canvas(2050,1310)
    def di_shape(ident,box,horizontal=None,label_box=None):
        attrs={'id':ident+'_di','bpmnElement':ident}
        if horizontal is not None:attrs['isHorizontal']='true'
        if ident in ('Parts','Post','ConfigOK','Ready'):attrs['isMarkerVisible']='true'
        shp=el(plane,'bpmndi:BPMNShape',**attrs)
        if ident in ('Config','Evaluate','Protocol'):shp.set('{'+ns['bioc']+'}fill','#dceefb')
        x,y,w,h=box;el(shp,'dc:Bounds',x=x,y=y,width=w,height=h)
        if label_box:
            lb=el(shp,'bpmndi:BPMNLabel');lx,ly,lw,lh=label_box;el(lb,'dc:Bounds',x=lx,y=ly,width=lw,height=lh)
    di_shape('Initiator',(20,20,1980,60),True);shape(d,'process',(20,20,1980,60),'Инициатор заявки: согласованная заявка и спецификация',fill='#f3f5f6')
    di_shape('Team',(20,120,1980,1140),True);shape(d,'process',(20,120,1980,1140),'')
    for ident,name,box in lane_defs:
        di_shape(ident,box,True);shape(d,'process',box,'');label(d,name,(55,box[1]+10,140,box[3]-20),18)
    edge(d,[(270,80),(270,185)],dash=True)
    d.ellipse((532,152,548,168),fill='white',outline='#334c60',width=3)
    for ident,s,t,points,name,lb in flows:edge(d,points,name,lb)
    for aid,points in assocs:edge(d,points,dash=True,arrow=False)
    for ident,kind,name,lane,box in nodes:
        lb=None
        if kind in ('startEvent','endEvent','exclusiveGateway'):
            lb=(box[0]-55,box[1]+box[3]+10,160,65)
            shape(d,{'startEvent':'start','endEvent':'end','exclusiveGateway':'decision'}[kind],box,'×' if kind=='exclusiveGateway' else '')
            label(d,name,lb,18)
            if ident=='Start':
                d.rectangle((516,394,564,426),outline='#253746',width=2)
                d.line([(516,394),(540,412),(564,394)],fill='#253746',width=2)
        else:
            auto=ident in ('Config','Evaluate','Protocol')
            shape(d,'task',box,name,fill='#dceefb' if auto else 'white',size=17 if ident=='Register' else 19)
        di_shape(ident,box,label_box=lb)
    for ident,name,box,target in data:
        di_shape(ident,box,label_box=(box[0]-60,box[1]+70,170,65));shape(d,'data',box);label(d,name,(box[0]-65,box[1]+70,180,65),17)
    for ident,s,t,points,name,lb in flows:
        ed=el(plane,'bpmndi:BPMNEdge',id=ident+'_di',bpmnElement=ident)
        for x,y in points:el(ed,'di:waypoint',x=x,y=y)
        if lb:
            la=el(ed,'bpmndi:BPMNLabel');x,y,w,h=lb;el(la,'dc:Bounds',x=x,y=y,width=w,height=h)
    for ident,points in assocs+[('RequestMessage',[(270,80),(270,185)])]:
        ed=el(plane,'bpmndi:BPMNEdge',id=ident+'_di',bpmnElement=ident)
        for x,y in points:el(ed,'di:waypoint',x=x,y=y)
    label(d,'Голубые задачи выполняются с помощью программы. Доработка запускает новый прогон; прежние записи сохраняются.',(250,1270,1650,30),19)
    ET.indent(root);ET.ElementTree(root).write(OUT/'bpmn.bpmn',encoding='utf-8',xml_declaration=True)
    im.save(OUT/'bpmn.png')


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    bpmn();er();algorithms()
    print(OUT)
