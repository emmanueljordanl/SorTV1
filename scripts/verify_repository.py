"""Verifica estructura, metadatos y archivos realmente versionados."""
import csv
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    "app": "capture quality inference decision transport controller evidence",
    "firmware": "state_machine drivers protocol config",
    "training": "datasets train evaluate export",
    "tests": "unit protocol integration fault_injection acceptance",
    "hardware": "electrical wiring pinout cad bom",
    "docs": "architecture adr procedures risks",
    "evidence": "benchmarks experiments acceptance photos",
}


def verify() -> None:
    for parent, children in MODULES.items():
        for child in children.split():
            path = ROOT / "sortv1" / parent / child
            if not path.is_dir() or not (path / "README.md").is_file():
                raise ValueError(f"Módulo ausente o sin documentación: {parent}/{child}")
    for parent in ("config", "models"):
        if not (ROOT / "sortv1" / parent / "README.md").is_file():
            raise ValueError(f"Falta {parent}")
    for path in (ROOT / "sortv1").rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    labels = json.loads((ROOT / "sortv1/config/labels.json").read_text())
    manifest = json.loads((ROOT / "sortv1/models/model_manifest.json").read_text())
    if labels != manifest["labels"]:
        raise ValueError("Orden de labels incompatible con el manifiesto del modelo")
    with (ROOT / "sortv1/hardware/bom/bom.csv").open(newline="", encoding="utf-8") as handle:
        total = sum(int(row["planned_mxn"]) for row in csv.DictReader(handle))
    if total != 9902:
        raise ValueError("La BOM inicial no coincide con el presupuesto fuente")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    for name in filter(None, tracked):
        path = Path(name)
        if "node_modules" in path.parts or "__pycache__" in path.parts or path.suffix == ".pyc":
            raise ValueError(f"Dependencia o caché versionada: {name}")
        if path.name == ".env" or path.name.startswith(".env.") and path.name != ".env.example":
            raise ValueError(f"Archivo de entorno local versionado: {name}")
        if (ROOT / name).stat().st_size >= 50 * 1024 * 1024:
            raise ValueError(f"Archivo requiere acordar almacenamiento para binarios grandes: {name}")
    print("OK: arquitectura, JSON, labels, BOM y archivos versionados")


if __name__ == "__main__":
    verify()
