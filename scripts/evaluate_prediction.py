"""E1: frozen Phase 02 MLP vs train-only fitted baselines, identical held-out indices."""
from phase07_common import *
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score
from backend.app.ml.pipeline import arrays, load_checkpoint, seed_all


def main():
    seed_all()
    parts = arrays(); x, y = parts['train']; tx, ty = parts['test']
    with torch.inference_mode():
        scores = {'MLP': torch.sigmoid(load_checkpoint()(torch.from_numpy(tx))).numpy()}
    for name, model in [('LogisticRegression', LogisticRegression(max_iter=2000, random_state=SEED)), ('RandomForest', RandomForestClassifier(n_estimators=300, min_samples_leaf=2, random_state=SEED, n_jobs=1))]:
        model.fit(x, y); scores[name] = model.predict_proba(tx)[:, 1]
    indices = json.loads((RES / 'phase02/splits.json').read_text())['test']
    summary = []; rows = []
    for name, score in scores.items():
        pred = (score >= .5).astype(int)
        summary.append(dict(model=name, accuracy=accuracy_score(ty,pred), precision=precision_score(ty,pred,zero_division=0), recall=recall_score(ty,pred,zero_division=0), f1=f1_score(ty,pred,zero_division=0), roc_auc=roc_auc_score(ty,score), pr_auc=average_precision_score(ty,score)))
        rows.extend(dict(model=name, test_index=int(idx), target=int(target), score=float(value), predicted_class=int(value>=.5)) for idx,target,value in zip(indices,ty,score))
    plot_bars('prediction',summary,'model',['f1','roc_auc','pr_auc'],'E1 / held-out research prediction; same 116 test rows')
    save('prediction',summary,rows,'Restricted historical Pima cohort; research only, no clinical generalization.', datasets=['data/raw/pima.csv','experiments/results/phase02/splits.json','artifacts/models/pima-mlp-0.2.0/manifest.json'],config={'threshold':.5,'test_size':len(ty),'preprocessing':'frozen train-only imputer/scaler','mlp':'frozen checkpoint; no retraining','rf_estimators':300,'rf_min_samples_leaf':2,'logistic_max_iter':2000,'pr_auc_definition':'average precision'})

if __name__ == '__main__': main()
