"""Independent patient-support, confusion arithmetic and validation-only selection audit."""
import csv,json,math
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from audit_ecg_rr_compare import metric,sha

def audit(stage):
 m=json.loads((stage/'manifest.json').read_text());r=json.loads((stage/'output/result.json').read_text());assert r['status']=='complete' and r['manifest_sha256']==sha(stage/'manifest.json');assert all(sha(stage/n)==h for n,h in m['source_sha256'].items());assert len(r['rows'])==18;expected={(s['id'],seed,w) for s in m['splits'] for seed in m['seeds'] for w in m['adversarial_weights']};seen=set();supports={};tests={}
 for split in m['splits']:
  assert sha(stage/split['context'])==split['context_sha256'] and sha(stage/split['split'])==split['split_sha256'];partgroups=defaultdict(set);train=defaultdict(lambda:Counter());test=Counter()
  records=list(csv.DictReader((stage/split['split']).open()));patients={x['record_id']:x['patient_id'] for x in records};assert patients['201']==patients['202'];recordparts={x['record_id']:x['split'] for x in records};assert recordparts['201']==recordparts['202']
  for row in csv.DictReader((stage/split['context']).open()):
   assert row['subject_group']==patients[row['record_id']] and row['split']==recordparts[row['record_id']];partgroups[row['split']].add(row['subject_group'])
   if row['split']=='train':train[row['subject_group']][row['class_4']]+=1
   elif row['split']=='test':test[row['class_4']]+=1
  assert not partgroups['train']&partgroups['validation'] and not partgroups['train']&partgroups['test'] and not partgroups['validation']&partgroups['test'];supports[split['id']]={s:[train[s][k] for k in 'NSVF'] for s in sorted(train)};tests[split['id']]=(test,partgroups['test'])
 for row in r['rows']:
  key=(row['split'],row['seed'],row['adversarial_weight']);assert key in expected and key not in seen;seen.add(key);assert sha(stage/'output'/('_'.join(map(str,key))+'.pt'))==row['checkpoint_sha256'];support=supports[row['split']];assert row['training_subject_class_support_N_S_V_F']==support and row['training_subject_mapping']=={s:i for i,s in enumerate(support)} and row['training_subject_count']==len(support)
  total=sum(sum(v) for v in support.values());assert math.isclose(row['largest_training_subject_fraction'],max(sum(v) for v in support.values())/total,abs_tol=1e-12);assert row['training_parameter_count']-row['inference_parameter_count']==65*len(support)
  hist=row['validation_history'];assert [x['epoch'] for x in hist]==list(range(1,13));best=min(hist,key=lambda x:x['validation_ce']);assert best['epoch']==row['selected_epoch'] and abs(best['validation_ce']-row['validation_ce'])<1e-10 and abs(row['reloaded_validation_ce']-row['validation_ce'])<1e-6
  for x in hist:assert x['subject_loss']>=0 and x['mean_batch_weighted_classification_loss']>=0 and 0<=x['training_subject_accuracy']<=1
  for source in ['mit_development','incart_development']:
   d=row[source];c=metric(d);group=np.zeros((4,4),dtype=int)
   for g in d['per_group'].values():group+=metric(g)
   np.testing.assert_array_equal(group,c);assert 0<=d['brier_multiclass']<=2 and 0<=d['ece_10_equal_width']<=1 and d['cross_entropy']>=0
   support_counts={k:v['support'] for k,v in d['per_class'].items()}
   if source=='mit_development':assert support_counts==dict(tests[row['split']][0]) and set(d['per_group'])==tests[row['split']][1]
   else:assert support_counts=={'N':153594,'S':1958,'V':20006,'F':219} and len(d['per_group'])==32
 assert seen==expected
 validation={str(w):float(np.mean([x['validation_ce'] for x in r['rows'] if x['adversarial_weight']==w])) for w in m['adversarial_weights']};chosen=min(m['adversarial_weights'],key=lambda w:(validation[str(w)],w));summary={}
 for source in ['mit_development','incart_development']:
  arms={}
  for w in m['adversarial_weights']:
   cells=[x for x in r['rows'] if x['adversarial_weight']==w];values=[]
   for x in cells:
    d=x[source];c=np.array(d['confusion_matrix_rows_actual_columns_predicted']);v={'macro_f1':d['macro_f1_present_classes'],'brier':d['brier_multiclass'],'nll':d['cross_entropy']}
    for cl,i in [('S',1),('F',3)]:
     for k in ['precision','recall','f1']:v[cl+'_'+k]=d['per_class'][cl][k]
     v[cl+'_false_positives']=int(c[:,i].sum()-c[i,i])
    values.append(v)
   arms[str(w)]={'mean':{k:float(np.mean([v[k] for v in values])) for k in values[0]},'macro_f1_range':[min(v['macro_f1'] for v in values),max(v['macro_f1'] for v in values)]}
  a=arms[str(chosen)]['mean'];b=arms['0']['mean'];guards={'positive_macro_f1':a['macro_f1']>b['macro_f1'],'positive_S_f1':a['S_f1']>b['S_f1'],'F_recall_not_lower':a['F_recall']>=b['F_recall'],'F_precision_not_lower':a['F_precision']>=b['F_precision'],'brier_not_higher':a['brier']<=b['brier'],'S_false_positives_within_110percent':a['S_false_positives']<=1.1*b['S_false_positives'],'F_false_positives_within_110percent':a['F_false_positives']<=1.1*b['F_false_positives']};paired=[]
  for split in m['splits']:
   for seed in m['seeds']:
    cells={x['adversarial_weight']:x[source] for x in r['rows'] if x['split']==split['id'] and x['seed']==seed};paired.append({'split':split['id'],'seed':seed,'delta_macro_f1':cells[chosen]['macro_f1_present_classes']-cells[0]['macro_f1_present_classes']})
  summary[source]={'arms':arms,'validation_selected_weight_guards':guards,'guards_passed':all(guards.values()),'paired_selected_minus_control':paired}
 passed=chosen!=0 and all(s['guards_passed'] for s in summary.values())
 return {'status':'audited_complete','runs':18,'raw_sha256':sha(stage/'output/result.json'),'manifest_sha256':sha(stage/'manifest.json'),'validation_mean_ce_by_weight':validation,'validation_selected_weight':chosen,'summary':summary,'provisional_rule_passed':passed,'reference_decision':'provisional subject-adversarial candidate; fresh confirmation pending' if passed else 'retain existing combined CNN/timing reference','elapsed_seconds':r['elapsed_seconds'],'gpu_name':r['gpu_name'],'limits':r['limits'],'auditor_sha256':sha(Path(__file__))}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('output',type=Path);a=p.parse_args();result=audit(a.stage);assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
