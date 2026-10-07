"""Capture real direct tool results using only synthetic files; no LLM."""
from pathlib import Path
import argparse
import json
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['01','02'],default='02');args=p.parse_args()
sys.path.insert(0,str(ROOT/('stage-01-files' if args.stage=='01' else 'stage-02-skills')))
from tools import list_files
import paths
out=ROOT/'evidence'/f'direct_tools_stage{args.stage}.jsonl'
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'workspace';root.mkdir();paths.WORKSPACE_DIR=root
 (root/'data').mkdir();(root/'data/demo.md').write_text('Synthetic test document',encoding='utf-8')
 (root/'data/subdir').mkdir();(root/'data/subdir/nested.md').write_text('Nested synthetic file',encoding='utf-8')
 records=[]
 def check(name,path,expected):
  result=json.loads(list_files.invoke({'path':path}))
  actual='OK' if result['ok'] else result['error']['code']
  assert actual==expected,(name,result)
  records.append({'execution':'direct_tool_not_model','case':name,'arguments':{'path':path},'result':result,'passed':True})
 check('valid','data','OK')
 check('file','data/demo.md','NOT_A_DIRECTORY')
 check('missing','data/missing','DIRECTORY_NOT_FOUND')
 check('traversal','../fake-outside','PATH_OUTSIDE_WORKSPACE')
 check('absolute',str(root/'data'),'PATH_OUTSIDE_WORKSPACE')
 outside=Path(tmp)/'fake-outside';outside.mkdir()
 try:
  (root/'escape').symlink_to(outside,target_is_directory=True)
 except (OSError,NotImplementedError):
  records.append({'case':'symlink','status':'SKIPPED','reason':'OS does not allow test symlink'})
 else:
  check('symlink_outside','escape','PATH_OUTSIDE_WORKSPACE')
  check('listing_contains_outside_link','.','PATH_OUTSIDE_WORKSPACE')
 (root/'data/demo.md').rename(root/'data/renamed.md')
 check('renamed','data','OK')
 out.parent.mkdir(exist_ok=True)
 out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
 print(out)
