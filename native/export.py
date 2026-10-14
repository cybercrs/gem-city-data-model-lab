"""Export original teaching content and independent Python outcome fixtures."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'native'))
from capture import load,State,flat
from gem_city_data_model_lab import case_data as c,engine as e,progress as p
rec,ns=load(ROOT)
specs=[('grain','g',[('grain',c.GRAIN_CORRECT,c.GRAIN_OPTIONS),('key',c.KEY_CORRECT,c.KEY_OPTIONS)]),('anomalies','a',[(x['id'],x['correct'],c.ANOMALY_OPTIONS) for x in c.ANOMALIES]),('normalization','n',[(f,t,c.TABLE_OPTIONS) for f,t,_ in c.FIELD_ASSIGNMENTS]),('er','e',[(i,a,c.ER_FOREIGN_KEY_OPTIONS if i=='foreign_keys' else c.ER_RELATIONSHIP_OPTIONS) for i,_,_,a in c.ER_PROMPTS]),('rea','r',[(i,a,c.REA_OPTIONS) for i,a,_ in c.REA_ITEMS])]
renderers=['render_briefing','render_grain','render_anomalies','render_normalization','render_er','render_rea','render_debrief']
allgood={group:{i:a for i,a,_ in fields} for group,key,fields in specs}
def state(stage,variant):
 s=State(p.activity_defaults());s.dm_shuffle_seed=0;s.dm_stage=stage
 for index,(group,key,fields) in enumerate(specs,1):
  answers=allgood[group].copy() if index<stage or index==stage and variant!='unanswered' else {}
  if index==stage and variant=='wrong':i,a,opts=fields[0];answers[i]=next(v for v in opts if v!=a)
  s['dm_'+group]=answers;s.dm_drafts[group]=answers.copy()
  if answers:s.dm_attempts[group]=1
 return s
screens=[]
for stage,name in enumerate(renderers):
 variants={}
 for variant in ['unanswered','wrong','correct']:
  rec.session_state=state(stage,variant)
  with rec.capture() as items:ns[name]()
  variants[variant]=flat(items)
 screens.append(variants)
rec.session_state=state(0,'unanswered')
with rec.capture() as hero:ns['render_hero']()
groups=[]
for stage,(group,key,fields) in enumerate(specs,1):
 screen=screens[stage]['unanswered'];widgets=[n for n in screen if n['kind'] in ['radio','select']]
 first=next(i for i,n in enumerate(screen) if n['kind'] in ['radio','select'])
 if stage==2:first-=1
 prefix=screen[:first];fielditems=[]
 for identifier,answer,options in fields:
  expected={'grain':'widget_dm_grain','key':'widget_dm_key'}.get(identifier) if stage==1 else 'widget_dm_'+({'anomalies':'anomaly_','normalization':'normalize_','er':'er_','rea':'rea_'}[group])+(identifier.lower().replace(' ','_') if group=='rea' else identifier)
  widget=next(n for n in widgets if n['key']==expected);card=None
  if stage==2:
   at=screen.index(widget);card=screen[at-1]
  detail={}
  for value in options:
   answers=allgood[group].copy();answers[identifier]=value
   if stage==1:
    correct,messages=e.evaluate_grain(answers['grain'],answers['key']);message=messages[0 if identifier=='grain' else 1]
   else:
    func=getattr(e,'evaluate_'+('normalization' if group=='normalization' else group));_,ds=func(answers);d=next(x for x in ds if x.get('id',x.get('field',x.get('label')))==identifier)
    lead={'anomalies':'The best classification is ','normalization':'Correct table: ','er':'Correct answer: ','rea':'Correct category: '}[group]
    message=lead+d['answer']+'. '+d['explanation']
   detail[value]={'correct':value==answer,'message':message}
  fielditems.append({'id':identifier,'answer':answer,'options':list(options),'widget':widget,'card':card,'feedback':detail})
 correct=screens[stage]['correct'];last=max(i for i,n in enumerate(correct) if n['kind']=='html' and '<div class="feedback' in n['text'])
 groups.append({'stage':stage,'id':group,'key':key,'fields':fielditems,'prefix':prefix,'tail':correct[last+1:],'check':next(n['label'] for n in screen if n['kind']=='button')})
data={'hero':hero,'stages':list(ns['STAGE_LABELS']),'screens':screens,'groups':groups,'rawRows':list(c.RAW_ROWS),'rawColumns':list(c.RAW_COLUMNS)}
(ROOT/'native/content.js').write_text('export const DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
css=ns['APP_CSS'].strip().removeprefix('<style>').removesuffix('</style>');(ROOT/'native/original.css').write_text(css)
fixtures=[]
for stage in range(7):
 s=state(stage,'correct' if stage else 'unanswered');s.dm_shuffle_seed=9223372036854775807
 fixtures.append({'stage':stage,'token':p.encode_state(s),'snapshot':p.snapshot_from_state(s)})
(ROOT/'native/tests/python-oracles.json').write_text(json.dumps({'legacy':fixtures,'shuffles':[{'seed':str(seed),'salt':salt,'expected':(setattr(rec,'session_state',State(dm_shuffle_seed=seed)) or ns['shuffled'](list(c.ANOMALY_OPTIONS),salt))} for seed in [0,34105,9223372036854775807] for salt in ['anomaly-answer-order:insert_customer','rea-question-order']]},indent=2)+'\n')
print('Exported all seven original screens, feedback for every choice, normalized/ER/REA visuals and URL fixtures')
