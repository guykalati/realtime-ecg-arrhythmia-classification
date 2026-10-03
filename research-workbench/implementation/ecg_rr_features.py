"""Past-only, annotation-assisted timing aligned to unchanged window indices."""
import csv,hashlib,json,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import wfdb
BEATS=set('NLRaVFJASEj/QBenfr')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def features(samples,targets,fs):
    samples=np.asarray(samples,dtype=np.int64);targets=np.asarray(targets,dtype=np.int64)
    assert np.all(np.diff(samples)>0) and fs>0
    positions=np.searchsorted(samples,targets);assert np.all(positions<len(samples)) and np.array_equal(samples[positions],targets)
    intervals=np.diff(samples)/fs;out=np.zeros((len(targets),3),dtype=np.float32);stats=Counter()
    for i,j in enumerate(positions):
        if j==0:out[i,2]=1;stats['no_previous_beat']+=1;continue
        pre=intervals[j-1];past=intervals[max(0,j-11):j-1]
        out[i,0]=np.log(np.clip(pre,.05,5))
        if not len(past):out[i,2]=1;stats['no_baseline_history']+=1;continue
        baseline=float(np.median(past));assert baseline>0
        ratio=pre/baseline;out[i,1]=np.log(np.clip(ratio,.05,20))
        stats['complete_history' if len(past)==10 else 'partial_history']+=1
        stats['clipped_pre_rr']+=int(pre<.05 or pre>5);stats['clipped_ratio']+=int(ratio<.05 or ratio>20)
    assert np.isfinite(out).all();return out,dict(stats)
def run():
    began=time.monotonic();m=json.loads(Path('manifest.json').read_text());assert sha(Path(__file__))==m['source_sha256'];assert not Path('features').exists();Path('features').mkdir();results=[]
    for spec in m['sources']:
        manifest=Path(spec['window_manifest']);assert sha(manifest)==spec['window_manifest_sha256'];groups=defaultdict(list)
        for row in csv.DictReader(manifest.open()):groups[row[spec['record_column']]].append(row)
        assert set(groups)==set(spec['annotation_sha256']);total=0
        for record,rows in sorted(groups.items()):
            assert time.monotonic()-began<180,'three-minute local CPU cap'
            raw=Path(spec['annotation_root']);assert sha(raw/(record+'.atr'))==spec['annotation_sha256'][record]
            ann=wfdb.rdann(str(raw/record),'atr');samples=[s for s,t in zip(ann.sample,ann.symbol) if t in BEATS]
            assert [int(r['window_index']) for r in rows]==list(range(len(rows)))
            targets=[int(r[spec['sample_column']]) for r in rows];array,stats=features(samples,targets,spec['fs']);file=Path('features')/(spec['name']+'_'+record+'.npy');np.save(file,array);total+=len(rows)
            results.append({'source':spec['name'],'record':record,'windows':len(rows),'sha256':sha(file),'bytes':file.stat().st_size,'stats':stats,'classes':dict(Counter(r[spec['class_column']] for r in rows)),'annotation_symbols':dict(Counter(ann.symbol))})
        assert total==spec['expected_windows']
    assert sum(r['bytes'] for r in results)<4_000_000
    result={'status':'complete','files':results,'manifest_sha256':sha(Path('manifest.json')),'source_sha256':sha(Path(__file__)),'wfdb_version':wfdb.__version__,'elapsed_seconds':time.monotonic()-began,'feature_order':['log_pre_rr_seconds_clipped_0.05_5','log_pre_rr_over_median_previous_up_to10_intervals_clipped_0.05_20','missing_history'],'annotation_assisted':True,'no_model_scoring':True,'limits':'Full documented beat-symbol stream; rhythm, artifacts, blocked P-waves and flutter markers are not discrete beats. Median excludes current interval. Partial1-9 interval history retained and reported; cold start neutral ratio/missing flag. Clipping is fixed, not fitted. Centered waveforms still use about0.5sec future signal; no instantaneous-monitor claim.'}
    Path('result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))
def selfcheck():
    a,s=features([0,100,200,300,350],[200,300,350],100)
    np.testing.assert_allclose(a[:,1],[0,0,np.log(.5)],atol=1e-7)
    b,_=features([0,100,200,300,350,9000],[200,300,350],100);np.testing.assert_array_equal(a,b)
    c,s=features([0,100,200],[0,100,200],100);assert list(c[:,2])==[1,1,0]
if __name__=='__main__':
    import sys
    if '--selfcheck' in sys.argv:selfcheck();print('past-only and cold-start selfcheck passed')
    else:run()
