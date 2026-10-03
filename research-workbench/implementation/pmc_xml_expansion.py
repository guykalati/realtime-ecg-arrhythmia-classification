"""Frozen 981-article quality acquisition; outputs are not training eligibility labels."""
import hashlib
import json
import re
import shutil
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError

from pmc_metadata_pilot import read_jsonl, append_jsonl
from pmc_xml_pilot import download, source_url, inspect_xml

BASE = Path(__file__).resolve().parent
OUT = BASE / 'data/pmc_xml_expansion_20260929'
CAP = 2_000_000_000

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def normalized(text):
    return ' '.join(re.findall(r'\w+', text.casefold()))

def shingles(text):
    tokens = normalized(text).split()
    return {' '.join(tokens[i:i+5]) for i in range(len(tokens)-4)}

def extract(path):
    root = ET.parse(path).getroot()
    paragraphs = []
    def walk(node, section):
        if node.tag == 'sec':
            title = node.find('title')
            section = section + [' '.join(title.itertext()).strip() if title is not None else 'untitled']
        if node.tag in ('p', 'table-wrap', 'fig'):
            paragraphs.append({'kind': node.tag, 'section': section,
                               'text': ' '.join(node.itertext()).strip()})
            return
        for child in node:
            walk(child, section)
    abstract = root.find('./front/article-meta/abstract')
    body = root.find('body')
    if body is not None:
        walk(body, [])
    return {'abstract': ' '.join(abstract.itertext()).strip() if abstract is not None else '',
            'paragraphs': paragraphs}

def run():
    audit_path = BASE / 'pmc_scope_benchmark_audit_2026-09-29.jsonl'
    metadata_path = BASE / 'pmc_metadata_1000_2026-09-28.jsonl'
    benchmark_path = BASE / 'data/pubmedqa_exclusion_2026-09-29/ori_pqal.json'
    assert sha(benchmark_path) == '8b3276be8942ebbd77f3ddcda12c1749bf0e490045a736fd8438ee40cf37a41d'
    metadata = {r['pmcid']: r for r in read_jsonl(metadata_path)}
    plan = []
    for row in read_jsonl(audit_path):
        if row.get('status') != 'version_candidate' or row.get('benchmark_overlap') != 'no_exact_pmid_match' or not row.get('pmid'):
            continue
        version = next(v for v in metadata[row['pmcid']]['versions'] if v['name'] == row['version'])
        url, md5 = source_url(version['metadata']['xml_url'], row['version'])
        plan.append({k: row[k] for k in ('pmcid','version','pmid','doi','license_code')} | {'url':url,'md5':md5})
    assert len(plan) == 981 and len({r['pmcid'] for r in plan}) == 981
    contract = {'sources': {p.name:sha(p) for p in (audit_path,metadata_path,benchmark_path)},
                'byte_cap':CAP,'plan':plan,'shingles':5,'minimum_shared':30,'jaccard':.8,'containment':.9}
    OUT.mkdir(parents=True, exist_ok=True)
    saved = OUT / 'contract.json'
    if saved.exists():
        assert json.loads(saved.read_text()) == contract, 'frozen acquisition contract changed'
    else:
        saved.write_text(json.dumps(contract,indent=2)+'\n')
    xml_dir = OUT / 'xml'
    xml_dir.mkdir(exist_ok=True)
    checks = OUT / 'checks.jsonl'
    failures = OUT / 'failures.jsonl'
    seen = {r['pmcid'] for r in read_jsonl(checks)}
    failed = {r['pmcid'] for r in read_jsonl(failures)}
    bytes_used = sum(p.stat().st_size for p in xml_dir.glob('*.xml'))
    for item in plan:
        if item['pmcid'] in seen or item['pmcid'] in failed:
            continue
        target = xml_dir / (item['version']+'.xml')
        old = BASE / 'data/pmc_xml_pilot_2026-09-28/xml' / target.name
        if not target.exists() and old.exists():
            assert hashlib.md5(old.read_bytes()).hexdigest() == item['md5']
            assert bytes_used + old.stat().st_size <= CAP
            shutil.copyfile(old,target)
        try:
            size, digest = download(item['url'],target,item['md5'],bytes_used,CAP)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            if isinstance(exc, ValueError) and 'MD5 mismatch' not in str(exc):
                raise
            append_jsonl(failures, item | {'error': str(exc), 'eligible_for_use': False})
            failed.add(item['pmcid'])
            print(f'EXCLUDED {item["version"]}: {exc}', flush=True)
            time.sleep(.5)
            continue
        bytes_used = sum(p.stat().st_size for p in xml_dir.glob('*.xml'))
        append_jsonl(checks,item | {'bytes':size,'verified_md5':digest,'sha256':sha(target),**inspect_xml(target)})
        seen.add(item['pmcid'])
        print(f'XML {len(seen)}/981; {bytes_used} bytes',flush=True)
        time.sleep(.5)
    # Read benchmark contexts only; questions and answers never enter corpus outputs.
    reference = {str(pmid):shingles(' '.join(row['CONTEXTS']))
                 for pmid,row in json.loads(benchmark_path.read_text()).items()}
    inverted = defaultdict(list)
    for pmid,values in reference.items():
        for value in values:
            inverted[value].append(pmid)
    rows = read_jsonl(checks)
    documents = OUT / 'documents.jsonl'
    screens = OUT / 'screens.jsonl'
    doi_seen, text_seen = {}, {}
    # Deterministic replacement makes resumed processing idempotent.
    with documents.open('w') as doc_handle, screens.open('w') as screen_handle:
        for row in rows:
            path = xml_dir / (row['version']+'.xml')
            assert sha(path) == row['sha256']
            if not row.get('jats_article'):
                screen_handle.write(json.dumps({'pmcid':row['pmcid'],'unusable_xml':True})+'\n')
                continue
            content = extract(path)
            body = ' '.join(p['text'] for p in content['paragraphs'])
            digest = hashlib.sha256(normalized(body).encode()).hexdigest()
            values = shingles(content['abstract']+' '+body)
            shared = Counter(pmid for value in values for pmid in inverted.get(value,()))
            matches = []
            for pmid,count in shared.items():
                if count < 30:
                    continue
                jaccard = count / (len(values)+len(reference[pmid])-count)
                containment = count / len(reference[pmid])
                if jaccard >= .8 or containment >= .9:
                    matches.append({'pmid':pmid,'shared':count,'jaccard':jaccard,'containment':containment})
            doi = (row.get('doi') or '').strip().casefold()
            screen = {'pmcid':row['pmcid'],'benchmark_context_matches':matches,
                      'duplicate_doi_of':doi_seen.get(doi) if doi else None,
                      'duplicate_body_of':text_seen.get(digest) if body else None,
                      'normalized_body_sha256':digest,'training_eligibility':'unreviewed',
                      'structural_review_flags': [name for name,flag in {
                          'not_research_article':row.get('article_type')!='research-article',
                          'language_unconfirmed':row.get('xml_lang')!='en',
                          'short_body':row.get('body_words',0)<500}.items() if flag]}
            if doi:
                doi_seen.setdefault(doi,row['pmcid'])
            if body:
                text_seen.setdefault(digest,row['pmcid'])
            doc_handle.write(json.dumps(row | content)+'\n')
            screen_handle.write(json.dumps(screen)+'\n')
    screening = read_jsonl(screens)
    summary = {'planned_documents':len(plan),'documents':len(rows),'failed_documents':len(failed),
               'xml_bytes':bytes_used,'contract_sha256':sha(saved),
               'body_words':sum(r.get('body_words',0) for r in rows),
               'article_types':dict(Counter(r.get('article_type') for r in rows)),
               'languages':dict(Counter(str(r.get('xml_lang')) for r in rows)),
               'benchmark_context_flagged':sum(bool(r.get('benchmark_context_matches')) for r in screening),
               'duplicate_doi':sum(bool(r.get('duplicate_doi_of')) for r in screening),
               'duplicate_body':sum(bool(r.get('duplicate_body_of')) for r in screening),
               'note':'Quality corpus only; topical centrality and empirical human study scope still require review.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__ == '__main__':
    run()
