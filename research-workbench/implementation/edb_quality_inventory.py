"""Inventory source-annotated channel quality at beat times, without signals."""
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import wfdb
from edb_metadata_inventory import BASE,SYMBOL_CLASS

def quality_states(code):
    # WFDB bxb tests bits4/5 for unreadability; EDB defines each channel's low noisy bit.
    # Raw files use 0x13/0x22/0x23, unlike the literal 0x12/0x20/0x21 prose table.
    if code<0 or code & ~0x33:raise ValueError('unrecognized quality bit mask')
    return tuple('unreadable' if code&unreadable else 'noisy' if code&noisy else 'clean'
                 for unreadable,noisy in [(0x10,1),(0x20,2)])

def run():
    source=BASE/'edb_metadata_inventory_2026-09-30.json'
    inventory=json.loads(source.read_text())
    root=BASE/'data/edb_metadata_20260930'
    totals=defaultdict(Counter);v5=defaultdict(Counter);codes=Counter();rows=[]
    for record in inventory['records']:
        name=record['record_id'];annotation=wfdb.rdann(str(root/name),'atr')
        assert (np.diff(annotation.sample)>=0).all()
        symbols=np.asarray(annotation.symbol)
        noise=symbols=='~'
        samples=annotation.sample[noise]
        subtypes=annotation.subtype[noise]
        codes.update(int(v) for v in subtypes)
        for code in set(int(v) for v in subtypes):quality_states(code)
        beats=np.flatnonzero(np.isin(symbols,list(SYMBOL_CLASS)))
        index=np.searchsorted(samples,annotation.sample[beats],side='right')-1
        counters=defaultdict(Counter)
        for beat,event in zip(beats,index):
            klass=SYMBOL_CLASS[symbols[beat]]
            states=quality_states(int(subtypes[event])) if event>=0 else ('unknown','unknown')
            for lead,state in zip(record['lead_names'],states):
                totals[klass][state]+=1;counters[klass][state]+=1
                if lead=='V5':v5[klass][state]+=1
        assert sum(sum(v.values()) for v in counters.values())==2*sum(record['classes'].get(c,0) for c in 'NSVF')
        rows.append({'record_id':name,'patient_group':record['patient_group'],'quality_change_events':int(noise.sum()),
                     'class_channel_quality':{c:dict(v) for c,v in counters.items()}})
    assert sum(codes.values())==inventory['symbols']['~']
    result={'status':'audited','metadata_inventory_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'quality_code_counts':{hex(k):v for k,v in sorted(codes.items())},
            'decoder_sources':['https://physionet.org/physiotools/wfdb/app/bxb.c','https://physionet.org/physiobank/database/edb/annotations.shtml'],
            'literal_table_discrepancy':'Observed0x13,0x22,0x23 instead of the prose table0x12,0x20,0x21. Decode unreadable bits4/5 from WFDB bxb and channel/noisy-bit associations from EDB table; these derived states need a source-convention check before exclusion policy.',
            'all_channel_beat_quality':{c:dict(v) for c,v in totals.items()},
            'V5_beat_quality':{c:dict(v) for c,v in v5.items()},'records':rows,
            'interpretation':'Last source NOISE annotation at or before a beat is carried forward independently per channel. Before first annotation is unknown, never assumed clean. All-channel rows count two lead observations per mapped beat; V5 rows count one where available.',
            'limits':'Source annotation state, not waveform quality remeasurement. No window-duration expansion, sample exclusion, preprocessing, training or performance claim.'}
    (BASE/'edb_quality_inventory_2026-09-30.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','quality_code_counts','V5_beat_quality']},indent=2))

if __name__=='__main__':run()
