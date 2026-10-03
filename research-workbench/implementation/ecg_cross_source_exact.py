"""Exact prepared-input duplication screen; never infer person identity."""
import csv,hashlib,json,time
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def compare_entries(entries):
    # Exact float32 windows only; near-episode matching requires a separate method.
    first={};cross={};counts=Counter();constant=Counter()
    for meta,window in entries:
        assert window.shape==(360,) and window.dtype==np.float32 and np.isfinite(window).all()
        source=meta['source'];counts[source]+=1
        if np.all(window==window[0]):constant[source]+=1;continue
        digest=hashlib.sha256(window.tobytes()).hexdigest()
        if digest not in first:first[digest]=[meta,1];continue
        prev,previous_count=first[digest];first[digest][1]+=1
        if prev['source']==source and digest not in cross:continue
        group=cross.setdefault(digest,{'sources':{prev['source']},'examples':[prev],'matching_entries':previous_count})
        group['sources'].add(source);group['matching_entries']+=1
        if len(group['examples'])<10:group['examples'].append(meta)
    return {'windows_per_source':dict(counts),'constant_windows_skipped':dict(constant),
            'cross_source_exact_groups':[{'window_sha256':k,'sources':sorted(v['sources']),'matching_entries':v['matching_entries'],'examples':v['examples']} for k,v in cross.items() if len(v['sources'])>1]}

def run():
    started=time.monotonic();m=json.loads(Path('manifest.json').read_text());assert sha(Path(__file__))==m['source_sha256']
    assert not Path('result.json').exists();files=[];record_counts=Counter();class_counts=defaultdict(Counter)
    def entries():
        for spec in m['sources']:
            root=Path(spec['root']);csv_path=root/'window_manifest.csv';assert sha(csv_path)==spec['csv_sha256']
            grouped=defaultdict(list)
            with csv_path.open() as handle:
                for row in csv.DictReader(handle):grouped[row[spec['record_column']]].append(row)
            assert set(grouped)==set(spec['array_sha256'])
            for record,expected in sorted(spec['array_sha256'].items()):
                path=root/'windows_360'/(record+'.npy');assert sha(path)==expected
                x=np.load(path,mmap_mode='r');rows=grouped.pop(record)
                assert x.shape==(len(rows),360) and x.dtype==np.float32 and np.isfinite(x).all()
                record_counts[spec['name']]+=1;local=Counter()
                for i,row in enumerate(rows):
                    assert int(row['window_index'])==i
                    klass=row[spec['class_column']];local[klass]+=1
                    meta={'source':spec['name'],'record':record,'group':row[spec['group_column']],
                          'lead':row[spec['lead_column']],'class':klass,'index':i}
                    yield meta,x[i]
                class_counts[spec['name']].update(local)
                files.append({'source':spec['name'],'record':record,'sha256':expected,'windows':len(rows)})
            assert not grouped
    d=compare_entries(entries())
    assert d['windows_per_source']==m['expected_windows']
    assert dict(record_counts)==m['expected_records']
    for key,expected in m['expected_classes'].items():assert dict(class_counts[key])==expected
    result={'status':'complete',**d,'cross_source_exact_group_count':len(d['cross_source_exact_groups']),
            'records_per_source':dict(record_counts),'classes_per_source':{k:dict(v) for k,v in class_counts.items()},
            'files':files,'source_sha256':sha(Path(__file__)),'manifest_sha256':sha(Path('manifest.json')),
            'elapsed_seconds':time.monotonic()-started,'no_filtering':True,'no_training':True,
            'limits':'Exact nonconstant float32 one-second prepared windows, not aligned long-recording/near-duplicate screening or cross-release patient identity. Different leads/resampling/offsets can evade hashes. Zero matches does not establish independent people. MIT includes all48 prepared records, including paced/Q/V5 cases outside primary training scope. SVDB untouched.'}
    encoded=json.dumps(result,indent=2)+'\n';assert len(encoded.encode())<1_000_000
    Path('result.json').write_text(encoded);print(json.dumps({k:v for k,v in result.items() if k not in ('files','cross_source_exact_groups')}))

def selfcheck():
    x=np.arange(360,dtype=np.float32);y=x+1
    def meta(source):return {'source':source,'record':'r','group':'g','lead':'II','class':'N','index':0}
    d=compare_entries([(meta('a'),x),(meta('a'),x.copy()),(meta('b'),x.copy()),(meta('b'),y),(meta('a'),np.zeros(360,dtype=np.float32))])
    assert len(d['cross_source_exact_groups'])==1 and d['cross_source_exact_groups'][0]['sources']==['a','b']
    assert d['cross_source_exact_groups'][0]['matching_entries']==3
    assert d['constant_windows_skipped']=={'a':1} and d['windows_per_source']=={'a':3,'b':2}
if __name__=='__main__':
    import sys
    if '--selfcheck' in sys.argv:selfcheck();print('selfcheck passed')
    else:run()
