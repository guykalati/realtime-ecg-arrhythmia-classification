"""Local five-class model inference and annotated replay; no clinical use."""
import argparse,json,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
def predict(x,weights,mean,std):
    x=((np.asarray(x,dtype=np.float32)-mean)/std)[None,None,:]
    for i,k in [(0,7),(3,5),(6,3)]:
        window=np.lib.stride_tricks.sliding_window_view(np.pad(x,((0,0),(0,0),(k//2,k//2))),k,axis=2)
        x=np.einsum('bclk,ock->bol',window,weights[f'net.{i}.weight'],optimize=True)+weights[f'net.{i}.bias'][None,:,None]
        x=np.maximum(x,0);n=x.shape[2]//2;x=x[:,:,:n*2].reshape(x.shape[0],x.shape[1],n,2).max(3)
    return x.mean(2)@weights['net.11.weight'].T+weights['net.11.bias']
def verify(output):
    data=json.loads((output/'replay_verified.json').read_text());weights=np.load(output/'weights.npz')
    errors=[];durations=[]
    for beat in data['beats']:
        t=time.perf_counter();got=predict(beat['waveform'],weights,data['mean'],data['std'])[0];durations.append(time.perf_counter()-t)
        expected=np.array(beat['torch_logits']);errors.append(float(np.max(np.abs(got-expected))))
        assert np.allclose(got,expected,atol=1e-4,rtol=1e-4),beat['id']
        assert got.argmax()==expected.argmax()
    return {'status':'passed','cases':len(errors),'max_logit_error':max(errors),'numpy_latency_median_ms':float(np.median(durations)*1000),'numpy_latency_p95_ms':float(np.percentile(durations,95)*1000),'numpy':np.__version__}
def serve(output,port):
    data=json.loads((output/'replay_verified.json').read_text());weights=np.load(output/'weights.npz')
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/':
                body=(ROOT/'index.html').read_bytes();kind='text/html'
            elif self.path=='/api/replay':
                body=json.dumps({'classes':data['classes'],'sampling_hz':360,'beats':[{'id':b['id'],'label':b['label'],'waveform':b['waveform']} for b in data['beats']]}).encode();kind='application/json'
            elif self.path.startswith('/api/predict?index='):
                try:
                    i=int(self.path.split('=')[1]);assert 0<=i<len(data['beats']);beat=data['beats'][i];t=time.perf_counter()
                    logits=predict(beat['waveform'],weights,data['mean'],data['std'])[0];prob=np.exp(logits-logits.max());prob/=prob.sum();c=data['classes'][int(prob.argmax())]
                    body=json.dumps({'id':beat['id'],'prediction':c,'probabilities':prob.tolist(),'inference_ms':(time.perf_counter()-t)*1000,'simulated_alert':c!='N'}).encode();kind='application/json'
                except (ValueError,AssertionError,IndexError):self.send_error(400);return
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    print(f'http://127.0.0.1:{port}',flush=True);ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'output');p.add_argument('--port',type=int,default=8766);p.add_argument('--verify',action='store_true');a=p.parse_args()
    if a.verify: print(json.dumps(verify(a.output),indent=2))
    else:serve(a.output,a.port)
