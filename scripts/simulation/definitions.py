from typing import Dict, List
from dataclasses import dataclass
from simulation.units import AmountUnit, TimeUnit

@dataclass
class DosingEvent:
    type: str
    target: str
    amount: float
    time: float
    duration: float | None = None
    interval: float | None = None
    until: float | None = None

@dataclass
class Comparison:
    id: str
    label: str
    output: str

@dataclass
class Scenario:
    id: str
    label: str
    duration: int
    evaluation_resolution: int
    dosing_events: List[DosingEvent]
    comparisons: List[Comparison]
    time_unit: TimeUnit
    amount_unit: AmountUnit

@dataclass
class ModelInstance:
    id: str
    label: str
    model_path: str
    param_file: str
    target_mappings: Dict[str, str]

@dataclass
class SimulationConfig:
    id: str
    label: str
    scenarios: List[Scenario]
    model_instances: List[ModelInstance]
