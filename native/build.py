"""Package the native app under /js/ without changing the existing site root."""
import argparse,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def build(output):
 output.mkdir(parents=True,exist_ok=True);files={}
 for p in sorted(HERE.rglob('*')):
  rel=p.relative_to(HERE)
  if not p.is_file() or any(x in rel.parts for x in ['tests','review','test-results','dist','__pycache__']):continue
  if p.suffix not in ['.js','.mjs','.html','.css','.wasm','.txt','.json'] or p.name in ['package.json','eslint.config.js']:continue
  target=output/rel;target.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();target.write_bytes(data);files[str(rel)]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 manifest={'entrypoint':'index.html','canonical_directory':'js/','files':files,'application_bytes':sum(f['bytes'] for f in files.values()),'python_runtime':False}
 (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'dist');a=p.parse_args();build(a.output)
