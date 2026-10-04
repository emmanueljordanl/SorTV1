from typing import Protocol

from app.contracts import Frame, Prediction


class Inference(Protocol):
    """Adaptador futuro de ONNX Runtime; nunca se sustituye por predicción manual."""

    def predict(self, frame: Frame) -> Prediction: ...
