import argparse
from pathlib import Path
from .config import GenerationConfig
from .generator import build_dataset, export_dataset

def main():
    p = argparse.ArgumentParser(description="Generate deterministic YottaFlex synthetic data")
    p.add_argument("--seed", type=int, default=20261022)
    p.add_argument("--output", default="data/generated")
    p.add_argument("--scale", type=float, default=1.0, help="Scale all baseline volumes (0 < scale <= 1 for quick runs)")
    a = p.parse_args()
    if not 0 < a.scale <= 1: p.error("--scale must be > 0 and <= 1")
    base = GenerationConfig()
    cfg = GenerationConfig(seed=a.seed, products=max(1,int(base.products*a.scale)),
        suppliers=max(1,int(base.suppliers*a.scale)), material_lots=max(1,int(base.material_lots*a.scale)),
        production_orders=max(1,int(base.production_orders*a.scale)),
        inspection_results=max(1,int(base.inspection_results*a.scale)),
        machines=base.machines, process_steps=base.process_steps, defects_rate=base.defects_rate)
    data = build_dataset(cfg)
    export_dataset(data, Path(a.output))
    import json
    summary = {"seed":a.seed,"record_counts":{k:len(v) for k,v in data.items()}}
    Path(a.output,"validation_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__ == "__main__": main()
