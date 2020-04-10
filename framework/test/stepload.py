from dataclasses import dataclass


@dataclass
class StepLoad:
    enabled: bool = False
    duration: int = 0
    clients: int = 0


