"""Inventory finite one-second V5 windows and quality flags, without model input files."""
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
import numpy as np
import wfdb

SOURCE = Path('/home/guykalat/codex_edb_v5_acquire_20261001')
LINKS = Path('/home/guykalat/codex_edb_decode_20261001/links')
LABELS = {'N': 'N', 'a': 'S', 'J': 'S', 'S': 'S', 'V': 'V', 'F': 'F'}


def flags_for_windows(changes, codes, channel, length, starts, stops):
    assert len(changes) == len(codes) and np.all(np.diff(changes) >= 0)
    assert all(0 <= int(c) <= 0x33 and not int(c) & ~0x33 for c in codes)
    index = np.searchsorted(changes, np.arange(length), side='right') - 1
    unknown = index < 0
    active = np.zeros(length, dtype=np.int16)
    if len(codes):
        active[~unknown] = codes[index[~unknown]]
    result = {}
    for name, values in [('unknown', unknown), ('noisy', (active & (1 << channel)) != 0),
                         ('unreadable', (active & (0x10 << channel)) != 0)]:
        prefix = np.concatenate(([0], np.cumsum(values, dtype=np.int64)))
        result[name] = (prefix[stops] - prefix[starts]) > 0
    return result


def self_check():
    flags = flags_for_windows(np.array([3, 5]), np.array([1, 0x10]), 0, 8,
                              np.array([0, 3, 5, 6]), np.array([3, 5, 6, 8]))
    assert flags['unknown'].tolist() == [True, False, False, False]
    assert flags['noisy'].tolist() == [False, True, False, False]
    assert flags['unreadable'].tolist() == [False, False, True, True]
    other = flags_for_windows(np.array([0]), np.array([1]), 1, 8,
                              np.array([0]), np.array([8]))
    assert not any(v.any() for v in other.values())


def run():
    self_check()
    began = time.monotonic()
    manifest = json.loads(Path('manifest.json').read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == manifest['source_sha256']
    assert hashlib.sha256((SOURCE / 'plan.json').read_bytes()).hexdigest() == manifest['signal_plan_sha256']
    plan = json.loads((SOURCE / 'plan.json').read_text())
    rows = []; total = Counter(); excluded = Counter()
    with Path('windows.csv').open('w') as handle:
        writer = csv.writer(handle)
        writer.writerow(['record', 'documented_group', 'lead', 'sample', 'symbol', 'class',
                         'unknown_in_window', 'noisy_in_window', 'unreadable_in_window'])
        for item in plan['signals']:
            name = item['key'].rsplit('/', 1)[-1].removesuffix('.dat')
            for ext in ('hea', 'atr'):
                path = SOURCE / (name + '.' + ext)
                assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['metadata_sha256'][path.name]
            raw = SOURCE / 'raw' / (name + '.dat')
            assert hashlib.sha256(raw.read_bytes()).hexdigest() == item['release_sha256']
            signal = wfdb.rdrecord(str(LINKS / name), channels=[item['v5_index']])
            assert signal.fs == 250 and signal.sig_name == ['V5'] and signal.units == ['mV']
            values = signal.p_signal[:, 0]
            ann = wfdb.rdann(str(LINKS / name), 'atr')
            symbols = np.array(ann.symbol); selected = np.isin(symbols, list(LABELS))
            centers = ann.sample[selected]; beat_symbols = symbols[selected]
            assert len(np.unique(centers)) == len(centers)
            starts = centers - 125; stops = centers + 125
            bounds = (starts >= 0) & (stops <= len(values))
            local_excluded = Counter('edge:' + LABELS[s] for s in beat_symbols[~bounds])
            starts, stops, centers, beat_symbols = [a[bounds] for a in (starts, stops, centers, beat_symbols)]
            invalid_prefix = np.concatenate(([0], np.cumsum(~np.isfinite(values), dtype=np.int64)))
            finite = (invalid_prefix[stops] - invalid_prefix[starts]) == 0
            local_excluded.update('nonfinite:' + LABELS[s] for s in beat_symbols[~finite])
            starts, stops, centers, beat_symbols = [a[finite] for a in (starts, stops, centers, beat_symbols)]
            noise = symbols == '~'
            flags = flags_for_windows(ann.sample[noise], ann.subtype[noise], item['v5_index'], len(values), starts, stops)
            local = Counter(); class_flags = {c: Counter() for c in 'NSVF'}
            for i, (sample, symbol) in enumerate(zip(centers, beat_symbols)):
                c = LABELS[symbol]; local[c] += 1
                f = [bool(flags[n][i]) for n in ('unknown', 'noisy', 'unreadable')]
                for n, flag in zip(('unknown', 'noisy', 'unreadable'), f):
                    if flag: class_flags[c][n] += 1
                if not any(f): class_flags[c]['entire_window_source_clean'] += 1
                writer.writerow([name, item['patient_group'], 'V5', int(sample), symbol, c, *map(int, f)])
            total.update(local); excluded.update(local_excluded)
            rows.append({'record': name, 'documented_group': item['patient_group'], 'retained_classes': dict(local),
                         'excluded': dict(local_excluded), 'window_quality_flags': {c: dict(v) for c, v in class_flags.items()}})
            assert handle.tell() < manifest['output_byte_cap']
    assert len(rows) == 51
    output = {'status': 'complete', 'records': 51, 'window_rule': '[center-125,center+125) native250Hz V5 mV',
              'retained_classes': dict(total), 'excluded': dict(excluded), 'rows': rows,
              'manifest_sha256': hashlib.sha256(Path('windows.csv').read_bytes()).hexdigest(),
              'manifest_bytes': Path('windows.csv').stat().st_size, 'elapsed_seconds': time.monotonic() - began,
              'limits': 'No resampling, saved waveforms, quality-policy exclusions, duplicate screening, model training or scores. Source noise flags can coexist; unknown is not clean. Quality bit interpretation retains previously documented source-table discrepancy.'}
    Path('result.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({k:v for k,v in output.items() if k != 'rows'}))


if __name__ == '__main__':
    run()
