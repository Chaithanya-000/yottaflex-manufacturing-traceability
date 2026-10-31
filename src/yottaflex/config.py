from dataclasses import dataclass

@dataclass(frozen=True)
class GenerationConfig:
    seed: int = 20261022
    products: int = 200
    suppliers: int = 50
    material_lots: int = 2000
    production_orders: int = 5000
    inspection_results: int = 20000
    machines: int = 40
    process_steps: int = 8
    defects_rate: float = 0.035
