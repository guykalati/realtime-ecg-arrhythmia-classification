"""Audit frozen development ablation provenance and confusion arithmetic."""
import csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
CLASSES='NSVF'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metric(d):
    c=np.asarray(d['confusion_matrix_rows_actual_columns_predicted']);assert c.shape==(4,4) and np.all(c>=0) and np.all(c==c.astype(int));assert c.sum()==d['count'];f=[]
    for i,k in enumerate(CLASSES):
        r=d['per_class'][k];support=int(c[i].sum());assert support==r['support'];precision=c[i,i]/c[:,i].sum() if c[:,i].sum() else 0;recall=c[i,i]/support if support else None
        if support:
            value=2*precision*recall/(precision+recall) if precision+recall else 0
            for a,b in [(precision,r['precision']),(recall,r['recall']),(value,r['f1'])]:assert math.isclose(a,b,abs_tol=1e-10)
            f.append(value)
    assert math.isclose(float(np.mean(f)),d['macro_f1_present_classes'],abs_tol=1e-10);assert math.isclose(c.trace()/c.sum(),d['accuracy'],abs_tol=1e-10)
    return c
def audit(stage):
    m=json.loads((stage/'manifest.json').read_text());p=stage/'output/result.json';r=json.loads(p.read_text());assert r['status']=='complete' and r['manifest_sha256']==sha(stage/'manifest.json')
    assert all(sha(stage/n)==v for n,v in m['source_sha256'].items());assert len(r['rows'])==18
    expected={(s['id'],seed,mode) for s in m['splits'] for seed in m['seeds'] for mode in m['modes']};seen=set();groups={};summary={}
    for split in m['splits']:
        p=stage/split['context'];assert sha(p)==split['context_sha256'];assert sha(stage/split['split'])==split['split_sha256'];classes=Counter();subjects=set()
        for row in csv.DictReader(p.open()):
            if row['split']=='test':classes[row['class_4']]+=1;subjects.add(row['subject_group'])
        groups[split['id']]=(classes,subjects)
    for row in r['rows']:
        key=(row['split'],row['seed'],row['mode']);assert key in expected and key not in seen;seen.add(key)
        checkpoint=stage/'output'/('_'.join(map(str,key))+'.pt');assert sha(checkpoint)==row['checkpoint_sha256']
        history=row['validation_history'];assert len(history)==12 and [x['epoch'] for x in history]==list(range(1,13));assert abs(min(x['validation_ce'] for x in history)-row['validation_ce'])<1e-9;assert abs(row['reloaded_validation_ce']-row['validation_ce'])<1e-6
        for source in ['mit_development','incart_development']:
            d=row[source];c=metric(d);total=np.zeros((4,4),dtype=int)
            for g in d['per_group'].values():total+=metric(g)
            np.testing.assert_array_equal(total,c);assert 0<=d['brier_multiclass']<=2 and 0<=d['ece_10_equal_width']<=1 and d['cross_entropy']>=0
            support={k:v['support'] for k,v in d['per_class'].items()}
            if source=='mit_development':assert support==dict(groups[row['split']][0]) and set(d['per_group'])==groups[row['split']][1]
            else:assert support=={'N':153594,'S':1958,'V':20006,'F':219} and len(d['per_group'])==32
    assert seen==expected
    for source in ['mit_development','incart_development']:
        summary[source]={}
        for mode in m['modes']:
            rows=[x for x in r['rows'] if x['mode']==mode];values=[]
            for x in rows:
                d=x[source];c=np.asarray(d['confusion_matrix_rows_actual_columns_predicted']);values.append({'macro_f1':d['macro_f1_present_classes'],'S_f1':d['per_class']['S']['f1'],'S_precision':d['per_class']['S']['precision'],'S_recall':d['per_class']['S']['recall'],'F_f1':d['per_class']['F']['f1'],'F_recall':d['per_class']['F']['recall'],'F_precision':d['per_class']['F']['precision'],'F_false_positives':int(c[:,3].sum()-c[3,3]),'S_false_positives':int(c[:,1].sum()-c[1,1]),'brier':d['brier_multiclass'],'nll':d['cross_entropy']})
            summary[source][mode]={'mean':{k:float(np.mean([v[k] for v in values])) for k in values[0]},'macro_f1_range':[min(v['macro_f1'] for v in values),max(v['macro_f1'] for v in values)]}
        paired=[]
        for split in m['splits']:
            for seed in m['seeds']:
                pair={x['mode']:x[source] for x in r['rows'] if x['split']==split['id'] and x['seed']==seed};paired.append({'split':split['id'],'seed':seed,'delta_macro_f1':pair['combined']['macro_f1_present_classes']-pair['waveform']['macro_f1_present_classes']})
        summary[source]['paired_combined_minus_waveform']=paired
        a=summary[source]['combined']['mean'];b=summary[source]['waveform']['mean'];summary[source]['passes_frozen_source_rule']=a['macro_f1']>b['macro_f1'] and a['S_f1']>b['S_f1'] and a['F_recall']>=b['F_recall'] and a['brier']<=b['brier']
    passed=all(v['passes_frozen_source_rule'] for v in summary.values())
    return {'status':'audited_complete','raw_sha256':sha(stage/'output/result.json'),'manifest_sha256':r['manifest_sha256'],'runs':18,'gpu_name':r['gpu_name'],'elapsed_seconds':r['elapsed_seconds'],'summary':summary,'provisional_rule_passed':passed,'reference_decision':'provisional combined candidate; fresh confirmation still pending' if passed else 'retain waveform reference; mixed/negative development effects','limits':r['limits']}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('out',type=Path);a=p.parse_args();d=audit(a.stage);assert not a.out.exists();a.out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
