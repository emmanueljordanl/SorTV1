from dataclasses import dataclass
from enum import Enum
from typing import Any

LABELS = ("PET", "PAPEL_CARTON", "METAL_LATAS", "OTRO_SECO_CONOCIDO")


@dataclass(frozen=True)
class Cycle:
    boot: str
    number: int

    @property
    def key(self) -> str:
        return f"{self.boot}:{self.number}"


@dataclass(frozen=True)
class Frame:
    frame_id: str
    cycle: Cycle
    captured_ns: int  # Reloj monótono de la Pi, también en la simulación.
    rgb: Any
    controls: dict[str, Any]


@dataclass(frozen=True)
class QualityResult:
    valid: bool
    reason: str
    age_ms: float


@dataclass(frozen=True)
class Prediction:
    frame_id: str
    probabilities: tuple[float, float, float, float]
    model_sha256: str
    inference_ms: float


class DecisionKind(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "RECHAZO"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class Decision:
    kind: DecisionKind
    destination: int | None
    predicted_class: str | None
    reason: str
