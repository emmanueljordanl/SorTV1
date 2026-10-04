from typing import Protocol

from app.contracts import Cycle, Frame


class Capture(Protocol):
    """Debe devolver una captura RGB nueva ligada al ciclo, en reloj de la Pi."""

    def capture(self, cycle: Cycle) -> Frame: ...
