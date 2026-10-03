"""Finite MIT-only subject-adversarial objective test; external sources not fitted."""
import csv,json,random,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader,TensorDataset
from ecg_baseline import sha256,CLASSES
from ecg_context_compare import load_parts,evaluate
from ecg_waveform_transform import apply,fit
from ecg_rr_compare import Model as Reference,timing,describe,external

class Reverse(torch.autograd.Function):
    @staticmethod
    def forward(ctx,h,weight):ctx.weight=weight;return h.view_as(h)
    @staticmethod
    def backward(ctx,grad):return -ctx.weight*grad,None
class Model(Reference):
    def __init__(self,subjects):super().__init__('combined');self.subject_head=nn.Linear(64,subjects)
    def training_logits(self,x,rr,weight):
        h=self.features(x);return self.head(torch.cat((h,rr),1)),self.subject_head(Reverse.apply(h,weight))
def subject_map(parts):
    names=sorted(set(parts['train']['subjects']));assert not set(names)&set(parts['validation']['subjects']) and not set(names)&set(parts['test']['subjects']);return {name:i for i,name in enumerate(names)}
def run():
    began=time.monotonic();m=json.loads(Path('manifest.json').read_text());assert torch.cuda.is_available();assert all(sha256(Path(n))==h for n,h in m['source_sha256'].items());assert not Path('output').exists();Path('output').mkdir();features=Path('features');device=torch.device('cuda')
    for f in m['timing_files']:assert sha256(features/(f['source']+'_'+f['record']+'.npy'))==f['sha256']
    for spec in m['waveform_sources']:
        assert sha256(Path(spec['root'],'window_manifest.csv'))==spec['csv_sha256']
        for record,h in spec['array_sha256'].items():assert sha256(Path(spec['root'],'windows_360',record+'.npy'))==h
    rows=[]
    for split in m['splits']:
        context=Path(split['context']);assert sha256(context)==split['context_sha256'] and sha256(Path(split['split']))==split['split_sha256'];parts=load_parts(Path(m['waveform_sources'][0]['root'],'windows_360'),context,Path(split['split']),expected=split['expected_counts']);timing(parts,context,features);mapping=subject_map(parts);domain=np.array([mapping[s] for s in parts['train']['subjects']],dtype=np.int64);counts=np.bincount(parts['train']['y'],minlength=4);weights=np.sqrt(counts[0]/counts);params=fit(parts['train']['x'],'centered');mean=parts['train']['rr'][:,:2].mean(0,dtype=np.float64);std=parts['train']['rr'][:,:2].std(0,dtype=np.float64);assert np.all(std>0);rr_params={'mean':mean,'std':std}
        for p in parts.values():p['x']=apply(p['x'],params)[:,None,:];p['rr'][:,:2]=(p['rr'][:,:2]-mean)/std
        support={s:np.bincount(parts['train']['y'][parts['train']['subjects']==s],minlength=4).tolist() for s in mapping}
        for seed in m['seeds']:
            for weight in m['adversarial_weights']:
                assert time.monotonic()-began<m['max_internal_seconds'];start=time.monotonic();random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False;torch.cuda.reset_peak_memory_stats()
                loaders={n:DataLoader(TensorDataset(torch.from_numpy(p['x']),torch.from_numpy(p['rr']),torch.from_numpy(p['y'])),batch_size=256,shuffle=False,num_workers=0) for n,p in parts.items() if n!='train'};train=DataLoader(TensorDataset(torch.from_numpy(parts['train']['x']),torch.from_numpy(parts['train']['rr']),torch.from_numpy(parts['train']['y']),torch.from_numpy(domain)),batch_size=256,shuffle=True,generator=torch.Generator().manual_seed(seed),num_workers=0)
                model=Model(len(mapping)).to(device);opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001);criterion=nn.CrossEntropyLoss(weight=torch.tensor(weights,dtype=torch.float32,device=device));best=float('inf');history=[];tag=f"{split['id']}_{seed}_{weight}";file=Path('output')/(tag+'.pt')
                for epoch in range(1,13):
                    assert time.monotonic()-began<m['max_internal_seconds'];model.train();class_sum=domain_sum=seen=correct=0
                    for x,rr,y,s in train:
                        opt.zero_grad(set_to_none=True);logits,subject=model.training_logits(x.to(device),rr.to(device),weight);class_loss=criterion(logits,y.to(device));subject_loss=nn.functional.cross_entropy(subject,s.to(device));(class_loss+subject_loss).backward();opt.step();n=len(y);seen+=n;class_sum+=class_loss.item()*n;domain_sum+=subject_loss.item()*n;correct+=(subject.argmax(1)==s.to(device)).sum().item()
                    val,f1=evaluate(model,loaders['validation'],device);history.append({'epoch':epoch,'validation_ce':val,'validation_macro_f1':f1,'mean_batch_weighted_classification_loss':class_sum/seen,'subject_loss':domain_sum/seen,'training_subject_accuracy':correct/seen})
                    if val<best:best=val;selected=epoch;torch.save({'state_dict':model.state_dict(),'epoch':epoch,'adversarial_weight':weight,'subject_mapping':mapping,'waveform_transform':params,'timing_mean':mean,'timing_std':std},file)
                saved=torch.load(file,map_location='cpu',weights_only=False);model.load_state_dict(saved['state_dict']);reloaded,_=evaluate(model,loaders['validation'],device);assert abs(reloaded-best)<1e-6;_,y,p=evaluate(model,loaders['test'],device,detail=True);test=describe(y,p,parts['test']['subjects']);incart=external(model,params,rr_params,m['waveform_sources'][1],features,device)
                row={'split':split['id'],'seed':seed,'adversarial_weight':weight,'selected_epoch':selected,'validation_ce':best,'reloaded_validation_ce':reloaded,'validation_history':history,'mit_development':test,'incart_development':incart,'training_subject_mapping':mapping,'training_subject_class_support_N_S_V_F':support,'training_subject_count':len(mapping),'largest_training_subject_fraction':float(np.bincount(domain).max()/len(domain)),'inference_parameter_count':sum(p.numel() for n,p in model.named_parameters() if not n.startswith('subject_head.')),'training_parameter_count':sum(p.numel() for p in model.parameters()),'elapsed_seconds':time.monotonic()-start,'peak_gpu_bytes':torch.cuda.max_memory_allocated(),'checkpoint_sha256':sha256(file),'waveform_transform':params,'timing_mean':mean.tolist(),'timing_std':std.tolist()};rows.append(row)
                with Path('output/rows.jsonl').open('a') as out:out.write(json.dumps(row)+'\n')
                print(json.dumps({k:row[k] for k in ['split','seed','adversarial_weight','selected_epoch','elapsed_seconds']}),flush=True);assert sum(p.stat().st_size for p in Path('output').glob('*'))<m['output_byte_cap']
    assert len(rows)==18
    Path('output/result.json').write_text(json.dumps({'status':'complete','rows':rows,'manifest_sha256':sha256(Path('manifest.json')),'gpu_name':torch.cuda.get_device_name(),'torch_version':torch.__version__,'elapsed_seconds':time.monotonic()-began,'limits':'MIT training subject labels only, no validation/test subject fitting. Inspected development cohorts, centered waveform and annotation-assisted past-only timing. No EDB/SVDB scoring or fresh confirmation.'},indent=2)+'\n')
def selfcheck():
    torch.manual_seed(42);a=Reference('combined');torch.manual_seed(42);b=Model(3);x=torch.randn(2,1,360);rr=torch.randn(2,3);torch.testing.assert_close(a(x,rr),b(x,rr));c,s=b.training_logits(x,rr,0);torch.testing.assert_close(c,b(x,rr));assert s.shape==(2,3)
    h=torch.randn(4,64,requires_grad=True);layer=nn.Linear(64,3);labels=torch.tensor([0,1,2,0]);loss=nn.functional.cross_entropy(layer(h),labels);ordinary=torch.autograd.grad(loss,(h,layer.weight),retain_graph=True);reversed_loss=nn.functional.cross_entropy(layer(Reverse.apply(h,.2)),labels);reversed_grads=torch.autograd.grad(reversed_loss,(h,layer.weight));torch.testing.assert_close(reversed_grads[0],-.2*ordinary[0]);torch.testing.assert_close(reversed_grads[1],ordinary[1]);zero=torch.autograd.grad(nn.functional.cross_entropy(layer(Reverse.apply(h,0)),labels),h)[0];torch.testing.assert_close(zero,torch.zeros_like(h));print('paired initial logits, reversal sign/scale, ordinary head gradient and zero control passed')
if __name__=='__main__':
    import sys
    if '--selfcheck' in sys.argv:selfcheck()
    else:run()
