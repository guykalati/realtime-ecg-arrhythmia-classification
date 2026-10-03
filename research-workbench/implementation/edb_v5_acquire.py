"""Download a frozen named-lead EDB waveform subset; no model scores or windows."""
import hashlib,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from incart_signal_download import download_one

def run():
    plan=json.loads(Path('plan.json').read_text())
    for n,d in plan['files_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==d
    assert len(plan['signals'])==51 and sum(r['size'] for r in plan['signals'])<=plan['byte_cap']
    target=Path('raw');target.mkdir(exist_ok=True)
    def fetch(item):
        row=download_one(item,target)
        assert row['sha256']==item['release_sha256'], 'official release checksum mismatch'
        print(item['key']+' verified',flush=True);return row
    with ThreadPoolExecutor(max_workers=2) as pool:checked=list(pool.map(fetch,plan['signals']))
    Path('result.json').write_text(json.dumps({'status':'completed','files':checked,'bytes':sum(x['size'] for x in checked),'role':'development acquisition only','no_model_scores':True},indent=2)+'\n')
if __name__=='__main__':run()
