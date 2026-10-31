import argparse, hashlib, tempfile
from pathlib import Path
from .config import GenerationConfig
from .generator import build_dataset

def fingerprint(data):
    h=hashlib.sha256()
    for table in sorted(data):
        h.update(table.encode())
        for row in data[table]:
            h.update(repr(sorted(row.items())).encode())
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,default=20261022)
    a=p.parse_args()
    cfg=GenerationConfig(seed=a.seed)
    first=fingerprint(build_dataset(cfg))
    second=fingerprint(build_dataset(cfg))
    print({"seed":a.seed,"first":first,"second":second,"reproducible":first==second})
    if first!=second: raise SystemExit(1)
if __name__=="__main__": main()
