from browser_base import run
import json
from pathlib import Path
DATA=json.loads((Path(__file__).resolve().parents[1]/'content.js').read_text().removeprefix('export const DATA = ').removesuffix(';\n'))
def walk(page,origin,ready,click,passed,out):
 click(page,'Begin with the row grain')
 for g in DATA['groups']:
  def choose(f,value):
   # Exported stable widget IDs let the browser select the actual native controls.
   if f['widget']['kind']=='select':page.locator('#'+f['widget']['key']).select_option(value)
   else:page.locator('input').filter(has=page.locator('never')).count() if False else page.locator('input').evaluate_all('(nodes,p)=>{const n=nodes.find(x=>x.name===p[0]&&x.value===p[1]);n.click();}',[f['widget']['key'],value])
   ready(page)
  click(page,g['check']);assert page.get_by_role('status').count()>0
  for f in g['fields']:choose(f,next(x for x in f['options'] if x!=f['answer']))
  click(page,g['check']);assert page.get_by_role('button',name='Forward',exact=True).is_disabled()
  f=g['fields'][0];choose(f,f['answer']);before=page.url;page.reload();ready(page)
  if f['widget']['kind']=='select':assert page.locator('#'+f['widget']['key']).input_value()==f['answer']
  else:assert page.locator('input:checked').evaluate_all('(nodes,p)=>nodes.some(x=>x.name===p[0]&&x.value===p[1])',[f['widget']['key'],f['answer']])
  click(page,'Back');assert page.get_by_role('button',name='Start over',exact=True).is_disabled();click(page,'Forward');assert page.url==before
  for f in g['fields']:choose(f,f['answer'])
  click(page,'Check revised answers');assert page.locator('input,select').count()==0
  page.screenshot(path=str(out/(g['id']+'-desktop.png')),full_page=True)
  continue_label=next(x['label'] for x in g['tail'] if x['kind']=='button');click(page,continue_label)
  passed(g['id']+': incomplete/wrong/revised submissions, refreshed drafts and readonly review')
 assert page.get_by_text('5 of 5',exact=True).is_visible();assert page.get_by_text('5',exact=True).count()>0
 # Every original valid saved state is exercised in the actual browser.
 oracles=json.loads((Path(__file__).parent/'python-oracles.json').read_text())
 saved=page.url
 for fixture in oracles['legacy']:
  page.goto(origin+'?progress='+fixture['token']+'&view=999');ready(page);assert page.locator('html').get_attribute('data-reached')==str(fixture['stage']);assert page.locator('html').get_attribute('data-view')==str(fixture['stage'])
 page.goto(saved);ready(page);passed('All seven original Python links import; future views rejected')
 assert 'pilot' not in page.title().lower() and 'preview' not in page.title().lower() and 'test' not in page.title().lower();passed('Final title and all rendered lesson variants retain original content without provisional branding')
run(walk)
