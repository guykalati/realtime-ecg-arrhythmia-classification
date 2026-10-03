"""Check artifact hashes, support, and independently sampled past-only formulas."""
import csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import wfdb
BEATS={'N','L','R','a','V','F','J','A','S','E','j','/','Q','B','e','n','f','r'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(stage):
    m=json.loads((stage/'manifest.json').read_text());r=json.loads((stage/'result.json').read_text());assert r['status']=='complete'
    assert r['manifest_sha256']==sha(stage/'manifest.json') and r['source_sha256']==m['source_sha256']==sha(stage/'ecg_rr_features.py')
    files={(x['source'],x['record']):x for x in r['files']};assert len(files)==123;support=defaultdict(Counter);missing=defaultdict(Counter);checks=0
    for spec in m['sources']:
        p=Path(spec['window_manifest']);assert sha(p)==spec['window_manifest_sha256'];groups=defaultdict(list)
        for row in csv.DictReader(p.open()):groups[row[spec['record_column']]].append(row)
        for record,rows in groups.items():
            f=files[spec['name'],record];path=stage/'features'/(spec['name']+'_'+record+'.npy');assert sha(path)==f['sha256'];x=np.load(path);assert x.dtype==np.float32 and x.shape==(len(rows),3) and np.isfinite(x).all()
            raw=Path(spec['annotation_root']);assert sha(raw/(record+'.atr'))==spec['annotation_sha256'][record]
            ann=wfdb.rdann(str(raw/record),'atr');beats=[int(v) for v,t in zip(ann.sample,ann.symbol) if t in BEATS];positions={v:i for i,v in enumerate(beats)}
            for i,row in enumerate(rows):
                klass=row[spec['class_column']];support[spec['name']][klass]+=1;missing[spec['name']][klass]+=int(x[i,2]==1)
            for i in sorted({0,1,len(rows)//3,len(rows)//2,len(rows)-1}):
                j=positions[int(rows[i][spec['sample_column']])];expected=[0.,0.,1.]
                if j:
                    pre=(beats[j]-beats[j-1])/spec['fs'];expected[0]=math.log(min(5,max(.05,pre)))
                    past=[(beats[k]-beats[k-1])/spec['fs'] for k in range(max(1,j-10),j)]
                    if past:
                        ratio=pre/float(np.median(past));expected[1]=math.log(min(20,max(.05,ratio)));expected[2]=0.
                np.testing.assert_allclose(x[i],expected,atol=2e-7,rtol=1e-7);checks+=1
        assert sum(support[spec['name']].values())==spec['expected_windows']
    return {'status':'audited_complete','raw_sha256':sha(stage/'result.json'),'manifest_sha256':r['manifest_sha256'],'source_sha256':r['source_sha256'],'files':r['files'],'independent_formula_rows_checked':checks,'classes_per_source':{k:dict(v) for k,v in support.items()},'missing_history_per_class':{k:dict(v) for k,v in missing.items()},'no_model_scoring':True,'limits':r['limits']}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('out',type=Path);a=p.parse_args();d=audit(a.stage);assert not a.out.exists();a.out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:v for k,v in d.items() if k!='files'},indent=2))
