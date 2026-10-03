"""Audit array hashes, spread and exact model-input duplicates; never filter or score."""
import csv,hashlib,json,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np

ROOT=Path('/home/guykalat/codex_edb_resample_20261001')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    began=time.monotonic();m=json.loads(Path('manifest.json').read_text())
    assert sha(Path(__file__))==m['source_sha256']
    assert sha(ROOT/'summary.json')==m['summary_sha256']
    s=json.loads((ROOT/'summary.json').read_text());assert sha(ROOT/'window_manifest.csv')==s['manifest_sha256']
    rows=defaultdict(list)
    with (ROOT/'window_manifest.csv').open() as handle:
        for row in csv.DictReader(handle):rows[row['record']].append(row)
    signatures={};groups={};stds=defaultdict(list);zeros=Counter();counts=Counter();files=[]
    for item in s['files']:
        name=item['record'];p=ROOT/'windows_360'/(name+'.npy');assert sha(p)==item['sha256']
        x=np.load(p,mmap_mode='r');records=rows.pop(name);assert x.shape==(len(records),360) and np.isfinite(x).all()
        spread=x.std(axis=1,dtype=np.float64)
        local=Counter()
        for i,row in enumerate(records):
            assert int(row['window_index'])==i and row['lead']=='V5'
            klass=row['class'];counts[klass]+=1;local[klass]+=1;stds[klass].append(float(spread[i]))
            if spread[i]==0:zeros[klass]+=1
            digest=hashlib.sha256(x[i].tobytes()).digest()
            entry={'record':name,'group':row['documented_group'],'index':i,'class':klass}
            if digest in signatures:
                first=signatures[digest]
                # Retain counts and limited examples, keeping large flat-signal groups bounded.
                g=groups.setdefault(digest,{'count':1,'classes':Counter({first['class']:1}),
                                            'groups':{first['group']},'examples':[first]})
                g['count']+=1;g['classes'][klass]+=1;g['groups'].add(entry['group'])
                if len(g['examples'])<10:g['examples'].append(entry)
            else:signatures[digest]=entry
        assert dict(local)==item['classes'];files.append({'record':name,'sha256':item['sha256'],'windows':len(records)})
    assert not rows and dict(counts)==m['expected_classes']
    duplicates=[{'window_sha256':k.hex(),'count':v['count'],'classes':dict(v['classes']),
                 'documented_groups':sorted(v['groups']),'examples':v['examples']} for k,v in groups.items()]
    summary={'status':'passed','records':51,'classes':dict(counts),'constant_window_counts':dict(zeros),
             'std_mv_quantiles':{c:dict(zip(['min','p05','median','p95','max'],np.quantile(v,[0,.05,.5,.95,1]).tolist())) for c,v in stds.items()},
             'exact_duplicate_window_groups':len(duplicates),'duplicate_excess_windows':sum(x['count']-1 for x in duplicates),
             'cross_documented_group_duplicate_groups':sum(len(x['documented_groups'])>1 for x in duplicates),
             'files':files,'duplicate_groups':duplicates,'elapsed_seconds':time.monotonic()-began,
             'no_filtering':True,'limits':'Exact resampled float32 V5 model-input duplicates and amplitude spread only. One beat cannot establish same recorded episode or person. Negative exact hashes cannot exclude approximate/cross-lead/re-encoded recordings. No train normalization, filtering, model scores or SVDB access.'}
    encoded=json.dumps(summary,indent=2)+'\n';assert len(encoded.encode())<m['output_byte_cap']
    Path('result.json').write_text(encoded);print(json.dumps({k:v for k,v in summary.items() if k not in ['files','duplicate_groups']}))

if __name__=='__main__':run()
