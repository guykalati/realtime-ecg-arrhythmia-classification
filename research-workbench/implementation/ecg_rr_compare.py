"""Frozen waveform/timing/combined development ablation, no target-domain fitting."""
import csv,json,random,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader,TensorDataset
from ecg_baseline import CLASSES,metrics,sha256
from ecg_context_compare import CNN,load_parts,evaluate,calibration
from ecg_waveform_transform import apply,fit

class Model(nn.Module):
    def __init__(self,mode):
        super().__init__();self.mode=mode
        if mode=='timing':self.head=nn.Sequential(nn.Linear(3,16),nn.ReLU(),nn.Linear(16,4))
        else:
            base=CNN(context=False);self.features=base.features
            if mode=='waveform':self.head=base.head
            else:
                self.head=nn.Linear(67,4)
                with torch.no_grad():
                    self.head.weight[:,:64].copy_(base.head.weight);self.head.weight[:,64:].zero_();self.head.bias.copy_(base.head.bias)
    def forward(self,x,rr):
        if self.mode=='timing':return self.head(rr)
        h=self.features(x)
        return self.head(h if self.mode=='waveform' else torch.cat((h,rr),1))
def describe(y,p,subjects):
    predicted=p.argmax(1);d=metrics(y,predicted);d.update(calibration(y,p));d['cross_entropy']=float(-np.log(np.maximum(p[np.arange(len(y)),y],1e-12)).mean())
    d['per_group']={str(s):metrics(y[subjects==s],predicted[subjects==s]) for s in sorted(set(subjects))}
    return d
def timing(parts,context,features):
    values=defaultdict(list);arrays={}
    for row in csv.DictReader(context.open()):
        record=row['record_id'];arrays.setdefault(record,None)
        if arrays[record] is None:arrays[record]=np.load(features/('MIT_'+record+'.npy'))
        values[row['split']].append(arrays[record][int(row['target_index'])])
    for name,part in parts.items():
        part['rr']=np.asarray(values[name],dtype=np.float32);assert part['rr'].shape==(len(part['y']),3)
        part['x']=part['x'][:,0,:].copy()
def external(model,params,rr_params,spec,features,device):
    groups=defaultdict(list)
    for row in csv.DictReader(Path(spec['root'],'window_manifest.csv').open()):groups[row['record_id']].append(row)
    ys=[];probabilities=[];subjects=[]
    model.eval()
    with torch.no_grad():
        for record,rows in sorted(groups.items()):
            array=np.load(Path(spec['root'],'windows_360',record+'.npy'),mmap_mode='r');rr=np.load(features/('INCART_'+record+'.npy'));assert len(rows)==len(array)==len(rr)
            for begin in range(0,len(rows),512):
                stop=begin+512;x=apply(np.asarray(array[begin:stop]),params)[:,None,:];r=rr[begin:stop].copy();r[:,:2]=(r[:,:2]-rr_params['mean'])/rr_params['std']
                p=model(torch.from_numpy(np.ascontiguousarray(x)).to(device),torch.from_numpy(r).to(device)).softmax(1).cpu().numpy();probabilities.extend(p)
                ys.extend(CLASSES.index(row['class_4']) for row in rows[begin:stop]);subjects.extend(row['patient_id'] for row in rows[begin:stop])
    return describe(np.asarray(ys),np.asarray(probabilities),np.asarray(subjects))
def run():
    began=time.monotonic();m=json.loads(Path('manifest.json').read_text());assert torch.cuda.is_available();assert all(sha256(Path(n))==h for n,h in m['source_sha256'].items())
    assert not Path('output').exists();Path('output').mkdir();features=Path('features')
    for f in m['timing_files']:assert sha256(features/(f['source']+'_'+f['record']+'.npy'))==f['sha256']
    for spec in m['waveform_sources']:
        assert sha256(Path(spec['root'],'window_manifest.csv'))==spec['csv_sha256']
        for record,h in spec['array_sha256'].items():assert sha256(Path(spec['root'],'windows_360',record+'.npy'))==h
    device=torch.device('cuda');rows=[]
    for split in m['splits']:
        context=Path(split['context']);assert sha256(context)==split['context_sha256'];assert sha256(Path(split['split']))==split['split_sha256']
        parts=load_parts(Path(m['waveform_sources'][0]['root'],'windows_360'),context,Path(split['split']),expected=split['expected_counts']);timing(parts,context,features)
        params=fit(parts['train']['x'],'centered');mean=parts['train']['rr'][:,:2].mean(0,dtype=np.float64);std=parts['train']['rr'][:,:2].std(0,dtype=np.float64);assert np.all(std>0);rr_params={'mean':mean,'std':std}
        for part in parts.values():part['x']=apply(part['x'],params)[:,None,:];part['rr'][:,:2]=(part['rr'][:,:2]-mean)/std
        counts=np.bincount(parts['train']['y'],minlength=4);weights=np.sqrt(counts[0]/counts)
        for seed in m['seeds']:
            for mode in ['waveform','timing','combined']:
                assert time.monotonic()-began<780,'13-minute internal cap';start=time.monotonic();random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False;torch.cuda.reset_peak_memory_stats()
                loaders={n:DataLoader(TensorDataset(torch.from_numpy(p['x']),torch.from_numpy(p['rr']),torch.from_numpy(p['y'])),batch_size=256,shuffle=n=='train',generator=torch.Generator().manual_seed(seed),num_workers=0) for n,p in parts.items()}
                model=Model(mode).to(device);optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001);criterion=nn.CrossEntropyLoss(weight=torch.tensor(weights,dtype=torch.float32,device=device));best=float('inf');history=[];file=Path('output')/(split['id']+'_'+str(seed)+'_'+mode+'.pt')
                for epoch in range(1,13):
                    assert time.monotonic()-began<780,'13-minute internal cap';model.train()
                    for x,rr,y in loaders['train']:
                        optimizer.zero_grad(set_to_none=True);loss=criterion(model(x.to(device),rr.to(device)),y.to(device));loss.backward();optimizer.step()
                    val,f1=evaluate(model,loaders['validation'],device);history.append({'epoch':epoch,'validation_ce':val,'validation_macro_f1':f1})
                    if val<best:best=val;selected=epoch;torch.save({'state_dict':model.state_dict(),'mode':mode,'epoch':epoch,'transform':params,'timing_mean':mean,'timing_std':std},file)
                saved=torch.load(file,map_location='cpu',weights_only=False);model.load_state_dict(saved['state_dict']);reloaded_ce,_=evaluate(model,loaders['validation'],device);assert abs(reloaded_ce-best)<1e-6
                _,y,p=evaluate(model,loaders['test'],device,detail=True);test=describe(y,p,parts['test']['subjects']);incart=external(model,params,rr_params,m['waveform_sources'][1],features,device)
                row={'split':split['id'],'seed':seed,'mode':mode,'selected_epoch':selected,'validation_ce':best,'reloaded_validation_ce':reloaded_ce,'validation_history':history,'mit_development':test,'incart_development':incart,'parameter_count':sum(p.numel() for p in model.parameters()),'elapsed_seconds':time.monotonic()-start,'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'checkpoint_sha256':sha256(file),'waveform_transform':params,'timing_mean':mean.tolist(),'timing_std':std.tolist()};rows.append(row)
                with Path('output/rows.jsonl').open('a') as out:out.write(json.dumps(row)+'\n')
                print(json.dumps({k:row[k] for k in ['split','seed','mode','selected_epoch','elapsed_seconds']}),flush=True);assert sum(p.stat().st_size for p in Path('output').glob('*'))<80_000_000
    assert len(rows)==18
    Path('output/result.json').write_text(json.dumps({'status':'complete','rows':rows,'manifest_sha256':sha256(Path('manifest.json')),'gpu_name':torch.cuda.get_device_name(),'torch_version':torch.__version__,'elapsed_seconds':time.monotonic()-began,'limits':'Inspected development sets, annotation-assisted timing and centered waveform latency; no EDB/SVDB scoring or final confirmation. No INCART fitting.'},indent=2)+'\n')
def selfcheck():
    torch.manual_seed(42);a=Model('waveform');torch.manual_seed(42);b=Model('combined');x=torch.randn(2,1,360);rr=torch.randn(2,3);torch.testing.assert_close(a(x,rr),b(x,rr));assert Model('timing')(x,rr).shape==(2,4)
if __name__=='__main__':
    import sys
    if '--selfcheck' in sys.argv:selfcheck();print('paired initial-logit/timing shape selfcheck passed')
    else:run()
