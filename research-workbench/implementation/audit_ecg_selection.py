"""Verify paired checkpoint selection against saved development probabilities."""
import json
import statistics
from collections import defaultdict
from pathlib import Path
import numpy as np
from importlib.util import spec_from_file_location, module_from_spec

BASE = Path(__file__).resolve().parent
spec = spec_from_file_location('longrun_audit', BASE/'audit_longruns_2026-09-30.py')
audit = module_from_spec(spec)
spec.loader.exec_module(audit)

def run():
    root = BASE/'data/ecg_selection_20260930'
    manifest_path = BASE/'ecg_selection_manifest_2026-09-30.json'
    manifest = json.loads(manifest_path.read_text())
    rows, pairs = [], []
    for cell in manifest['cells']:
        directory = root/cell['id']
        history = json.loads((directory/'history.json').read_text())
        assert len(history) == 100
        old = BASE/'data/longruns_20260930/ecg/output'/cell['id']/'history.json'
        histories_identical = history == json.loads(old.read_text())
        cell_rows = {}
        for policy in ['ce', 'macro']:
            path = directory/policy
            r = json.loads((path/'result.json').read_text())
            assert r['status'] == 'success' and r['policy'] == policy and r['cell'] == cell
            assert r['history'] == history and r['epochs_completed'] == 100
            assert r['batch_manifest_sha256'] == audit.sha(manifest_path)
            assert r['checkpoint_sha256'] == audit.sha(path/'best.pt')
            best = (min if policy == 'ce' else max)(history, key=lambda x:x['validation_unweighted_ce' if policy == 'ce' else 'validation_macro_f1'])
            assert r['selected_epoch'] == best['epoch']
            audit.close(r['selected_validation_ce'], best['validation_unweighted_ce'])
            audit.close(r['selected_validation_macro_f1'], best['validation_macro_f1'])
            for split in ['validation', 'test']:
                with np.load(path/f'{split}_scores.npz', allow_pickle=False) as z:
                    y, p, subjects = z['y'], z['p'], z['subject']
                assert p.shape == (cell['expected'][split], 4)
                assert np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(1), 1, atol=1e-5)
                pred = p.argmax(1)
                cm = np.zeros((4,4), dtype=int)
                np.add.at(cm, (y,pred), 1)
                audit.confusion_check(r['metrics'][split], cm)
                confidence=p.max(1)
                correct=(pred==y).astype(float)
                ece=0.0
                bins=[]
                for i in range(10):
                    mask=(confidence>=i/10)&(confidence<=(i+1)/10 if i==9 else confidence<(i+1)/10)
                    if mask.any():
                        accuracy=float(correct[mask].mean())
                        mean_confidence=float(confidence[mask].mean())
                        ece+=float(mask.mean())*abs(accuracy-mean_confidence)
                        bins.append({'bin':i,'count':int(mask.sum()),'accuracy':accuracy,'confidence':mean_confidence})
                audit.close(ece,r['metrics'][split]['ece_10_equal_width'])
                audit.close(float(np.mean(np.sum((p-np.eye(4)[y])**2,axis=1))),r['metrics'][split]['brier_multiclass'])
                assert bins==r['metrics'][split]['calibration_bins']
                true_probability = p[np.arange(len(y)), y].astype(np.float64)
                assert (true_probability > 0).all()
                assert abs(float(-np.log(true_probability).mean())-r['metrics'][split]['cross_entropy']) < 1e-5
                assert set(subjects.tolist()) == set(r['metrics'][split]['per_subject'])
                for subject in set(subjects.tolist()):
                    mask = subjects == subject
                    cm = np.zeros((4,4), dtype=int)
                    np.add.at(cm, (y[mask],pred[mask]), 1)
                    audit.confusion_check(r['metrics'][split]['per_subject'][subject], cm)
            incart = r['metrics']['incart']
            assert incart['count'] == 175777
            audit.confusion_check(incart, incart['confusion_matrix_rows_actual_columns_predicted'])
            patient_sum=np.zeros((4,4),dtype=int)
            for patient_result in incart['per_patient'].values():
                patient_cm=np.asarray(patient_result['confusion_matrix_rows_actual_columns_predicted'])
                audit.confusion_check(patient_result,patient_cm)
                patient_sum+=patient_cm
            assert patient_sum.tolist()==incart['confusion_matrix_rows_actual_columns_predicted']
            row = {'id':cell['id'], 'model':cell['model'], 'seed':cell['seed'], 'policy':policy,
                   'epoch':r['selected_epoch'], 'matches_original_training_history':histories_identical}
            for source, split in [('mitdb','test'), ('incart','incart')]:
                metric = r['metrics'][split]
                row[source+'_macro_f1'] = metric['macro_f1_present_classes']
                row[source+'_ece'] = metric['ece_10_equal_width']
                row[source+'_brier'] = metric['brier_multiclass']
                for c in 'NSVF':
                    for name in ['precision','recall','f1']:
                        row[f'{source}_{c}_{name}'] = metric['per_class'][c][name]
            rows.append(row)
            cell_rows[policy] = row
        pairs.append({'id':cell['id'], 'model':cell['model'], 'seed':cell['seed'],
                      **{name:cell_rows['macro'][name]-cell_rows['ce'][name]
                         for name in cell_rows['ce'] if name.startswith(('mitdb_', 'incart_'))}})
    groups = defaultdict(list)
    for row in rows:groups[row['model']+'_'+row['policy']].append(row)
    paired = defaultdict(list)
    for row in pairs:paired[row['model']].append(row)
    keys = ['mitdb_macro_f1','incart_macro_f1','mitdb_ece','mitdb_brier','incart_ece','incart_brier','incart_S_precision','incart_S_recall','incart_F_precision','incart_F_recall']
    result = {'status':'passed', 'cells':rows, 'paired_macro_minus_ce':pairs,
              'groups':{k:audit.distribution(v, keys) for k,v in groups.items()},
              'paired_groups':{k:audit.distribution(v, keys) for k,v in paired.items()},
              'limits':'MIT aggregate and per-subject metrics recomputed from saved probabilities. INCART checked from saved confusion matrices; no new inference. Both development datasets, three seeds, only 15 validation F beats.'}
    (BASE/'ecg_selection_audit_2026-09-30.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'paired_groups':result['paired_groups']},indent=2))

if __name__ == '__main__':run()
