import argparse
import json
import hashlib
from collections import Counter
from pathlib import Path
from training.datasets.validate import validate_manifest, read_rows, write_rows
from app.utils import sha256, write_json

def prepare(manifests: list[Path], output: Path, *, allow_auxiliary_only: bool = False) -> dict:
    rows = []
    for manifest in manifests:
        validate_manifest(manifest, strict=True)
        for row in read_rows(manifest):
            image = Path(row["image_path"])
            row["image_path"] = str(image if image.is_absolute() else (manifest.parent / image).resolve())
            if row["source"] == "EXTERNAL" and row["split"] not in {"challenge", "train_external"}: row["split"] = "train_external"
            rows.append(row)
    test_rows = sorted([r for r in rows if r["split"] == "test"], key=lambda r: (r["object_id"], r["sha256"]))
    freeze_path = output.with_suffix(".test-freeze.json")
    digest = hashlib.sha256(json.dumps(test_rows, sort_keys=True).encode()).hexdigest()
    if freeze_path.exists() and json.loads(freeze_path.read_text())["test_manifest_sha256"] != digest:
        raise ValueError("Frozen TEST changed; create a new manifest/version explicitly")
    temporary = output.with_suffix(".validation.csv")
    write_rows(temporary, rows)
    try: validate_manifest(temporary, strict=True, require_local_eval=not allow_auxiliary_only)
    finally: temporary.unlink(missing_ok=True)
    write_rows(output, rows)
    report = {"manifest_sha256": sha256(output), "rows": len(rows),
              "counts": dict(Counter(f"{r['source']}:{r['split']}:{r['class_id']}" for r in rows)),
              "status": "PREPARED", "final_evaluation_domain": "LOCAL_PHYSICAL"}
    write_json(output.with_suffix(".report.json"), report)
    write_json(freeze_path, {"test_manifest_sha256": digest})
    return report

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("training/datasets/prepared.csv"))
    parser.add_argument("--auxiliary-only", action="store_true")
    args = parser.parse_args(); print(json.dumps(prepare(args.manifest, args.output, allow_auxiliary_only=args.auxiliary_only)))
if __name__ == "__main__": main()
