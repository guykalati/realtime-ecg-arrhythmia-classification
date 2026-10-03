"""Five-class, subject-disjoint MIT-BIH CNN; run only on an allocated GPU."""
import argparse, csv, hashlib, json, time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from ecg_split_guard import validate

CLASSES = 'NSVFQ'
SEED = 20261003
def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        layers=[]; channels=1
        for out,k in [(16,7),(32,5),(64,3)]:
            layers += [nn.Conv1d(channels,out,k,padding=k//2),nn.ReLU(),nn.MaxPool1d(2)]
            channels=out
        self.net=nn.Sequential(*layers,nn.AdaptiveAvgPool1d(1),nn.Flatten(),nn.Linear(64,5))
    def forward(self,x): return self.net(x)

def score(y,p):
    m=np.bincount(5*y+p,minlength=25).reshape(5,5)
    rows={}
    for i,c in enumerate(CLASSES):
        support=int(m[i].sum()); predictions=int(m[:,i].sum()); tp=int(m[i,i])
        pr=tp/predictions if predictions else 0.; re=tp/support if support else 0.
        rows[c]={'support':support,'precision':pr,'recall':re,'f1':2*pr*re/(pr+re) if pr+re else 0.}
    return {'count':int(m.sum()),'accuracy':float(m.trace()/m.sum()),'macro_f1':float(np.mean([r['f1'] for r in rows.values()])),
            'weighted_f1':sum(r['f1']*r['support'] for r in rows.values())/m.sum(),
            'per_class':rows,'confusion_matrix':m.tolist()}

def run(a):
    assert torch.cuda.is_available(), 'Use a Slurm GPU allocation'
    assert not a.output.exists(), 'Refuse to overwrite an existing run'
    start=time.monotonic(); torch.set_num_threads(2)
    np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic=True; torch.backends.cudnn.benchmark=False
    validate(a.split)
    split={r['record_id']:r for r in csv.DictReader(a.split.open())}
    grouped={r:[] for r in split}
    for row in csv.DictReader(a.manifest.open()):
        assert row['subject_group']==split[row['record_id']]['patient_id']
        if row['class_5'] in CLASSES: grouped[row['record_id']].append(row)
    parts={k:{'x':[],'y':[],'ids':[]} for k in ['train','validation','test']}; hashes={}
    for rid,rows in grouped.items():
        path=a.windows/(rid+'.npy'); hashes[rid]=digest(path); x=np.load(path)
        ix=[int(r['window_index']) for r in rows]; part=parts[split[rid]['split']]
        part['x'].append(x[ix]); part['y'] += [CLASSES.index(r['class_5']) for r in rows]
        part['ids'] += [r['record_id']+':'+r['sample_index'] for r in rows]
    for p in parts.values():
        p['x']=np.concatenate(p['x']).astype('float32'); p['y']=np.array(p['y'],dtype='int64')
        assert np.isfinite(p['x']).all() and set(p['y'])==set(range(5)), 'Every split must support all five classes'
    mean=float(parts['train']['x'].mean(dtype='float64')); std=float(parts['train']['x'].std(dtype='float64'))
    assert std>0
    loaders={k:DataLoader(TensorDataset(torch.from_numpy(((p['x']-mean)/std)[:,None,:]),torch.from_numpy(p['y'])),
                         batch_size=256,shuffle=k=='train',generator=torch.Generator().manual_seed(SEED)) for k,p in parts.items()}
    model=CNN().cuda(); optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
    counts=np.bincount(parts['train']['y'],minlength=5)
    weights=torch.tensor(np.sqrt(counts.sum()/(5*counts)),dtype=torch.float32,device='cuda')
    train_loss=nn.CrossEntropyLoss(weight=weights)
    def evaluate(loader):
        model.eval(); total=0.; yy=[]; pp=[]
        with torch.inference_mode():
            for x,y in loader:
                logits=model(x.cuda()); total+=nn.functional.cross_entropy(logits,y.cuda(),reduction='sum').item()
                yy.extend(y.tolist()); pp.extend(logits.argmax(1).cpu().tolist())
        return total/len(yy),np.array(yy),np.array(pp)
    history=[]; best=float('inf'); state=None
    a.output.mkdir(parents=True)
    for epoch in range(1,25):
        assert time.monotonic()-start<1500,'25 minute internal cap'
        model.train(); total=0.
        for x,y in loaders['train']:
            optimizer.zero_grad(set_to_none=True); loss=train_loss(model(x.cuda()),y.cuda())
            loss.backward(); optimizer.step(); total+=loss.item()*len(y)
        vl,yy,pp=evaluate(loaders['validation']); row={'epoch':epoch,'train_loss':total/len(parts['train']['y']),'validation_cross_entropy':vl,'validation_macro_f1':score(yy,pp)['macro_f1']}
        history.append(row); print(json.dumps(row),flush=True)
        if vl<best:
            best=vl; selected=epoch; state={k:v.cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(state); tl,yy,pp=evaluate(loaders['test'])
    torch.save({'state_dict':state,'mean':mean,'std':std,'classes':CLASSES},a.output/'model.pt')
    np.savez_compressed(a.output/'weights.npz',**{k:v.numpy() for k,v in state.items()})
    # A fixed, balanced annotated replay set is a demo, not a second benchmark.
    ix=np.concatenate([np.flatnonzero(yy==i)[:10] for i in range(5)])
    raw=parts['test']['x'][ix]; normalized=torch.from_numpy(((raw-mean)/std)[:,None,:]).cuda()
    with torch.inference_mode(): logits=model(normalized).cpu().numpy()
    demo={'classes':CLASSES,'sampling_hz':360,'mean':mean,'std':std,'beats':[{'id':parts['test']['ids'][int(j)],'label':CLASSES[int(yy[j])],'waveform':raw[n].tolist(),'torch_logits':logits[n].tolist()} for n,j in enumerate(ix)]}
    (a.output/'replay.json').write_text(json.dumps(demo))
    np.savez_compressed(a.output/'test_predictions.npz',actual=yy,predicted=pp)
    result={'status':'completed','seed':SEED,'epochs':24,'selected_epoch':selected,'classes':CLASSES,'counts':{k:np.bincount(p['y'],minlength=5).tolist() for k,p in parts.items()},
            'train_mean':mean,'train_std':std,'history':history,'test':score(yy,pp),'test_cross_entropy':tl,'seconds':time.monotonic()-start,
            'source_sha256':digest(__file__),'split_sha256':digest(a.split),'manifest_sha256':digest(a.manifest),'windows_sha256':hashes,
            'artifacts_sha256':{p.name:digest(p) for p in a.output.iterdir() if p.is_file()},'gpu':torch.cuda.get_device_name(),'torch':torch.__version__,
            'limitations':'Annotated peak windows; all five mapped classes include paced subjects. Patient-disjoint test. MLII except V5 for 102/104. No live detection or clinical validation.'}
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['test']),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('windows',type=Path);p.add_argument('manifest',type=Path);p.add_argument('split',type=Path);p.add_argument('output',type=Path)
    run(p.parse_args())
