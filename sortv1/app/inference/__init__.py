from typing import Protocol

from app.contracts import Frame, Prediction


class Inference(Protocol):
    """Contrato común de inferencia, implementado por OnnxInference."""

    def predict(self, frame: Frame) -> Prediction: ...
