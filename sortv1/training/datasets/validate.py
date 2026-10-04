import argparse
import csv
from pathlib import Path

FIELDS = {"object_id", "session_id", "class_id", "split", "image_path", "source",
          "lighting_setup", "operator", "excluded_reason"}


def validate_manifest(path: Path) -> int:
    objects: dict[str, tuple[str, str]] = {}
    images: set[str] = set()
    count = 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not FIELDS.issubset(reader.fieldnames or []):
            raise ValueError("Faltan columnas obligatorias del manifest")
        for row in reader:
            if not row["object_id"] or row["split"] not in {"train", "validation", "test", "challenge"}:
                raise ValueError("Objeto o partición inválidos")
            if row["class_id"] not in {"0", "1", "2", "3"} and row["split"] != "challenge":
                raise ValueError("Clase fuera de catálogo")
            identity = row["split"], row["class_id"]
            if row["object_id"] in objects and objects[row["object_id"]] != identity:
                raise ValueError(f"Fuga de partición o etiqueta: {row['object_id']}")
            objects[row["object_id"]] = identity
            if not row["image_path"] or row["image_path"] in images:
                raise ValueError("Imagen vacía o duplicada")
            images.add(row["image_path"])
            count += 1
    if not count:
        raise ValueError("Manifest vacío: aún no existen datos reales")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validar etiquetas y detectar fuga por objeto")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        print(f"Manifest válido: {validate_manifest(args.manifest)} imágenes")
    except ValueError as exc:
        parser.exit(1, f"ERROR: {exc}\n")
