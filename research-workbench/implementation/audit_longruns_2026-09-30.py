"""Audit retrieved frozen batches; recompute ECG metrics from saved per-beat scores."""
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'data/longruns_20260930'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def close(a, b):
    assert math.isclose(a,b,rel_tol=0,abs_tol=1e-7),(a,b)

def confusion_check(result, matrix):
    matrix=np.asarray(matrix)
    assert matrix.shape==(4,4) and (matrix>=0).all()
    assert int(matrix.sum())==result['count']
    assert matrix.tolist()==result['confusion_matrix_rows_actual_columns_predicted']
    close(float(np.trace(matrix)/matrix.sum()),result['accuracy'])
    f1s=[]
    for i,c in enumerate('NSVF'):
        support=int(matrix[i].sum());predicted=int(matrix[:,i].sum());tp=int(matrix[i,i])
        assert support==result['per_class'][c]['support']
        if not support:continue
        precision=tp/predicted if predicted else 0.;recall=tp/support
        f1=2*tp/(support+predicted)
        for key,value in [('precision',precision),('recall',recall),('f1',f1)]:close(value,result['per_class'][c][key])
        f1s.append(f1)
    close(statistics.mean(f1s),result['macro_f1_present_classes'])

def distribution(rows, keys):
    return {k:{'mean':statistics.mean(r[k] for r in rows),
               'sample_sd':statistics.stdev(r[k] for r in rows),
               'min':min(r[k] for r in rows),'max':max(r[k] for r in rows)} for k in keys}

def run():
    lm_root=ROOT/'language_model';ecg_root=ROOT/'ecg'
    lm_manifest=json.loads((lm_root/'batch_manifest.json').read_text())
    ecg_path=ecg_root/'ecg_longrun_manifest_2026-09-29.json'
    ecg_manifest=json.loads(ecg_path.read_text())
    assert sha(ecg_path)==sha(BASE/ecg_path.name)
    assert sha(lm_root/'batch_manifest.json')==sha(BASE/'autoresearch_longrun_20260929/batch_manifest.json')
    for root,manifest in [(lm_root,lm_manifest),(ecg_root,ecg_manifest)]:
        for file,digest in manifest['source_sha256'].items():assert sha(root/file)==digest,file
    lm_rows=[];ecg_rows=[]
    for cell in lm_manifest['cells']:
        path=lm_root/Path(cell['candidate_file']).parent/'output'
        r=json.loads((path/'result.json').read_text());v=json.loads((path/'verified.json').read_text())
        assert r['status']=='success' and v['verified'] is True
        assert sha(lm_root/cell['candidate_file'])==cell['train_sha256']==r['train_sha256']
        assert sha(path/'model.pt')==r['checkpoint_sha256']==v['checkpoint_sha256']
        assert r['prepare_sha256']==lm_manifest['prepare_sha256']
        assert sha(lm_root/'data/data_manifest.json')==r['data_manifest_sha256']==lm_manifest['data_manifest_sha256']
        assert r['seed']==cell['seed'] and r['configuration']==cell['configuration']
        assert 1200<=r['training_seconds']<=1210
        assert r['validation_bytes_scored']==v['validation_bytes_scored']==2097152
        assert abs(r['val_bpb']-v['independent_val_bpb'])<=1e-5
        lm_rows.append({'id':cell['id'],'configuration':cell['configuration'],'seed':cell['seed'],
                        **{k:r[k] for k in ['val_bpb','training_seconds','steps','parameter_count','gpu_peak_bytes']}})
    for cell in ecg_manifest['cells']:
        path=ecg_root/'output'/cell['id'];r=json.loads((path/'result.json').read_text())
        assert r['status']=='success' and r['cell']==cell
        assert r['batch_manifest_sha256']==sha(ecg_path)
        assert sha(path/'best.pt')==r['checkpoint_sha256']
        assert r['epochs_completed']==100 and len(r['history'])==100
        assert r['history']==json.loads((path/'history.json').read_text())
        best=min(r['history'],key=lambda v:v['validation_unweighted_ce'])
        assert r['selected_epoch']==best['epoch']
        close(r['selected_validation_ce'],best['validation_unweighted_ce'])
        for split in ['validation','test']:
            z=np.load(path/f'{split}_scores.npz',allow_pickle=False)
            y,p,subjects=z['y'],z['p'],z['subject']
            assert len(y)==cell['expected'][split] and p.shape==(len(y),4)
            assert np.isfinite(p).all() and (p>=0).all() and np.allclose(p.sum(1),1,atol=1e-5)
            pred=p.argmax(1);matrix=np.zeros((4,4),dtype=int)
            np.add.at(matrix,(y,pred),1)
            confusion_check(r['metrics'][split],matrix)
            true_prob=p[np.arange(len(y)),y].astype(np.float64)
            assert (true_prob>0).all(), 'saved probabilities underflow; logits needed for exact CE'
            ce=float(-np.log(true_prob).mean())
            assert abs(ce-r['metrics'][split]['cross_entropy'])<1e-5
            assert set(r['metrics'][split]['per_subject'])==set(subjects.tolist())
            for subject in set(subjects.tolist()):
                mask=subjects==subject;cm=np.zeros((4,4),dtype=int)
                np.add.at(cm,(y[mask],pred[mask]),1)
                confusion_check(r['metrics'][split]['per_subject'][subject],cm)
        incart=r['metrics']['incart'];assert incart['count']==175777
        confusion_check(incart,incart['confusion_matrix_rows_actual_columns_predicted'])
        row={'id':cell['id'],'split':cell['id'][0],'model':cell['model'],'seed':cell['seed'],
             'selected_epoch':r['selected_epoch'],'elapsed_seconds':r['elapsed_seconds'],
             'parameter_count':r['parameter_count'],'gpu_peak_bytes':r['gpu_peak_bytes'],
             'mitdb_macro_f1':r['metrics']['test']['macro_f1_present_classes'],
             'incart_macro_f1':incart['macro_f1_present_classes']}
        for source,result in [('mitdb',r['metrics']['test']),('incart',incart)]:
            for c in 'SF':
                for metric in ['precision','recall','f1']:row[f'{source}_{c}_{metric}']=result['per_class'][c][metric]
        ecg_rows.append(row)
    lm_groups=defaultdict(list);ecg_groups=defaultdict(list)
    for r in lm_rows:lm_groups[r['configuration']].append(r)
    for r in ecg_rows:ecg_groups[r['split']+'_'+r['model']].append(r)
    result={'status':'passed','language_model_cells':lm_rows,'ecg_cells':ecg_rows,
            'language_model_groups':{k:distribution(v,['val_bpb','steps','training_seconds']) for k,v in lm_groups.items()},
            'ecg_groups':{k:distribution(v,['mitdb_macro_f1','incart_macro_f1','incart_S_precision','incart_S_recall','incart_F_precision','incart_F_recall']) for k,v in ecg_groups.items()},
            'limits':'LM independent GPU rescoring was performed by pinned verifier during original jobs; local audit checks those records and hashes. ECG MIT scores are independently recomputed; INCART aggregate/per-class consistency is checked from saved confusion matrices, not a new external inference run.'}
    (BASE/'longrun_audit_2026-09-30.json').write_text(json.dumps(result,indent=2)+'\n')
    manifest={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file()}
    (BASE/'longrun_retrieval_hashes_2026-09-30.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','language_model_groups','ecg_groups']},indent=2))

if __name__=='__main__':run()
