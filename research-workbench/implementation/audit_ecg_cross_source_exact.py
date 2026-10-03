"""Independently check the completed exact-input screen's manifest and coverage."""
import argparse,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(stage):
    r=json.loads((stage/'result.json').read_text());m=json.loads((stage/'manifest.json').read_text())
    assert r['manifest_sha256']==sha(stage/'manifest.json')
    assert r['source_sha256']==m['source_sha256']==sha(stage/'ecg_cross_source_exact.py')
    for result,expected in [('windows_per_source','expected_windows'),('records_per_source','expected_records'),('classes_per_source','expected_classes')]:assert r[result]==m[expected]
    assert len(r['files'])==sum(m['expected_records'].values())
    assert len({(x['source'],x['record']) for x in r['files']})==len(r['files'])
    for spec in m['sources']:
        files={x['record']:x for x in r['files'] if x['source']==spec['name']}
        assert {k:v['sha256'] for k,v in files.items()}==spec['array_sha256']
        assert sum(x['windows'] for x in files.values())==m['expected_windows'][spec['name']]
    groups=r['cross_source_exact_groups'];assert len(groups)==r['cross_source_exact_group_count']
    assert len({x['window_sha256'] for x in groups})==len(groups)
    for g in groups:
        assert len(g['sources'])>1 and set(g['sources'])<=set(m['expected_windows'])
        assert g['matching_entries']>=len(g['examples'])>=2
        assert len(g['window_sha256'])==64
    assert r['status']=='complete' and r['no_training'] and r['no_filtering']
    return {'status':'audited_complete','raw_sha256':sha(stage/'result.json'),'source_sha256':r['source_sha256'],'manifest_sha256':r['manifest_sha256'],'windows_per_source':r['windows_per_source'],'records_per_source':r['records_per_source'],'classes_per_source':r['classes_per_source'],'cross_source_exact_group_count':len(groups),'constant_windows_skipped':r['constant_windows_skipped'],'limits':r['limits']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',type=Path);a=p.parse_args();print(json.dumps(audit(a.stage),indent=2))
