"""Run the REAL lab agent, independently per case; no canned model responses."""
from pathlib import Path
import argparse
import json
import shutil
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
STAGES = {'00':'stage-00-chat','01':'stage-01-files','02':'stage-02-skills'}
QUESTIONS = {
 'A':'Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?',
 'B':'Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?',
 'missing':'Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026.',
 'boundary_old':'Tôi mua ngày 24/09/2026, yêu cầu hoàn ngày 01/10/2026, chưa kích hoạt. Tôi có được hoàn không?',
 'boundary_new':'Tôi mua ngày 01/10/2026, yêu cầu hoàn ngày 15/10/2026, chưa kích hoạt. Tôi có được hoàn không?',
 'activated':'Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, đã kích hoạt. Tôi có được hoàn không?',
}


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--stage',choices=STAGES,default='02')
 p.add_argument('--case',choices=['all',*QUESTIONS,'A_renamed','B_renamed'],default='all')
 args=p.parse_args()
 stage=ROOT/STAGES[args.stage]
 sys.path.insert(0,str(stage))
 from config import load_settings, RECURSION_LIMIT
 from agent import build_agent, build_model
 from observer import Observer
 from langchain_core.messages import HumanMessage
 import paths
 settings, missing=load_settings()
 if missing:
  p.exit(2,'Thiếu cấu hình: '+', '.join(missing)+'. Điền .env cục bộ trong stage; không nộp .env.\n')
 cases=list(QUESTIONS)+['A_renamed','B_renamed'] if args.case=='all' else [args.case]
 out=ROOT/'evidence'/'live';out.mkdir(parents=True,exist_ok=True)
 failed=False
 for case in cases:
  question=QUESTIONS[case.replace('_renamed','')]
  # New workspace and agent per case: no old messages/checkpoints or stale names.
  with tempfile.TemporaryDirectory(prefix='refund-lab-') as td:
   workspace=Path(td)/'workspace'
   if args.stage!='00':
    shutil.copytree(stage/'workspace',workspace)
    if case.endswith('_renamed'):
     policy_dir=workspace/'data/policies'
     for i, source in enumerate(sorted(policy_dir.glob('*.md'))):
      source.rename(policy_dir/f'document-{uuid.uuid4().hex[:10]}-{i}.md')
    paths.WORKSPACE_DIR=workspace
   observer=Observer(conversation_id=uuid.uuid4().hex)
   observer.start_turn(uuid.uuid4().hex)
   trace=out/f'stage{args.stage}_{case}.jsonl'
   def record(kind,data):
    event=observer.record(kind,data)
    with trace.open('a',encoding='utf-8') as f:
     f.write(json.dumps(event,ensure_ascii=False,default=str)+'\n')
   trace.write_text('',encoding='utf-8')
   record('user_submitted',{'content':question,'case':case,'execution':'real_model'})
   messages=[]
   try:
    agent=build_agent(build_model(settings))
    for mode,chunk in agent.stream({'messages':[HumanMessage(content=question)]},
         config={'recursion_limit':RECURSION_LIMIT},stream_mode=['custom','values']):
     if mode=='custom' and chunk.get('observer'):
      record(chunk['event'],chunk['data'])
     elif mode=='values': messages=chunk.get('messages',messages)
    observer.sync_messages(messages)
    final=messages[-1].content if messages else ''
    record('run_completed',{'final_answer':final,'messages':observer.messages})
    print(f'{args.stage} {case}: {trace.relative_to(ROOT)}')
   except Exception as exc:
    # Avoid leaking request headers/credentials through exception strings.
    record('run_failed',{'error':type(exc).__name__})
    print(f'{args.stage} {case}: FAILED ({type(exc).__name__}); kiểm tra endpoint và cấu hình cục bộ.')
    failed=True
   events=[json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines()]
   index=['# Vị trí bằng chứng — '+trace.name,'','Đây là vị trí sự kiện thực tế; cần đọc câu trả lời để đánh giá, không tự động coi là PASS.','']
   for i,e in enumerate(events,1):
    kind=e['type']
    if kind=='tool_finished':
     r=e.get('result',{})
     index.append(f"- Dòng {i}: {kind}, {e.get('tool_name')}, path={r.get('path') if isinstance(r,dict) else ''}, ok={r.get('ok') if isinstance(r,dict) else ''}.")
    elif kind in ['model_request','run_completed','run_failed']:
     index.append(f'- Dòng {i}: {kind}.')
   trace.with_suffix('.index.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
 return 1 if failed else 0

if __name__=='__main__':
 raise SystemExit(main())
