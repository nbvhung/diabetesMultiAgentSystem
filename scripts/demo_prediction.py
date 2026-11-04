"""Three explicitly SYNTHETIC assessments; real MLP inference and PostgreSQL writes."""
from pathlib import Path
import os,sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from fastapi.testclient import TestClient
from backend.app.main import create_app

ROOT=Path(__file__).resolve().parents[1]
def main():
    url=os.environ['DATABASE_URL']
    engine=create_engine(url,hide_parameters=True)
    base=dict(pregnancies=0,glucose=100,blood_pressure=70,skin_thickness=20,insulin=50,bmi=22,diabetes_pedigree=0.3,age=30)
    records=[]
    try:
        with TestClient(create_app(prediction_enabled=True,engine=engine)) as client:
            assert client.get('/api/v1/models/current').status_code==200
            for n,assessment in enumerate([base,base|{'pregnancies':2,'glucose':140,'bmi':28,'age':45},base|{'glucose':85,'insulin':70,'bmi':24,'age':25}],1):
                response=client.post('/api/v1/mas/runs',json={'assessment':assessment,'is_synthetic':True})
                assert response.status_code==201,response.text
                run=response.json(); prediction=run['agent_results']['prediction']
                assert prediction['status']=='COMPLETED' and prediction['implementation']=='integrated'
                assert client.get('/api/v1/mas/runs/'+run['run_id']).json()==run
                trace=client.get('/api/v1/mas/runs/'+run['run_id']+'/trace').json()['agent_trace']
                record={'label':f'SYNTHETIC_CASE_{n}_NOT_REAL_PATIENT','run_id':run['run_id'],'model_version':prediction['output']['model_version'],'prediction_output':prediction['output'],'persisted_record_id':prediction['output']['persisted_record_id'],'agent_trace':trace}
                records.append(record); print(json.dumps(record,ensure_ascii=True))
        target=ROOT/'docs/validation/phase03/demo.json';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(records,indent=2),encoding='utf-8')
    finally: engine.dispose()
if __name__=='__main__': main()
