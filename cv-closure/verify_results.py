"""Verify saved held-out metrics, selected epoch, source and model artifacts."""
import json,hashlib
from pathlib import Path
import numpy as np
from demo import verify
from ecg_split_guard import validate
p=Path(__file__).resolve().parent; out=p/'output';r=json.loads((out/'result.json').read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(p/'train.py')==r['source_sha256'];assert sha(p/'split.csv')==r['split_sha256'];validate(p/'split.csv')
assert r['selected_epoch']==min(r['history'],key=lambda x:x['validation_cross_entropy'])['epoch']
assert sum(sum(v) for v in r['counts'].values())==109438
assert all(len(v)==5 and min(v)>0 for v in r['counts'].values())
for name,h in r['artifacts_sha256'].items():
    if name=='model.pt' and not (out/name).exists():continue
    assert sha(out/name)==h,name
pred=np.load(out/'test_predictions.npz');m=np.bincount(5*pred['actual']+pred['predicted'],minlength=25).reshape(5,5)
assert m.tolist()==r['test']['confusion_matrix'];assert np.isclose(m.trace()/m.sum(),r['test']['accuracy'])
export=json.loads((out/'export_audit.json').read_text());assert sha(out/'replay_verified.json')==export['replay_verified_sha256'];assert export['model_sha256']==r['artifacts_sha256']['model.pt']
audit={'status':'passed','count':int(m.sum()),'all_five_classes_supported':True,'heldout_accuracy_recomputed':float(m.trace()/m.sum()),'model_export_bound_to_training_result':True,'numpy_reference_check':verify(out),'result_sha256':sha(out/'result.json')}
(out/'result_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
