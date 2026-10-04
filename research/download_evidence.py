"""Download public primary evidence and verify the pinned annotation release.

No provider credentials, web scraping service, or proprietary source are used.
Use --output-dir outside iCloud if desired; HTML snapshots remain local.
"""
from __future__ import annotations
import argparse, hashlib, json, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def download(output: Path) -> dict:
    output.mkdir(parents=True,exist_ok=True)
    targets=json.loads((ROOT/'research/evidence/dng02_targets.json').read_text())
    sources=[('flywire-neuron-annotations-v2.1.0.tsv',targets['annotation_url'],targets['annotation_sha256']),
             ('namiki-dng02-paper.html','https://pmc.ncbi.nlm.nih.gov/articles/PMC9206711/',None),
             ('shiu-brain-model-paper.html','https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/',None)]
    result={}
    for filename,url,expected in sources:
        path=output/filename
        if not path.exists():
            request=urllib.request.Request(url,headers={'User-Agent':'FlyBrainLab/1.0 public-research-reproduction'})
            with urllib.request.urlopen(request,timeout=90) as response:
                content=response.read(40*1024*1024+1)
            if len(content)>40*1024*1024: raise ValueError('Source exceeds40MiB bound')
            actual=hashlib.sha256(content).hexdigest()
            if expected and actual!=expected: raise ValueError('Pinned annotation hash mismatch')
            path.write_bytes(content)
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if expected and actual!=expected: raise ValueError('Existing annotation hash mismatch')
        result[filename]={'url':url,'sha256':actual,'path':str(path),'pin_verified':expected is not None}
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(download(args.output_dir),indent=2))
