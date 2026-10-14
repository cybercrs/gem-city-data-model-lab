import ast, json, sys
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
class State(dict):
 def __getattr__(self,k):return self[k]
 def __setattr__(self,k,v):self[k]=v
class Container:
 def __init__(self,r,n):self.r=r;self.n=n
 def __enter__(self):self.r.stack.append(self.n['children']);return self
 def __exit__(self,*a):self.r.stack.pop()
 def __getattr__(self,k):
  def f(*args,**kwargs):
   with self:return getattr(self.r,k)(*args,**kwargs)
  return f
class Recorder:
 def __init__(self):self.session_state=State();self.query_params={};self.stack=[[]]
 def node(self,kind,**kw):n={'kind':kind,**kw};self.stack[-1].append(n);return n
 def set_page_config(self,**kw):pass
 def markdown(self,text,unsafe_allow_html=False,**kw):self.node('html' if unsafe_allow_html else 'markdown',text=text.strip())
 def __getattr__(self,k):
  if k in {'header','subheader','write','success','warning','info','error','caption','code'}:return lambda text,**kw:self.node(k,text=str(text).replace(r'\$','$'))
  if k in {'iframe','rerun','divider'}:return lambda *a,**kw:None
  raise AttributeError(k)
 def button(self,label,**kw):self.node('button',label=label,key=kw.get('key'));return False
 def radio(self,label,options,**kw):
  self.node('radio',label=label,options=list(options),key=kw.get('key'),help=kw.get('help'));i=kw.get('index');return options[i] if i is not None else None
 def selectbox(self,label,options,**kw):
  self.node('select',label=label,options=list(options),key=kw.get('key'),help=kw.get('help'));i=kw.get('index');return options[i] if i is not None else None
 def text_area(self,label,**kw):self.node('textarea',label=label,key=kw.get('key'));return kw.get('value','')
 def metric(self,label,value,**kw):self.node('metric',label=label,value=value,**kw)
 def dataframe(self,rows,**kw):self.node('table',rows=rows.to_dict('records') if hasattr(rows,'to_dict') else rows)
 def columns(self,count):n=self.node('columns',children=[]);count=count if isinstance(count,int) else len(count);result=[]
 def expander(self,label,**kw):return Container(self,self.node('details',label=label,open=kw.get('expanded',False),children=[]))
 @contextmanager
 def capture(self):self.stack=[[]];yield self.stack[0]
# Explicit columns implementation retains source layout and column-owned content.
def columns(self,count):
 count=count if isinstance(count,int) else len(count);n=self.node('columns',children=[]);result=[]
 for _ in range(count):
  child={'kind':'column','children':[]};n['children'].append(child);result.append(Container(self,child))
 return result
Recorder.columns=columns

def load(root):
 source=(root/'streamlit_app.py').read_text();tree=ast.parse(source);driver=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='initialize_state'];assert len(driver)==1
 rec=Recorder();ns={'__name__':'native_export'}
 with patch.dict(sys.modules,{'streamlit':rec}):exec(compile(''.join(source.splitlines(keepends=True)[:driver[0].lineno-1]),str(root/'streamlit_app.py'),'exec'),ns)
 return rec,ns

def flat(nodes):
 return sum([flat(n['children']) if n['kind'] in ['column','columns'] else [n] for n in nodes],[])
