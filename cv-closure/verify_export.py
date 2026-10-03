"""Independent float32 CPU reference for the selected CNN export."""
import json,hashlib
from pathlib import Path
import numpy as np,torch
from train import CNN
p=Path('output');torch.set_num_threads(2)
checkpoint=torch.load(p/'model.pt',map_location='cpu',weights_only=True);m=CNN().eval();m.load_state_dict(checkpoint['state_dict'])
d=json.loads((p/'replay.json').read_text());previous=[]
with torch.inference_mode():
    for b in d['beats']:
        x=(np.array(b['waveform'],dtype='float32')-d['mean'])/d['std'];got=m(torch.from_numpy(x[None,None,:]))[0].numpy()
        previous.append(float(np.max(np.abs(got-np.array(b['torch_logits'])))));b['torch_logits']=got.tolist()
d['reference']='Independent PyTorch float32 CPU; original GPU export may use TF32'
(p/'replay_verified.json').write_text(json.dumps(d))
audit={'status':'completed','cases':len(previous),'original_gpu_vs_cpu_max_error':max(previous),'model_sha256':hashlib.sha256((p/'model.pt').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'replay_verified_sha256':hashlib.sha256((p/'replay_verified.json').read_bytes()).hexdigest(),'torch':torch.__version__}
(p/'export_audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit))
