from yottaflex.config import GenerationConfig
from yottaflex.generator import build_dataset
from yottaflex.reproducibility import fingerprint

def test_same_seed_is_reproducible():
    cfg=GenerationConfig(products=10,suppliers=5,material_lots=30,production_orders=20,inspection_results=80)
    assert fingerprint(build_dataset(cfg)) == fingerprint(build_dataset(cfg))

def test_required_baseline_counts():
    cfg=GenerationConfig(products=200,suppliers=50,material_lots=2000,production_orders=5000,inspection_results=20000)
    data=build_dataset(cfg)
    assert len(data["products"])==200
    assert len(data["suppliers"])==50
    assert len(data["material_lots"])==2000
    assert len(data["production_orders"])==5000
    assert len(data["inspection_results"])==20000
    assert len(data["anomalies"])==5
