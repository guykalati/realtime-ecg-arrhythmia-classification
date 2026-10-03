"""EDB release checksum and subject-level beat inventory; no signals/inference."""
import hashlib
import json
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree
from incart_metadata_inventory import BUCKET, NS, download_one

BASE=Path(__file__).resolve().parent
PREFIX='edb/1.0.0/'
SYMBOL_CLASS={'N':'N','a':'S','J':'S','S':'S','V':'V','F':'F'}
GROUPS=[range(118,123),range(123,127),[129,133],[136,139],[147,148],[154,155],[162,163]]

def patient(record):
    number=int(record[1:])
    for group in GROUPS:
        if number in group:return f'edb_e{min(group):04d}'
    return 'edb_'+record

def run():
    import wfdb
    target=BASE/'data/edb_metadata_20260930'
    target.mkdir(parents=True,exist_ok=True)
    with urlopen(BUCKET+'/?list-type=2&prefix='+PREFIX+'&max-keys=1000',timeout=30) as response:xml=response.read()
    listing=ElementTree.fromstring(xml)
    assert listing.findtext('s:IsTruncated',namespaces=NS)=='false'
    objects={}
    for entry in listing.findall('s:Contents',NS):
        key=entry.findtext('s:Key',namespaces=NS)
        if key and key.startswith(PREFIX):
            objects[key.removeprefix(PREFIX)]={'key':key,'size':int(entry.findtext('s:Size',namespaces=NS)),
                                             'etag':entry.findtext('s:ETag',namespaces=NS).strip('"')}
    # First pin source record list and release SHA256 manifest, also checking S3 size/MD5.
    metadata=[download_one(objects[name],target) for name in ['RECORDS','SHA256SUMS.txt']]
    records=(target/'RECORDS').read_text().splitlines()
    assert len(records)==90 and len(set(records))==90 and all(re.fullmatch(r'e\d{4}',r) for r in records)
    items=[objects[record+'.'+suffix] for record in records for suffix in ['hea','atr']]
    assert len(items)==180 and sum(i['size'] for i in items)+sum(i['size'] for i in metadata)<=5_000_000
    with ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(lambda i:download_one(i,target),items))
    release={}
    for line in (target/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split(maxsplit=1)
        release[name.lstrip('*').removeprefix('./')]=digest
    for f in files:
        name=f['key'].removeprefix(PREFIX)
        assert f['sha256']==release[name],name
    symbols,classes,leads=Counter(),Counter(),Counter()
    people=defaultdict(lambda:{'records':[],'classes':Counter()})
    rows=[]
    for name in records:
        header=wfdb.rdheader(str(target/name));annotation=wfdb.rdann(str(target/name),'atr')
        assert header.fs==250 and header.n_sig==2 and header.sig_len==1800000
        assert len(annotation.sample)==len(annotation.symbol)
        assert (annotation.sample>=0).all() and (annotation.sample<header.sig_len).all()
        counts=Counter(annotation.symbol);mapped=Counter(SYMBOL_CLASS.get(s,'unmapped') for s in annotation.symbol)
        symbols.update(counts);classes.update(mapped);leads.update(header.sig_name)
        pid=patient(name);people[pid]['records'].append(name);people[pid]['classes'].update(mapped)
        rows.append({'record_id':name,'patient_group':pid,'fs':header.fs,'lead_names':header.sig_name,
                     'lead_ii_indices':[i for i,s in enumerate(header.sig_name) if s.upper() in ['II','MLII']],
                     'annotation_events':len(annotation.symbol),'symbols':dict(counts),'classes':dict(mapped)})
    assert len(people)==79 and sum(symbols.values())==sum(classes.values())
    concentration={}
    for c in 'SF':
        ranked=sorted(((pid,p['classes'][c]) for pid,p in people.items() if p['classes'][c]),key=lambda x:-x[1])
        concentration[c]={'subjects_with_class':len(ranked),'total':classes[c],'by_subject':ranked,
                          'largest_subject_fraction':ranked[0][1]/classes[c] if ranked else None}
    result={'status':'audited','source_url':'https://physionet.org/content/edb/1.0.0/',
            'license':'ODC Attribution v1.0','source_release':'1.0.0','retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
            'files':metadata+files,'bytes':sum(f['size'] for f in metadata+files),
            'records':rows,'subjects':{pid:{'records':p['records'],'classes':dict(p['classes'])} for pid,p in sorted(people.items())},
            'symbol_mapping':SYMBOL_CLASS,'symbols':dict(symbols),'classes':dict(classes),'lead_counts':dict(leads),
            'records_with_II_or_MLII':sum(bool(r['lead_ii_indices']) for r in rows),'rare_class_concentration':concentration,
            'wfdb_version':wfdb.__version__,'source_listing_sha256':hashlib.sha256(xml).hexdigest(),
            'limits':'Metadata only, all source annotations before waveform/window/lead exclusions. Counts are beats/events, not patients. EDB role unassigned; no signals, scores, cross-source identity guarantee or SVDB access.'}
    (target/'source_listing.xml').write_bytes(xml)
    (BASE/'edb_metadata_inventory_2026-09-30.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','bytes','classes','records_with_II_or_MLII','rare_class_concentration']},indent=2),flush=True)

if __name__=='__main__':run()
