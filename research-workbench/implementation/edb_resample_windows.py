"""Emit bounded development-only V5 arrays from the frozen finite-window inventory."""
import csv
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import scipy
from scipy.signal import resample_poly
import wfdb

SOURCE = Path('/home/guykalat/codex_edb_v5_acquire_20261001')
LINKS = Path('/home/guykalat/codex_edb_decode_20261001/links')
INVENTORY = Path('/home/guykalat/codex_edb_windows_20261001/windows.csv')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    began = time.monotonic(); m = json.loads(Path('manifest.json').read_text())
    assert sha(Path(__file__)) == m['source_sha256']
    assert sha(INVENTORY) == m['window_inventory_sha256']
    assert sha(SOURCE / 'plan.json') == m['signal_plan_sha256']
    assert not Path('windows_360').exists(); Path('windows_360').mkdir()
    by_record = defaultdict(list)
    with INVENTORY.open() as handle:
        for row in csv.DictReader(handle): by_record[row['record']].append(row)
    plan = json.loads((SOURCE / 'plan.json').read_text())
    counts = Counter(); outputs = []; allocated = 0
    with Path('window_manifest.csv').open('w') as handle:
        fields = ['record', 'documented_group', 'lead', 'sample', 'symbol', 'class',
                  'unknown_in_window', 'noisy_in_window', 'unreadable_in_window', 'window_index']
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for item in plan['signals']:
            name = item['key'].rsplit('/', 1)[-1].removesuffix('.dat')
            assert sha(SOURCE / 'raw' / (name + '.dat')) == item['release_sha256']
            for ext in ('hea', 'atr'):
                assert sha(SOURCE / (name + '.' + ext)) == m['metadata_sha256'][name + '.' + ext]
            decoded = wfdb.rdrecord(str(LINKS / name), channels=[item['v5_index']])
            assert decoded.fs == 250 and decoded.sig_name == ['V5'] and decoded.units == ['mV']
            signal = decoded.p_signal[:, 0]; rows = by_record.pop(name)
            samples = np.array([int(r['sample']) for r in rows]); assert len(np.unique(samples)) == len(rows)
            assert all(r['lead'] == 'V5' and r['documented_group'] == item['patient_group'] for r in rows)
            source_windows = signal[samples[:, None] + np.arange(-125, 125)]
            assert np.isfinite(source_windows).all()
            result = resample_poly(source_windows.astype(np.float32), 36, 25, axis=1).astype(np.float32)
            assert result.shape == (len(rows), 360) and np.isfinite(result).all()
            # Recompute three individual windows to check indexing and vectorized resampling.
            for i in sorted({0, len(rows) // 2, len(rows) - 1}):
                direct = resample_poly(signal[samples[i]-125:samples[i]+125].astype(np.float32), 36, 25)
                np.testing.assert_allclose(result[i], direct, atol=1e-6, rtol=1e-6)
            path = Path('windows_360') / (name + '.npy'); np.save(path, result)
            allocated += path.stat().st_size; assert allocated <= m['waveform_byte_cap']
            local = Counter(r['class'] for r in rows); counts.update(local)
            for i, row in enumerate(rows): writer.writerow(dict(row, window_index=i))
            outputs.append({'record': name, 'group': item['patient_group'], 'windows': len(rows),
                            'classes': dict(local), 'sha256': sha(path), 'bytes': path.stat().st_size})
    assert not by_record and len(outputs) == 51 and dict(counts) == m['expected_classes']
    summary = {'status': 'complete', 'records': 51, 'classes': dict(counts), 'windows': sum(counts.values()),
               'waveform_bytes': allocated, 'files': outputs, 'manifest_sha256': sha(Path('window_manifest.csv')),
               'window_rule': 'native250Hz V5 mV [center-125,center+125), resample_poly(36,25),360samples',
               'scipy_version': scipy.__version__, 'wfdb_version': wfdb.__version__,
               'elapsed_seconds': time.monotonic()-began, 'development_only': True,
               'limits': 'No quality-flag exclusions, fitted normalization, subject split, duplicate screen, training or scores. V5 is not II/MLII. Source noise interpretation and cross-source person identity remain unresolved.'}
    Path('summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'files'}))


if __name__ == '__main__': run()
