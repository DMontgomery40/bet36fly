"""Deterministic bespoke film animation. Anatomy views use real soma positions.
Other motion illustrates the narrated mechanism; it is explicitly labelled schematic.
"""
from pathlib import Path
import math,json,subprocess,argparse,concurrent.futures,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
W,H,FPS=1920,1080,24
BG=(9,17,26); PANEL=(17,29,40); WHITE=(239,238,228); MUTED=(149,169,182); TEAL=(74,216,201); GOLD=(241,182,110); CORAL=(241,127,116); BLUE=(113,162,220); PURPLE=(182,157,229)
FONTS={}
def font(size,bold=False,serif=False):
    key=(size,bold,serif)
    if key not in FONTS:
        path='/System/Library/Fonts/Supplemental/Georgia.ttf' if serif else '/System/Library/Fonts/Avenir Next.ttc'
        FONTS[key]=ImageFont.truetype(path,size,index=0 if serif else (2 if bold else 7))
    return FONTS[key]
def text(d,xy,s,size=32,fill=WHITE,bold=False,anchor=None,serif=False):
    d.text(xy,str(s).replace('→',' / '),font=font(size,bold,serif),fill=fill,anchor=anchor)
def wrap(d,xy,s,width,size=32,fill=MUTED,leading=1.38):
    x,y=xy
    if '\n' in s:
        for part in s.splitlines():y=wrap(d,(x,y),part,width,size,fill,leading)+size*.3
        return y
    line=''
    for word in s.split():
        test=(line+' '+word).strip()
        if d.textlength(test,font=font(size))>width and line:
            text(d,(x,y),line,size,fill);y+=size*leading;line=word
        else:line=test
    if line:text(d,(x,y),line,size,fill)
    return y+size*leading

def ease(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def lerp(a,b,p):return a+(b-a)*p
def line(d,a,b,c=TEAL,width=3):d.line([a,b],fill=c,width=width)
def arrow(d,a,b,c=TEAL,width=4):
    line(d,a,b,c,width);ang=math.atan2(b[1]-a[1],b[0]-a[0]);r=15
    d.polygon([b,(b[0]-r*math.cos(ang-.5),b[1]-r*math.sin(ang-.5)),(b[0]-r*math.cos(ang+.5),b[1]-r*math.sin(ang+.5))],fill=c)
def dot(d,x,y,r=8,c=TEAL):d.ellipse((x-r,y-r,x+r,y+r),fill=c)
def pulse(d,a,b,t,c=GOLD,phase=0):
    v=(t*.16+phase)%1;dot(d,lerp(a[0],b[0],v),lerp(a[1],b[1],v),7,c)
def card(d,box,title,subtitle='',color=TEAL):
    x,y,x2,y2=box;d.rounded_rectangle(box,radius=20,fill=PANEL,outline=(37,58,70),width=2)
    d.rectangle((x,y+25,x+4,y2-25),fill=color)
    text(d,(x+28,y+26),title,35,WHITE,bold=True)
    if subtitle:wrap(d,(x+28,y+86),subtitle,x2-x-56,27,MUTED)
def chip(d,x,y,s,c=TEAL):
    w=d.textlength(s,font=font(23))+36;d.rounded_rectangle((x,y,x+w,y+43),radius=18,outline=c,width=1);text(d,(x+18,y+6),s,23,c)

DATA=np.load(ROOT/'assets/anatomy.npz');XYZ=DATA['xyz'];GROUP=DATA['groups']
GC=[(91,119,139),TEAL,GOLD,CORAL,PURPLE,BLUE]
HERO=Image.open(ROOT/'assets/fly-editorial.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
# Static background prepared once; the light field is part of the editorial design.
yy,xx=np.mgrid[0:H,0:W];glow=np.exp(-(((xx-1430)/930)**2+((yy-520)/710)**2))
BASE=Image.fromarray(np.stack([BG[i]+glow*(5 if i==0 else 9) for i in range(3)],axis=-1).astype('uint8'))
RNG=np.random.default_rng(365)
NET=RNG.uniform([0,0],[1,1],(68,2));EDGES=[(i,j) for i in range(68) for j in range(i+1,68) if np.linalg.norm(NET[i]-NET[j])<.22]

def graph(d,box,t=0,color=TEAL,n=68,active=True,silenced=False):
    x,y,x2,y2=box;pts=NET[:n]*[x2-x,y2-y]+[x,y]
    off={i for i,(px,py) in enumerate(NET[:n]) if silenced and .28<px<.6 and .28<py<.68}
    for i,j in EDGES:
        if i<n and j<n and i not in off and j not in off:line(d,tuple(pts[i]),tuple(pts[j]),(38,68,83),2)
    for k,(px,py) in enumerate(pts):
        on=active and k not in off and math.sin(t*2.3+k*.71)>.7
        dot(d,px,py,6 if on else 4,color if on else ((52,59,65) if k in off else (87,113,129)))
    return pts

def anatomy(d,cx,cy,scale,t):
    a=.22*math.sin(t*.035);c,s=math.cos(a),math.sin(a)
    px=XYZ[:,0]*c+XYZ[:,2]*s;py=XYZ[:,1]
    depth=XYZ[:,2]*c-XYZ[:,0]*s
    for k in np.argsort(depth):
        x=cx+px[k]*scale;y=cy+py[k]*scale
        if 240<y<960 and 60<x<1860:dot(d,float(x),float(y),1.6 if GROUP[k]==0 else 2.2,GC[int(GROUP[k])])

def trace(d,box,t,c=TEAL,spikes=False):
    x,y,x2,y2=box;line(d,(x,y2),(x2,y2),(59,78,90),2);line(d,(x,y),(x,y2),(59,78,90),2)
    pts=[]
    for i in range(300):
        u=i/299
        v=(u*5+.08)%1
        val=(v*.8 if v<.85 else .12) if spikes else .34+.21*math.sin(u*17+t*.7)+.13*math.sin(u*49+t*.3)
        pts.append((x+u*(x2-x),y2-val*(y2-y)))
    d.line(pts,fill=c,width=4)
    cursor=x+(t*.07%1)*(x2-x);line(d,(cursor,y),(cursor,y2),GOLD,2)

SOURCES={
'hero':'bet36fly  /  a technical introduction for bet365',
'reconstruction':'Source: MaleCNS project • HHMI Janelia / Cambridge / MRC LMB / Google Research',
'timeline':'MaleCNS v1.0 • June 8, 2026     Paper • September 3, 2026',
'architecture':'Schematic • architecture, dynamics and adaptation are explicit model choices',
'spikes':'Schematic • leaky integrate-and-fire dynamics',
'model':'bet36fly simulator • conceptual layer diagram',
'pathway':'Schematic • sensory neurons → projection neurons → Kenyon cells → outputs',
'intervention':'Schematic • matched inputs and controlled interventions',
'viral':'Illustrated comparison • display technology and neural computation are separate components',
'doom':'Source: nftechie/doomfly • inspected public source • schematic of its closed loop',
'vision':'Workflow illustration • Lappalainen et al., Nature 2024 • TuragaLab/flyvis',
'body':'Body-feedback schematic • TuragaLab/flybody • body + physics + reinforcement-learning controllers',
'teams':'bet36fly • pregame information and an externally fitted probability model',
'encoding':'Schematic • independent team encoding; requested sensory stimulation',
'response':'bet36fly • recorded outputs: Clavicle / ANXXX462a and Quasimodo / GNG042',
'backtest':'Frozen 2023 MLB confirmation • 2,423 games • accuracy of each complete pipeline',
'learning':'bet36fly conditioning-02 • schematic of the qualified cue-learning mechanism',
'recovery':'bet36fly circuit-02 • schematic of dopamine-dependent recovery',
'reservoir':'Proposed research direction • sequence-driven recurrent state',
'readout':'Actual MaleCNS soma positions • display sample • camera motion only',
'llm':'Illustrated engineering workflow • language-model assistance around an explicit simulator',
'fish':'Schematic • Google Neural Mapping / ZAPBench • paired anatomy and activity resource in development',
'mouse':'Schematic • MICrONS Consortium, Nature 2025 • mouse visual cortex volume',
'close':'Research and source notes accompany this film • September 14, 2026'}


def render(scene,t,duration):
    k=scene['kind'];p=t/duration
    im=HERO.copy() if k in ['hero','close'] else BASE.copy();d=ImageDraw.Draw(im)
    if k in ['hero','close']:
        # Typography is authored separately from the generated editorial image.
        text(d,(100,100),'bet36fly  /  CONNECTOMES',28,TEAL,bold=True)
        if k=='hero':
            text(d,(100,290),'Neural architectures',63,WHITE,serif=True);text(d,(100,378),'from a nervous system',63,WHITE,serif=True)
            wrap(d,(106,532),'A technical introduction for bet365',670,36,WHITE)
            chip(d,108,657,'SEPTEMBER 2026',GOLD)
        else:
            text(d,(100,302),'Build with the wiring.',65,WHITE,serif=True)
            wrap(d,(105,439),'Carry the tools forward.',670,42,TEAL)
            wrap(d,(108,601),'Connectomes • bet36fly • visual and embodied models',635,28,MUTED)
        text(d,(106,927),'Editorial illustration',22,MUTED)
    else:
        text(d,(96,63),'CONNECTOMES',25,TEAL,bold=True)
        text(d,(1820,64),f'{scene["id"]+1:02d} / 24',24,MUTED,anchor='ra')
        text(d,(96,127),scene['title'],57,WHITE,serif=True)
        line(d,(96,224),(1824,224),(42,58,67),2)
    if k=='reconstruction':
        for a in range(6):
            off=a*19
            d.rounded_rectangle((136+off,395-off,496+off,774-off),radius=9,fill=(22+a*6,35+a*6,44+a*6),outline=(100,128,137),width=2)
            for j in range(6):
                x=160+off+j*58;y=450-off+(j%2)*57
                d.ellipse((x,y,x+100,y+155),outline=TEAL if a==5 else (59,79,87),width=3)
        arrow(d,(671,562),(851,562));graph(d,(940,335,1760,824),t,active=False)
        text(d,(175,853),'Serial tissue images',34,WHITE);text(d,(1080,853),'Identified cells + synapses',34,WHITE)
    elif k=='timeline':
        anatomy(d,1370,595,640,t)
        text(d,(110,334),'166,700',102,TEAL);text(d,(112,461),'retained neurons',35,MUTED)
        text(d,(110,574),'25.6 million',68,GOLD);text(d,(112,668),'connected neuron pairs',32,MUTED)
        line(d,(115,826),(870,826),TEAL,3)
        for x,a,b in [(150,'JUNE 8','v1.0 data'),(680,'SEPT 3','paper published')]:
            dot(d,x,826,9,GOLD);text(d,(x-20,865),a,24,GOLD);text(d,(x-20,902),b,27,WHITE)
        text(d,(1170,912),'Sampled soma positions',25,MUTED)
    elif k=='architecture':
        for i in range(4):
            x=122+i*158;card(d,(x,412,x+122,675),f'{i+1}',color=BLUE)
            for j in range(5):line(d,(x+25,502+j*23),(x+95,502+j*23),BLUE,3)
            if i<3:arrow(d,(x+124,548),(x+154,548),BLUE,3)
        text(d,(122,740),'Repeated designed blocks',33,WHITE)
        graph(d,(1000,330,1767,789),t);text(d,(1020,839),'Measured heterogeneous graph',33,WHITE)
        chip(d,128,310,'TRANSFORMER',BLUE);chip(d,1030,268,'CONNECTOME',TEAL)
    elif k=='spikes':
        trace(d,(160,350,1130,744),t,spikes=True)
        line(d,(160,500),(1130,500),(139,105,75),2);text(d,(180,451),'Threshold',26,GOLD)
        text(d,(180,800),'Integrate → spike → recover',37,WHITE)
        card(d,(1260,352,1780,773),'Voltage has history','Incoming current\nLeak toward rest\nThreshold event\nOutgoing signals',TEAL)
        text(d,(185,885),'τ dV/dt = −(V − Vrest) + input',39,TEAL)
    elif k=='model':
        rows=[('01','Wiring','Which cells connect?',TEAL),('02','Dynamics','How does activity propagate?',GOLD),('03','Plasticity','Which connections can change?',PURPLE)]
        for i,(n,a,b,c) in enumerate(rows):
            y=304+i*200;card(d,(152,y,1755,y+158),a,b,c);text(d,(1620,y+48),n,48,c)
            for j in range(8):dot(d,1030+j*62,y+79,7,c if (j+int(t))%3 else WHITE)
    elif k=='pathway':
        labels=['Odour receptors','Projection neurons','Kenyon cells','Output neurons'];xs=[215,690,1180,1660]
        for j,(x,lab) in enumerate(zip(xs,labels)):
            n=[8,6,32,4][j]
            for q in range(n):
                yy=420+q%8*48;xx=x+(q//8-1)*29
                active=j!=2 or q in [3,10,19,27]
                dot(d,xx,yy,9,TEAL if active else (49,65,73))
            wrap(d,(x-125,865),lab,300,30,WHITE)
            if j<3:
                a=(x+88,590);b=(xs[j+1]-120,590);arrow(d,a,b);pulse(d,a,b,t,phase=j*.2)
        chip(d,1040,308,'SPARSE CUE PATTERN',GOLD)
        text(d,(1300,331),'Dopamine',32,PURPLE);arrow(d,(1417,380),(1445,539),PURPLE)
    elif k=='intervention':
        graph(d,(145,330,810,785),t,active=True);graph(d,(1085,330,1765,785),t,active=True,silenced=True)
        d.rounded_rectangle((1280,480,1440,615),radius=20,outline=CORAL,width=4)
        text(d,(140,850),'Matched input',34,TEAL);text(d,(1080,850),'Selected cells silenced',34,CORAL)
        arrow(d,(850,562),(1020,562),GOLD);text(d,(827,740),'Compare',28,GOLD)
    elif k=='viral':
        card(d,(120,320,850,898),'Rendered behaviour','Script → movement → display',GOLD)
        # Deliberately simple schematic fly drawing, visibly authored rather than footage.
        cx=465+math.sin(t*.3)*90;cy=618
        d.ellipse((cx-24,cy-65,cx+24,cy+65),fill=GOLD);dot(d,cx,cy-78,24,GOLD)
        for a in [-1,1]:
            d.ellipse((cx+a*25-45,cy-80,cx+a*25+45,cy+10),outline=MUTED,width=2)
            for j in range(3):line(d,(cx,cy-25+j*30),(cx+a*100,cy-45+j*45+math.sin(t*2+j)*15),GOLD,3)
        card(d,(975,320,1800,898),'Simulated neural activity','Identified input → solver → decoded output',TEAL)
        graph(d,(1080,516,1690,760),t);chip(d,1110,805,'FOLLOW THE COMPUTATIONAL PATH',TEAL)
    elif k=='doom':
        boxes=[(125,348,683,546),(1210,348,1770,546),(1210,700,1770,892),(125,700,683,892)]
        for b,a,sub,c in zip(boxes,['Game frame','Sensory stimulation','Neural solver','Game controls'],['ViZDoom environment','Modelled visual neurons','Retained MaleCNS graph','Turn • move • fire'],[BLUE,TEAL,PURPLE,GOLD]):card(d,b,a,sub,c)
        paths=[((683,447),(1210,447)),((1490,546),(1490,700)),((1210,791),(683,791)),((405,700),(405,546))]
        for i,(a,b) in enumerate(paths):arrow(d,a,b,TEAL);pulse(d,a,b,t,phase=i*.25)
        text(d,(960,588),'Closed-loop control',40,WHITE,anchor='mm');text(d,(960,642),'DOOMFLY',29,TEAL,anchor='mm')
    elif k=='vision':
        d.rounded_rectangle((140,345,770,780),radius=18,fill=(28,44,53),outline=TEAL,width=2)
        for j in range(10):
            x=145+((j*82+t*32)%617);d.rectangle((x,350,min(x+24,764),773),fill=(100,189,181))
        arrow(d,(825,562),(1010,562));trace(d,(1080,346,1765,728),t)
        text(d,(150,822),'Motion-task optimisation',33,WHITE);text(d,(1080,792),'Predicted neural responses',32,WHITE)
        text(d,(1080,855),'Compared with 26 studies',29,GOLD);chip(d,155,286,'FLYVIS / PYTORCH',TEAL)
    elif k=='body':
        # Schematic body with alternating tripod gait, not project footage or a neural rollout.
        cx,cy=960,540
        for j in range(11):line(d,(180+j*150,850),(480+j*95,450),(34,52,62),2)
        for y in range(500,940,80):line(d,(150,y),(1780,y),(34,52,62),2)
        d.ellipse((875,422,1045,690),fill=(64,103,115),outline=TEAL,width=4);dot(d,960,395,57,TEAL)
        for side in [-1,1]:
            for j in range(3):
                y=460+j*75;step=math.sin(t*3+j*math.pi+side)*32
                a=(cx+side*55,y);b=(cx+side*(185+j*22),y+35);end=(cx+side*(260+j*27),y+120+step)
                line(d,a,b,GOLD,9);line(d,b,end,GOLD,7);dot(d,*end,8,TEAL)
        chip(d,145,295,'FLYBODY / MUJOCO',TEAL)
        text(d,(150,869),'Contact',34,WHITE);text(d,(758,925),'Momentum',34,WHITE);text(d,(1480,869),'Feedback',34,WHITE)
    elif k=='teams':
        for j,(a,b,c) in enumerate([('Pregame data','Available before the game',BLUE),('Sensory encoder','Team → stimulation',TEAL),('Circuit response','Measured output features',GOLD),('Probability','Externally fitted readout',PURPLE)]):
            x=100+j*461;card(d,(x,408,x+407,755),a,b,c)
            if j<3:arrow(d,(x+412,580),(x+452,580),TEAL);pulse(d,(x+412,580),(x+452,580),t,phase=j*.2)
        text(d,(125,842),'A repeatable experiment around a familiar prediction workflow',37,WHITE)
    elif k=='encoding':
        for x,name,c in [(150,'Team A',TEAL),(1050,'Team B',GOLD)]:
            card(d,(x,308,x+716,882),name,'Independent sensory representation',c)
            for j,(label,val) in enumerate([('Sweet',.69 if x<500 else .82),('Bitter',.22 if x<500 else .18),('Uncertainty',.38 if x<500 else .48)]):
                y=492+j*105;text(d,(x+40,y),label,30,WHITE);d.rounded_rectangle((x+265,y+7,x+655,y+35),radius=12,fill=(39,54,64));d.rounded_rectangle((x+265,y+7,x+265+390*val*ease(t/3),y+35),radius=12,fill=c)
        text(d,(960,939),'Both opportunities can be attractive',35,WHITE,anchor='mm')
    elif k=='response':
        for x,name,sub,c in [(142,'Clavicle','ANXXX462a',TEAL),(1045,'Quasimodo','GNG042',GOLD)]:
            card(d,(x,322,x+728,889),name,sub,c)
            # Spike marks convey the measurement type only, not fabricated sampled results.
            for j in range(22):
                xx=x+58+j*28;high=30+(j*13%57)
                if j/22<min(1,t/5):line(d,(xx,723),(xx,723-high),c,3)
            line(d,(x+40,724),(x+678,724),MUTED,2);text(d,(x+43,787),'Cue-window spike count',30,WHITE)
        text(d,(960,948),'Measurement schematic',25,MUTED,anchor='mm')
    elif k=='backtest':
        text(d,(140,314),'2,423 games',63,TEAL);text(d,(143,400),'MLB • 2023 confirmation',29,MUTED)
        vals=[('Full sensory pipeline',56.21,TEAL),('Encoder alone',55.84,GOLD),('Same-information model',56.29,BLUE)]
        for i,(lab,val,c) in enumerate(vals):
            y=519+i*132;text(d,(145,y),lab,32,WHITE)
            # Shared zero baseline, modest differences shown at their actual scale.
            d.rounded_rectangle((685,y+5,1680,y+48),radius=10,fill=(28,43,54))
            d.rounded_rectangle((685,y+5,685+995*val/100*ease(t/3),y+48),radius=10,fill=c)
            text(d,(1750,y-1),f'{val:.2f}%',36,c,anchor='ra')
        text(d,(686,952),'Accuracy • common 0–100% scale',26,MUTED)
    elif k=='learning':
        card(d,(120,317,680,834),'Cue','Sparse Kenyon-cell activity',TEAL);card(d,(1210,317,1780,834),'Output','Mushroom-body response',GOLD)
        for i in range(7):dot(d,440,490+i*39,9,TEAL)
        dot(d,1425,621,29,GOLD)
        for i in range(7):
            a=(455,490+i*39);b=(1388,621);width=6 if t<duration*.5 else (2 if i in [1,3,5] else 6);line(d,a,b,(84,137,144),width);pulse(d,a,b,t,phase=i*.12)
        chip(d,781,292,'DOPAMINE',PURPLE);arrow(d,(946,349),(955,535),PURPLE)
        text(d,(960,928),'Pairing → persistent change → reversal',36,WHITE,anchor='mm')
    elif k=='recovery':
        for i in range(14):
            x=172+i*115;y=460;initial=.08 if i%3 else .28;v=lerp(initial,.4+.14*math.sin(i),ease((t-2)/9))
            d.rounded_rectangle((x,y,x+55,808),radius=15,fill=(35,51,61));d.rounded_rectangle((x,808-330*v,x+55,808),radius=15,fill=TEAL)
        text(d,(148,327),'Room to adapt across repeated experience',43,WHITE)
        line(d,(145,790),(1770,790),CORAL,2);text(d,(147,841),'Allowed lower limit',27,CORAL)
        chip(d,1190,882,'RECOVERY UNDER DOPAMINE',PURPLE)
    elif k=='reservoir':
        for j,lab in enumerate(['Game 1','Rest','Game 2','Game 3']):
            x=140+j*235;card(d,(x,323,x+207,460),lab,color=BLUE)
        arrow(d,(1097,400),(1320,400),TEAL)
        graph(d,(1150,529,1740,875),t)
        trace(d,(155,579,998,842),t,TEAL)
        text(d,(157,904),'Sequence-dependent state',33,WHITE);text(d,(1250,904),'Recurrent circuit',33,WHITE)
    elif k=='readout':
        anatomy(d,690,600,640,t)
        for i,(a,c) in enumerate([('Mushroom-body outputs',GOLD),('Orientation circuits',PURPLE),('Descending pathways',BLUE)]):
            y=359+i*190;card(d,(1220,y,1790,y+145),a,color=c);arrow(d,(1020,430+i*136),(1213,y+73),c,3)
        text(d,(202,934),'Record additional anatomical pathways',31,MUTED)
    elif k=='llm':
        card(d,(125,323,810,865),'Language-model assistance','Read papers\nTrace cell identities\nBuild and test software',PURPLE)
        card(d,(1090,323,1790,865),'Explicit circuit model','Inputs\nState\nUpdate equations',TEAL)
        # Each row is a concrete step, not a decorative terminal log.
        for i,lab in enumerate(['Paper → implementation','Code → reproducible experiment']):
            text(d,(460 if i==0 else 1445,740),lab,24,GOLD,anchor='mm')
        arrow(d,(846,738),(1047,738),GOLD)
    elif k=='fish':
        # Transparent-fish outline is a schematic; neural scatter is illustrative.
        d.ellipse((183,388,1142,765),outline=TEAL,width=5)
        d.polygon([(1130,575),(1460,365),(1460,785)],outline=TEAL,width=5)
        for j in range(340):
            a=j*2.39996;r=math.sqrt(j/340)
            x=425+math.cos(a)*r*185;y=562+math.sin(a)*r*120;dot(d,x,y,3,GOLD if j%7==0 else TEAL)
        text(d,(142,298),'Wiring + activity in the same specimen',41,WHITE)
        card(d,(1120,720,1786,935),'70,000+ neurons','ZAPBench activity recordings',GOLD)
        trace(d,(180,817,905,933),t,TEAL)
    elif k=='mouse':
        x,y=412,448
        d.polygon([(x,y),(x+655,y),(x+847,y-134),(x+190,y-134)],fill=(36,57,71),outline=TEAL,width=3)
        d.polygon([(x+655,y),(x+847,y-134),(x+847,y+289),(x+655,y+423)],fill=(19,40,53),outline=TEAL,width=3)
        d.rectangle((x,y,x+655,y+423),fill=(25,44,57),outline=TEAL,width=3)
        graph(d,(x+30,y+25,x+620,y+398),t,active=False)
        text(d,(1370,415),'~0.5 billion',55,GOLD);text(d,(1371,495),'synaptic connections',28,MUTED)
        wrap(d,(1370,605),'Wiring and functional recordings from mouse visual cortex',405,35,WHITE)
        text(d,(420,907),'MICrONS • reconstructed cortical volume',32,WHITE)
    # Footer is deliberately small but readable and consistent across the film.
    text(d,(98,1004),SOURCES[k],22,MUTED)
    d.rectangle((0,1068,W,1079),fill=(24,39,48));d.rectangle((0,1068,int(W*p),1079),fill=TEAL)
    fade=min(ease(t/.35),ease((duration-t)/.35))
    if fade<1:im=Image.blend(Image.new('RGB',(W,H),BG),im,fade)
    return im


def probe(path):
    return float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True))

def one_scene(scene,preview=False):
    audio=ROOT/scene['audio_path'];dur=probe(audio) if audio.exists() else len(scene['narration'].split())/160*60
    if preview:
        dest=ROOT/'qa/frames';dest.mkdir(parents=True,exist_ok=True)
        for label,pct in [('early',.18),('mid',.53),('late',.85)]:render(scene,dur*pct,dur).save(dest/f'{scene["id"]:02d}-{label}.jpg',quality=88)
        return scene['id'],dur
    if not audio.exists():raise RuntimeError('Narration must exist before rendering')
    dest=ROOT/scene['video_source_path'];dest.parent.mkdir(parents=True,exist_ok=True)
    frames=math.ceil(dur*FPS)
    digest=hashlib.sha256((json.dumps(scene,sort_keys=True)+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+str(dur)).encode()).hexdigest()
    stamp=dest.with_suffix('.json')
    if dest.exists() and stamp.exists() and json.loads(stamp.read_text()).get('fingerprint')==digest:return scene['id'],dur
    cmd=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(frames):proc.stdin.write(render(scene,i/FPS,dur).tobytes())
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('Video encoder failed')
    stamp.write_text(json.dumps({'fingerprint':digest,'duration':dur,'frames':frames,'fps':FPS},indent=2)+'\n')
    print('rendered',scene['id'],round(dur,2),flush=True)
    return scene['id'],dur

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--scene',type=int);parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    plan=json.loads((ROOT/'plan.json').read_text());scenes=plan['scenes']
    if args.scene is not None:scenes=[s for s in scenes if s['id']==args.scene]
    if args.preview:
        for s in scenes:one_scene(s,True)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:list(ex.map(one_scene,scenes))
