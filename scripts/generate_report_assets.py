"""Render architecture from explicit specifications; copy only measured charts.

No chart values or trace events are synthesized. Diagram layouts are explanatory,
not measurements. Source inventory and captions are exported with SHA256.
"""
from pathlib import Path
import ast,csv,hashlib,json,shutil
from datetime import datetime,timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/report/figures'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def diagram(name,nodes,edges,title,source):
    fig,ax=plt.subplots(figsize=(12,7));ax.set(xlim=(0,12),ylim=(0,8));ax.axis('off')
    for key,(x,y,label) in nodes.items():
        ax.add_patch(FancyBboxPatch((x-.92,y-.38),1.84,.76,boxstyle='round,pad=.08',facecolor='#ecfdf5',edgecolor='#0d9488',lw=1.1,zorder=2))
        ax.text(x,y,label,ha='center',va='center',fontsize=9,color='#123e35',zorder=3)
    for start,end,label in edges:
        x,y,_=nodes[start];xx,yy,_=nodes[end]
        dx,dy=xx-x,yy-y
        scale=max(abs(dx)/1.05,abs(dy)/.52,1)
        ax.annotate('',xy=(xx-dx/scale,yy-dy/scale),xytext=(x+dx/scale,y+dy/scale),arrowprops={'arrowstyle':'->','color':'#628376','lw':1.15},zorder=1)
        if label:ax.text((x+xx)/2,(y+yy)/2+.12,label,ha='center',fontsize=7,color='#587365',bbox={'facecolor':'white','edgecolor':'none','alpha':.9},zorder=4)
    ax.set_title(title,fontsize=13,pad=12,color='#123e35');fig.tight_layout();fig.savefig(OUT/f'{name}.png',dpi=170);plt.close(fig)
    (OUT/f'{name}.source.json').write_text(json.dumps({'nodes':nodes,'edges':edges,'source':source},indent=2,ensure_ascii=False),encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    specs=[
      ('architecture',{'ui':(1.4,6.8,'React / TypeScript'),'api':(4,6.8,'FastAPI v2'),'co':(7,6.8,'Coordinator'),'s':(10.4,6.8,'Safety\ninput + output'),'p':(2,4.3,'Prediction\nMLP frozen'),'k':(5,4.3,'Knowledge\nKG / RAG'),'r':(8,4.3,'RL decision\nQ-policy'),'e':(10.6,4.3,'Education\nGroq / extractive'),'v':(9.4,2,'Verifier\nsource + review'),'sql':(2,1.3,'PostgreSQL\nrun / prediction / trace'),'kg':(5,1.3,'Neo4j\nversioned sources')},[('ui','api','HTTP'),('api','co','task'),('co','s','gates'),('co','p',''),('co','k',''),('co','r',''),('co','e',''),('k','kg','read'),('p','sql','transaction'),('e','v','candidate'),('v','co','accept / repair'),('co','sql','persist')],'Kiến trúc hệ đa agent Diabetes MAS','backend/app/research/api.py; agents.py; coordinator.py; db/migrations'),
      ('communication',{'c':(6,4,'Coordinator\nrun-local state'),'p':(2,6.5,'Prediction'),'k':(6,6.5,'Knowledge'),'r':(10,6.5,'RL decision'),'e':(2,1.5,'Education'),'v':(6,1.5,'Verifier'),'s':(10,1.5,'Safety')},[('c','p','PredictionTask / Result'),('c','k','KnowledgeTask / Result'),('c','r','RLTask / Result'),('c','e','EducationTask / Result'),('c','v','VerifierTask / Result'),('c','s','SafetyTask / Decision')],'Giao tiếp qua typed messages; agent không tự gọi agent khác','backend/app/research/schemas.py; agents.py; coordinator.py'),
      ('erd',{'case':(2,6.5,'demo_cases\nid PK; synthetic=true'),'a':(2,4,'assessments\ncase FK; features JSON'),'m':(6,6.5,'model_versions\nid PK; version; SHA256'),'p':(6,4,'predictions\nscore; class; result JSON'),'w':(10,4,'workflow_runs\nstatus; response JSON'),'e':(10,1.5,'agent_events\nrun FK; seq; event JSON')},[('case','a','1 : N'),('a','p','1 : N'),('m','p','1 : N'),('w','p','1 : N'),('w','e','1 : N; unique(run,seq)')],'Lược đồ PostgreSQL sau migration 0002_phase03','backend/app/db/migrations/versions/0001_phase02.py; 0002_phase03.py'),
      ('neo4j_schema',{'s':(2,6.5,'DiabetesSource\nURL / publisher / version'),'c':(6,6.5,'DiabetesEvidence\nSHA256 / release / quote'),'t':(10,6.5,'DiabetesTopic'),'a':(6,3.5,'DiabetesAssertion\nsubject / predicate / quote'),'sub':(2,1,'DiabetesConcept\nsubject'),'obj':(10,1,'DiabetesConcept\nobject')},[('s','c','HAS_CHUNK'),('t','c','SUPPORTED_BY'),('a','c','SUPPORTED_BY'),('sub','a','SUBJECT_OF'),('a','obj','OBJECT'),('sub','obj','typed relation + release')],'Neo4j: tài liệu, đoạn nguồn và assertion có provenance','backend/app/research/graph.py; corpus.py'),
      ('e2e_workflow',{'u':(2,6.8,'Synthetic assessment\n+ diabetes question'),'s1':(6,6.8,'Safety input'),'p':(10,6.8,'Prediction\nMLP / score'),'k':(10,4.4,'Knowledge\nevidence / retry'),'r':(6,4.4,'RL\naction / fallback'),'e':(2,4.4,'Education\nclaims / extractive'),'v':(2,2,'Verifier\naccept / repair'),'s2':(6,2,'Safety output\nallow / veto'),'db':(10,2,'SQL commit\nReact results')},[('u','s1',''),('s1','p','allow'),('p','k',''),('k','r',''),('r','e',''),('e','v',''),('v','s2','admitted'),('s2','db','release')],'Luồng demo; Coordinator quản lý mọi chuyển bước','backend/app/research/coordinator.py; repository.py')]
    for name,nodes,edges,title,source in specs:
        diagram(name,nodes,edges,title,source);records.append({'file':f'{name}.png','caption':title,'source':source,'kind':'code-derived explanatory diagram'})
    # Sequence diagram: fixed message order from actual Coordinator and persistence code.
    names=['React','FastAPI','Coordinator','Agents','PostgreSQL']
    messages=[(0,1,'POST /api/v2/mas/runs'),(1,2,'validate + warmup'),(2,3,'Safety input'),(3,2,'allow / veto'),(2,3,'Prediction → Knowledge → RL'),(3,2,'score / evidence / action'),(2,3,'Education → Verifier'),(3,2,'proof / reason codes'),(2,3,'Safety output'),(3,2,'allow / warning / block'),(2,1,'WorkflowResponse'),(1,4,'snapshot + prediction + events; COMMIT'),(1,0,'201 only after commit'),(0,1,'GET run / trace'),(1,4,'read persisted version'),(1,0,'run + ordered trace')]
    fig,ax=plt.subplots(figsize=(12,9));ax.axis('off');ax.set(xlim=(-.5,4.5),ylim=(-1,19))
    for x,name in enumerate(names):ax.text(x,18,name,ha='center',fontsize=11,color='#047857');ax.plot([x,x],[0,17.5],ls='--',lw=.7,color='#9cb5a9')
    for i,(a,b,label) in enumerate(messages):
        y=16.8-i;ax.annotate('',xy=(b,y),xytext=(a,y),arrowprops={'arrowstyle':'->','lw':1,'color':'#426e5a'});ax.text((a+b)/2,y+.15,f'{i+1}. {label}',ha='center',fontsize=8,color='#264d39',bbox={'facecolor':'white','edgecolor':'none','pad':1})
    fig.tight_layout();fig.savefig(OUT/'sequence.png',dpi=170);plt.close(fig)
    records.append({'file':'sequence.png','caption':'Sequence diagram: phản hồi HTTP sau transaction commit','source':'backend/app/research/api.py; coordinator.py; repository.py','kind':'code-derived explanatory diagram'})
    charts={'dl_training':('experiments/figures/phase02/learning_curves.png','BCE train/validation: lịch sử huấn luyện thật, checkpoint epoch 24'), 'prediction_evaluation':('experiments/figures/prediction.png','MLP và baseline trên cùng test split'), 'prediction_diagnostics':('experiments/figures/phase02/MLP_evaluation.png','Confusion matrix, ROC, PR và reliability của MLP'), 'rag_evaluation':('experiments/figures/diabetes_rag.png','Các chiến lược truy hồi; phân biệt development/diagnostic/confirmatory'), 'mas_evaluation':('experiments/figures/diabetes_mas.png','MAS so với direct workflow; khác retry budget, không kết luận nhân quả'), 'rl_rewards':('experiments/figures/phase06/reward_curves.png','Reward curves theo lịch sử ba seed huấn luyện'), 'rl_evaluation':('experiments/figures/rl.png','Policy phục vụ Q-learning và rule baseline trong simulator'), 'safety_summary':('experiments/figures/diabetes_safety.png','Finite software safety scenarios; không phải clinical certification'), 'llm_evaluation':('experiments/figures/diabetes_llm.png','Groq thực: verifier acceptance có điều kiện trên output LLM')}
    for name,(source,caption) in charts.items():
        if (ROOT/source).exists():shutil.copy2(ROOT/source,OUT/f'{name}.png');records.append({'file':f'{name}.png','caption':caption,'source':source,'source_sha256':sha(ROOT/source),'kind':'existing measured artifact; not rerun unless manifest says so'})
    for name in ['public-overview','public-answer','public-monitor','public-mobile']:
        source=ROOT/f'docs/validation/phase08/{name}.png'
        if source.exists():shutil.copy2(source,OUT/f'{name}.png');records.append({'file':f'{name}.png','caption':'Ảnh trình duyệt thật qua HTTPS tạm: '+name,'source':source.relative_to(ROOT).as_posix(),'kind':'actual browser screenshot'})
    live=ROOT/'docs/validation/phase08/public_demo.json'
    if live.exists():
        run=json.loads(live.read_text(encoding='utf-8'))['runs'][0]['run'];events=run['agent_trace']
        fig,ax=plt.subplots(figsize=(12,max(5,len(events)*.28)));ax.axis('off')
        for i,event in enumerate(events):
            label=f"{event['sequence']:02d}  {event.get('agent_id') or 'Coordinator':12}  {event['status']:10}  {event['reason']}"
            ax.text(.01,1-(i+.5)/len(events),label,fontsize=8,color='#047857' if event.get('agent_id') is None else '#273c32',transform=ax.transAxes)
        ax.set_title('Trace thực tế — Run '+run['run_id'],fontsize=11);fig.tight_layout();fig.savefig(OUT/'actual_trace.png',dpi=170);plt.close(fig)
        records.append({'file':'actual_trace.png','caption':'Trace các quyết định thật của workflow HTTPS, không phải timeline mô phỏng','source':'docs/validation/phase08/public_demo.json','kind':'actual ordered trace rendering'})
    (OUT/'catalog.json').write_text(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(),'figures':[{**r,'sha256':sha(OUT/r['file'])} for r in records]},indent=2,ensure_ascii=False),encoding='utf-8')
    sources=[]
    for folder in ['backend','scripts','frontend/src','infra']:
        for path in sorted((ROOT/folder).rglob('*')):
            if path.suffix not in ('.py','.ts','.tsx','.css','.cjs','.ps1','.yaml','.txt','.Dockerfile') or '__pycache__' in path.parts:continue
            text=path.read_text(encoding='utf-8-sig')
            entry={'path':path.relative_to(ROOT).as_posix(),'lines':len(text.splitlines()),'sha256':sha(path)}
            if path.suffix=='.py':
                module=ast.parse(text);entry['symbols']=[node.name for node in module.body if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))]
            sources.append(entry)
    (ROOT/'docs/report/source_inventory.json').write_text(json.dumps(sources,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Rendered/copied',len(records),'figures; inventoried',len(sources),'source files.')

if __name__=='__main__':main()
