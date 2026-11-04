"""Offline research pipeline; never invoked by MAS in Phase 02."""
from pathlib import Path
import hashlib, json, random, platform, importlib.metadata
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

ROOT = Path(__file__).resolve().parents[3]
FEATURES = ['pregnancies','glucose','blood_pressure','skin_thickness','insulin','bmi','diabetes_pedigree','age']
ZERO_MISSING = ['glucose','blood_pressure','skin_thickness','insulin','bmi']
SEED = 42
VERSION = 'pima-mlp-0.2.0'
ART = ROOT/'artifacts/models'/VERSION
RES = ROOT/'experiments/results/phase02'
FIG = ROOT/'experiments/figures/phase02'
for p in (ART,RES,FIG): p.mkdir(parents=True,exist_ok=True)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save_json(path,obj): Path(path).write_text(json.dumps(obj,indent=2),encoding='utf-8')
def seed_all():
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)

def load_data():
    df=pd.read_csv(ROOT/'data/raw/pima.csv',header=None,names=FEATURES+['Outcome'])
    validate_data(df)
    return df

def validate_data(df):
    if df.shape != (768,9) or list(df.columns) != FEATURES+['Outcome']:
        raise ValueError('Expected standard 768 x 9 Pima dataset')
    values=df.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values<0).any() or set(df.Outcome.unique()) != {0,1}:
        raise ValueError('Invalid numeric data or binary target')
    for col in ['pregnancies','age','Outcome']:
        if not (df[col] == df[col].astype(int)).all(): raise ValueError('Expected integer '+col)

def split_indices(df):
    train,rest=train_test_split(np.arange(len(df)),test_size=0.30,stratify=df.Outcome,random_state=SEED)
    val,test=train_test_split(rest,test_size=0.5,stratify=df.Outcome.iloc[rest],random_state=SEED)
    return {k:v.tolist() for k,v in [('train',train),('validation',val),('test',test)]}

def features(df): return df[FEATURES].replace({c:{0:np.nan} for c in ZERO_MISSING})
def prepare():
    df=load_data(); splits=split_indices(df)
    pipeline=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler())])
    pipeline.fit(features(df).iloc[splits['train']])
    joblib.dump(pipeline,ART/'preprocessing.joblib')
    save_json(RES/'splits.json',splits)
    config={'seed':SEED,'features':FEATURES,'zero_as_missing':ZERO_MISSING,'imputer':'median','scaler':'StandardScaler','fit_partition':'train','dataset_sha256':sha(ROOT/'data/raw/pima.csv')}
    save_json(ART/'preprocessing_config.json',config)
    save_json(RES/'split_summary.json',{k:{'n':len(v),'positive':int(df.Outcome.iloc[v].sum())} for k,v in splits.items()})
    return df,splits,pipeline

def arrays():
    df=load_data(); splits=json.loads((RES/'splits.json').read_text())
    config=json.loads((ART/'preprocessing_config.json').read_text())
    assert sha(ROOT/'data/raw/pima.csv') == config['dataset_sha256']
    pipe=joblib.load(ART/'preprocessing.joblib')
    return {k:(pipe.transform(features(df).iloc[v]).astype('float32'),df.Outcome.iloc[v].to_numpy(dtype='float32')) for k,v in splits.items()}

class MLP(nn.Module):
    def __init__(self):
        super().__init__(); self.layers=nn.Sequential(nn.Linear(8,32),nn.ReLU(),nn.Dropout(0.15),nn.Linear(32,16),nn.ReLU(),nn.Linear(16,1))
    def forward(self,x): return self.layers(x).squeeze(-1)

def load_checkpoint():
    manifest=json.loads((ART/'manifest.json').read_text())
    for name,digest in manifest['sha256'].items():
        if sha(ART/name)!=digest: raise ValueError('Artifact checksum mismatch: '+name)
    checkpoint=torch.load(ART/'checkpoint.pt',map_location='cpu',weights_only=True)
    model=MLP(); model.load_state_dict(checkpoint['state_dict']); model.eval()
    return model

def train():
    from torch.utils.data import TensorDataset, DataLoader
    import matplotlib.pyplot as plt
    seed_all(); parts=arrays()
    x,y=parts['train']; vx,vy=map(torch.from_numpy,parts['validation'])
    loader=DataLoader(TensorDataset(torch.from_numpy(x),torch.from_numpy(y)),batch_size=32,shuffle=True,generator=torch.Generator().manual_seed(SEED))
    model=MLP(); optimizer=torch.optim.Adam(model.parameters(),lr=0.001)
    loss_fn=nn.BCEWithLogitsLoss(); best=float('inf'); stale=0; history=[]
    for epoch in range(1,201):
        model.train(); total=0.
        for bx,by in loader:
            optimizer.zero_grad(); loss=loss_fn(model(bx),by); loss.backward(); optimizer.step(); total+=loss.item()*len(by)
        model.eval()
        with torch.no_grad(): val=float(loss_fn(model(vx),vy))
        history.append({'epoch':epoch,'train_loss':total/len(y),'validation_loss':val})
        if val < best-1e-5:
            best=val; stale=0
            torch.save({'state_dict':model.state_dict(),'model_version':VERSION,'epoch':epoch,'input_features':FEATURES},ART/'checkpoint.pt')
        else: stale+=1
        if stale>=20: break
    config={'seed':SEED,'max_epochs':200,'early_stopping_patience':20,'min_delta':1e-5,'optimizer':'Adam','learning_rate':0.001,'batch_size':32,'loss':'BCEWithLogitsLoss','threshold':0.5,'architecture':[8,32,16,1],'dropout':0.15,'selection':'minimum validation loss','device':'cpu'}
    save_json(ART/'training_config.json',config)
    pd.DataFrame(history).to_csv(RES/'learning_history.csv',index=False)
    pd.DataFrame(history).set_index('epoch').plot(); plt.ylabel('BCE loss'); plt.tight_layout(); plt.savefig(FIG/'learning_curves.png'); plt.show(); plt.close()
    environment={'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in ['torch','scikit-learn','pandas','numpy','joblib','matplotlib','nbconvert']}}
    save_json(RES/'environment.json',environment)
    names=['checkpoint.pt','preprocessing.joblib','preprocessing_config.json','training_config.json']
    save_json(ART/'manifest.json',{'model_version':VERSION,'dataset_sha256':sha(ROOT/'data/raw/pima.csv'),'sha256':{p:sha(ART/p) for p in names},'environment':environment,'use':'research only; not clinical diagnosis'})
    print('Epochs executed:',len(history),'best validation loss:',best)
    return pd.DataFrame(history)

def evaluate():
    import matplotlib.pyplot as plt
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,brier_score_loss,ConfusionMatrixDisplay,RocCurveDisplay,PrecisionRecallDisplay
    from sklearn.calibration import CalibrationDisplay
    seed_all(); parts=arrays(); x,y=parts['train']; tx,ty=parts['test']
    model=load_checkpoint()
    with torch.no_grad(): scores={'MLP':torch.sigmoid(model(torch.from_numpy(tx))).numpy()}
    for name,baseline in [('LogisticRegression',LogisticRegression(max_iter=2000,random_state=SEED)),('RandomForest',RandomForestClassifier(n_estimators=300,min_samples_leaf=2,random_state=SEED,n_jobs=1))]:
        baseline.fit(x,y); scores[name]=baseline.predict_proba(tx)[:,1]
    metrics={}
    for name,score in scores.items():
        pred=(score>=0.5).astype(int)
        metrics[name]={'accuracy':accuracy_score(ty,pred),'precision':precision_score(ty,pred,zero_division=0),'recall':recall_score(ty,pred,zero_division=0),'f1':f1_score(ty,pred,zero_division=0),'roc_auc':roc_auc_score(ty,score),'pr_auc_average_precision':average_precision_score(ty,score),'brier_score':brier_score_loss(ty,score)}
        fig,axes=plt.subplots(2,2,figsize=(10,8))
        ConfusionMatrixDisplay.from_predictions(ty,pred,ax=axes[0,0])
        RocCurveDisplay.from_predictions(ty,score,ax=axes[0,1])
        PrecisionRecallDisplay.from_predictions(ty,score,ax=axes[1,0])
        CalibrationDisplay.from_predictions(ty,score,n_bins=5,strategy='quantile',ax=axes[1,1]); axes[1,1].plot([0,1],[0,1],'k--')
        fig.suptitle(name+' — held-out test, research only'); fig.tight_layout(); fig.savefig(FIG/(name+'_evaluation.png')); plt.show(); plt.close(fig)
        save_json(RES/(name+'_errors.json'),{'false_positive_indices':np.array(json.loads((RES/'splits.json').read_text())['test'])[(pred==1)&(ty==0)].tolist(),'false_negative_indices':np.array(json.loads((RES/'splits.json').read_text())['test'])[(pred==0)&(ty==1)].tolist()})
    save_json(RES/'metrics.json',metrics); frame=pd.DataFrame(metrics).T; frame.to_csv(RES/'metrics.csv',index_label='model')
    print('No test-driven threshold tuning. Calibration is assessed, not fitted on test.')
    return frame
