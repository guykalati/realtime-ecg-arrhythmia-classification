"""Source decoding and named-channel QA on two10-second segments per EDB record."""
import hashlib,json,time
from pathlib import Path
import numpy as np,wfdb
S=Path('/home/guykalat/codex_edb_v5_acquire_20261001')
def run():
    begin=time.monotonic();m=json.loads(Path('manifest.json').read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==m['source_sha256']
    plan=json.loads((S/'plan.json').read_text());assert hashlib.sha256((S/'plan.json').read_bytes()).hexdigest()==m['signal_plan_sha256']
    work=Path('links');work.mkdir(exist_ok=True);results=[]
    for item in plan['signals']:
        name=item['key'].rsplit('/',1)[-1].removesuffix('.dat')
        for ext in ['hea','atr','dat']:
            original=S/('raw' if ext=='dat' else '')/(name+'.'+ext);link=work/(name+'.'+ext)
            if not link.exists():link.symlink_to(original)
        header=wfdb.rdheader(str(work/name));index=header.sig_name.index('V5')
        assert header.fs==250 and header.n_sig==2 and index==item['v5_index']
        assert header.units[index]=='mV'
        annotation=wfdb.rdann(str(work/name),'atr');assert np.all(np.diff(annotation.sample)>=0) and annotation.sample.max()<header.sig_len
        segments=[]
        for start in [0,header.sig_len//2]:
            stop=start+2500
            digital=wfdb.rdrecord(str(work/name),sampfrom=start,sampto=stop,channels=[index],physical=False).d_signal[:,0]
            physical=wfdb.rdrecord(str(work/name),sampfrom=start,sampto=stop,channels=[index],physical=True).p_signal[:,0]
            expected=(digital.astype(float)-header.baseline[index])/header.adc_gain[index]
            finite=np.isfinite(physical);assert np.allclose(expected[finite],physical[finite],atol=1e-12)
            segments.append({'start_sample':start,'samples':len(physical),'finite_samples':int(finite.sum()),'physical_min_mv':float(physical[finite].min()) if finite.any() else None,'physical_max_mv':float(physical[finite].max()) if finite.any() else None,'std_mv':float(physical[finite].std()) if finite.any() else None})
        results.append({'record_id':name,'patient_group':item['patient_group'],'fs':header.fs,'lead':'V5','channel_index':index,'gain':header.adc_gain[index],'baseline':header.baseline[index],'units':header.units[index],'samples':header.sig_len,'annotation_events':len(annotation.sample),'segments':segments})
    assert len(results)==51
    output={'status':'passed','records':51,'segment_seconds_per_record':20,'wfdb_version':wfdb.__version__,'numpy_version':np.__version__,'rows':results,'elapsed_seconds':time.monotonic()-begin,'no_model_scores':True,'limits':'Source gain/channel decoding and annotation bounds on two10-second segments. Not full-record signal-quality validation, resampling/window cohort, recording-duplicate screen or cross-source identity proof.'}
    Path('result.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='rows'}))
if __name__=='__main__':run()
