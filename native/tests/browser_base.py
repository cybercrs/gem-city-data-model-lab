"""Actual local Chromium QA under /js/ with outside requests blocked."""
import json,threading,time,sys,gzip
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  path=urlsplit(path).path
  if path.startswith('/js/'):path=path[3:]
  return super().translate_path(path)
 def log_message(self,*a):pass

def run(walk,session_only=False):
 dist=ROOT/'dist';handler=lambda *a,**kw:Handler(*a,directory=str(dist),**kw);server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}/js/'
 results={'checks':[],'console_errors':[],'page_errors':[],'external_requests':[],'http_errors':[],'hosted_ui_tested':False};screens=OUT
 def passed(name):results['checks'].append({'name':name,'status':'passed'});print('PASSED:',name,flush=True)
 def ready(page):page.wait_for_function("document.documentElement.dataset.ready==='true' && document.documentElement.dataset.saving!=='true'")
 def click(page,name):page.get_by_role('button',name=name,exact=True).click();ready(page)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,proxy={'server':'http://127.0.0.1:9','bypass':'127.0.0.1,localhost'})
  context=browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True);page=context.new_page()
  page.on('console',lambda m:results['console_errors'].append(m.text) if m.type=='error' else None);page.on('pageerror',lambda e:results['page_errors'].append(str(e)))
  page.on('request',lambda r:results['external_requests'].append(r.url) if not r.url.startswith(origin[:-4]) and not r.url.startswith(('data:','blob:')) else None)
  page.on('response',lambda r:results['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  start=time.perf_counter();page.goto(origin);ready(page);elapsed=(time.perf_counter()-start)*1000
  page.screenshot(path=str(screens/'briefing-desktop.png'),full_page=True);assert page.get_by_role('button',name='Forward',exact=True).is_disabled();passed('Native /js/ cold initialization with forward locked')
  walk(page,origin,ready,click,passed,screens)
  ready(page);saved=page.url;before=parse_qs(urlsplit(saved).query).get('progress');current=page.locator('html').get_attribute('data-reached')
  for _ in range(int(current)):click(page,'Back')
  assert page.locator('html').get_attribute('data-view')=='0';assert page.get_by_role('button',name='Start over',exact=True).is_disabled();assert all(n.is_disabled() for n in page.locator('input,select,textarea').all());assert before==parse_qs(urlsplit(page.url).query).get('progress')
  for _ in range(int(current)):click(page,'Forward')
  assert page.get_by_role('button',name='Forward',exact=True).is_disabled();assert before==parse_qs(urlsplit(page.url).query).get('progress');passed('All reached pages review readonly; forward capped; progress token unchanged')
  page.get_by_role('button',name='Back',exact=True).focus();page.keyboard.press('Tab');page.keyboard.press('Shift+Tab');button=page.get_by_role('button',name='Back',exact=True);assert button.evaluate('(n)=>getComputedStyle(n).outlineStyle')!='none';page.keyboard.press('Enter');ready(page);assert int(page.locator('html').get_attribute('data-view'))==int(current)-1;click(page,'Forward');passed('Keyboard focus ring and Enter navigation')
  page.set_viewport_size({'width':390,'height':844});page.mouse.move(0,0);page.screenshot(path=str(screens/'complete-narrow.png'),full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');sizes=page.get_by_role('button',name='Back',exact=True).bounding_box();assert sizes['width']>=44 and sizes['height']>=44;passed('390px layout, no page overflow, 44px navigation touch targets');page.set_viewport_size({'width':1280,'height':900});page.screenshot(path=str(screens/'complete-desktop.png'),full_page=True)
  separate=browser.new_context();fresh=separate.new_page();fresh.goto(origin);ready(fresh);assert fresh.locator('html').get_attribute('data-reached')=='0';passed('Independent sessions start fresh');separate.close()
  page.goto(saved);ready(page);assert page.locator('html').get_attribute('data-reached')==('0' if session_only else current);passed('Refresh/bookmark behavior matches original saving design')
  page.goto(origin+'?view=999&progress=malformed');ready(page);assert page.locator('html').get_attribute('data-reached')=='0';assert page.get_by_role('button',name='Forward',exact=True).is_disabled();click(page,'Start over');page.reload();ready(page);assert page.locator('html').get_attribute('data-view')=='0';passed('Malformed/future bookmarks and reset remain fresh')
  assert not any(results[k] for k in ['console_errors','page_errors','external_requests','http_errors']),results;passed('No external requests, asset failures, or browser execution errors')
  manifest=json.loads((dist/'manifest.json').read_text());results['measurement']={'local_cold_navigation_to_ready_ms':round(elapsed,1),'viewport':'1280x900','browser':browser.version,'browser_context':'new context; local loopback HTTP; no simulated network latency; cache empty','application_bytes':manifest['application_bytes'],'gzip_bytes_sum':sum(len(gzip.compress((dist/f).read_bytes(),mtime=0)) for f in manifest['files']),'capacity_claim':False};results['not_run']=['Hosted UI: known proxy denial','Physical classroom devices/network','Classroom concurrent capacity'];browser.close()
 server.shutdown();(OUT/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
