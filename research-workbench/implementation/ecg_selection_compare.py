"""Paired CE/macro-F1 checkpoint selection on the same frozen training trajectory."""
import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from ecg_baseline import CLASSES, metrics, sha256
from ecg_context_compare import CNN, calibration, evaluate, load_parts
from ecg_multiscale_compare import MultiScaleCNN
from ecg_robustness_compare import external
from ecg_waveform_transform import apply, fit


def run(manifest_path, index):
    batch = json.loads(manifest_path.read_text())
    cell = batch['cells'][index]
    for name, digest in batch['source_sha256'].items():
        if sha256(manifest_path.parent / name) != digest:
            raise ValueError(f'frozen source changed: {name}')
    for field in ('context', 'split', 'incart_manifest'):
        if sha256(Path(cell[field])) != cell[field + '_sha256']:
            raise ValueError(f'frozen input changed: {field}')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA allocation required')
    output = manifest_path.parent / 'output' / cell['id']
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    parts = load_parts(Path(batch['windows_dir']), Path(cell['context']),
                       Path(cell['split']), expected=cell['expected'])
    seed = cell['seed']
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = torch.device('cuda')
    transform = fit(parts['train']['x'][:, 0, :], 'centered')
    counts = np.bincount(parts['train']['y'], minlength=4)
    if np.any(counts == 0):
        raise ValueError('missing training class')
    weights = np.sqrt(counts[0] / counts)
    loaders = {}
    for name, part in parts.items():
        x = apply(part['x'][:, 0, :], transform)[:, None, :]
        dataset = TensorDataset(torch.from_numpy(np.ascontiguousarray(x)),
                                torch.zeros(len(x), 2), torch.from_numpy(part['y']))
        loaders[name] = DataLoader(dataset, batch_size=256, shuffle=name == 'train',
                                   num_workers=0, pin_memory=True,
                                   generator=torch.Generator().manual_seed(seed))
    model = (CNN(context=False) if cell['model'] == 'cnn' else MultiScaleCNN()).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.0001)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    torch.cuda.reset_peak_memory_stats()
    best = {'ce': float('inf'), 'macro': float('-inf')}
    selected, history = {}, []
    checkpoints = {}
    for policy in best:
        (output / policy).mkdir()
        checkpoints[policy] = output / policy / 'best.pt'
    for epoch in range(1, batch['epochs'] + 1):
        model.train()
        total_loss, targets = 0., 0
        for x, rr, y in loaders['train']:
            if time.monotonic() - started > batch['internal_seconds']:
                raise TimeoutError('frozen internal training cap')
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(x.to(device), rr.to(device)), y.to(device))
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y)
            targets += len(y)
        val_loss, val_f1 = evaluate(model, loaders['validation'], device)
        row = {'epoch': epoch, 'training_weighted_ce': total_loss / targets,
               'validation_unweighted_ce': val_loss, 'validation_macro_f1': val_f1}
        history.append(row)
        print(json.dumps({'cell': cell['id'], **row}), flush=True)
        (output / 'history.json').write_text(json.dumps(history, indent=2) + '\n')
        for policy, value in [('ce', val_loss), ('macro', val_f1)]:
            improved = value < best[policy] if policy == 'ce' else value > best[policy]
            if improved:
                best[policy], selected[policy] = value, epoch
                torch.save({'state_dict': {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                            'epoch': epoch, 'transform': transform, 'cell': cell}, checkpoints[policy])
    for policy, checkpoint in checkpoints.items():
        saved = torch.load(checkpoint, map_location=device, weights_only=False)
        model.load_state_dict(saved['state_dict'])
        results = {}
        for name in ('validation', 'test'):
            loss, y, p = evaluate(model, loaders[name], device, detail=True)
            pred = p.argmax(1)
            result = metrics(y, pred)
            result.update(calibration(y, p))
            result['cross_entropy'] = loss
            subjects = parts[name]['subjects']
            result['per_subject'] = {s: metrics(y[subjects == s], pred[subjects == s])
                                     for s in sorted(set(subjects))}
            results[name] = result
            np.savez_compressed(output / policy / f'{name}_scores.npz', y=y, p=p, subject=subjects)
        results['incart'] = external(model, transform, Path(batch['incart_windows_dir']),
                                     Path(cell['incart_manifest']), device)
        result = {'status': 'success', 'policy': policy, 'cell': cell, 'epochs_completed': len(history),
                  'selected_epoch': selected[policy], 'selected_validation_ce': history[selected[policy]-1]['validation_unweighted_ce'],
                  'selected_validation_macro_f1': history[selected[policy]-1]['validation_macro_f1'],
                  'history': history, 'transform': transform,
                  'counts': {name: dict(Counter(CLASSES[i] for i in p['y'])) for name, p in parts.items()},
                  'parameter_count': sum(p.numel() for p in model.parameters()),
                  'metrics': results, 'checkpoint_sha256': sha256(checkpoint),
                  'batch_manifest_sha256': sha256(manifest_path),
                  'elapsed_seconds': time.monotonic() - started,
                  'gpu_peak_bytes': torch.cuda.max_memory_allocated(),
                  'gpu_name': torch.cuda.get_device_name(), 'torch_version': torch.__version__}
        (output / policy / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'complete': cell['id'], 'policy': policy, 'selected_epoch': selected[policy],
                          'mitdb_macro_f1': results['test']['macro_f1_present_classes'],
                          'incart_macro_f1': results['incart']['macro_f1_present_classes']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('index', type=int)
    args = parser.parse_args()
    run(args.manifest, args.index)
