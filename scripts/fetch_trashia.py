"""Inspect/download TrashIA with official SDK, or import a reproducible local ZIP."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sortv1"))
from app.utils import sha256, write_json

METADATA = ROOT / "sortv1/training/datasets/roboflow"

def initial_metadata():
    metadata = json.loads((METADATA / "public_metadata.json").read_text(encoding="utf-8"))
    metadata.update(url="https://universe.roboflow.com/trashia/trashia",
                    metadata_access="PUBLIC_METADATA_VERIFIED", inference_access="ACCESS_REQUIRED",
                    dataset_export_access="ACCESS_REQUIRED", dataset_downloaded=False,
                    class_mapping="PENDING_REVIEW")
    return metadata

def download_export(selected, key, model_format, destination):
    """Official export API, hashed archive and bounded safe extraction; URL stays in memory."""
    from roboflow.adapters import rfapi
    info = rfapi.get_version_export(key, "trashia", "trashia", selected.version, model_format)
    if info.get("ready") is False:
        raise ValueError("Export generating; retry later")
    link = info["export"]["link"]
    if not isinstance(link, str) or not link.startswith("https://"):
        raise ValueError("HTTPS export required")
    cache = ROOT / "datasets-cache"
    cache.mkdir(exist_ok=True)
    archive = cache / f"trashia-v{selected.version}-{model_format}-{time.time_ns()}.zip"
    try:
        with urllib.request.urlopen(link, timeout=60) as response, archive.open("xb") as output:
            count = 0
            while chunk := response.read(1024**2):
                count += len(chunk)
                if count > 4 * 1024**3: raise ValueError("Export exceeds 4 GiB")
                output.write(chunk)
        digest = sha256(archive)
        safe_extract(archive, destination)
    except Exception:
        archive.unlink(missing_ok=True)
        raise
    # ZIP contents are third-party input; refuse credential text before publishing a manifest.
    for path in destination.rglob("*"):
        if path.is_file() and key.encode() in path.read_bytes():
            raise ValueError("Credential content in external file")
    return digest

def safe_extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as handle:
        total = 0
        for item in handle.infolist():
            target = (destination / item.filename).resolve()
            if not target.is_relative_to(destination) or item.filename.startswith(("/", "\\")):
                raise ValueError("Unsafe ZIP path")
            if (item.external_attr >> 16) & 0o170000 == 0o120000: raise ValueError("ZIP links not allowed")
            total += item.file_size
            if total > 10 * 1024**3 or item.file_size > 100 * 1024**2: raise ValueError("ZIP too large")
        handle.extractall(destination)

def publish_metadata(metadata: dict, destination: Path | None) -> None:
    write_json(METADATA / "trashia_metadata.json", metadata)
    license_text = metadata.get("license")
    attribution = ("# TrashIA attribution\n\nSource: https://universe.roboflow.com/trashia/trashia\n\n"
                   f"Verification: {metadata['status']}\n\nLicense: {license_text or 'NOT_VERIFIED — download/use blocked'}\n\n"
                   f"Pinned version: {metadata.get('selected_version')}\n")
    METADATA.mkdir(parents=True, exist_ok=True)
    (METADATA / "ATTRIBUTION.md").write_text(attribution, encoding="utf-8")
    files = [] if destination is None else [{"path": str(p.relative_to(destination)), "sha256": sha256(p),
                                            "bytes": p.stat().st_size} for p in sorted(destination.rglob("*")) if p.is_file()]
    write_json(METADATA / "source_manifest.json", {"workspace": "trashia", "project": "trashia",
               "version": metadata.get("selected_version"), "source": "EXTERNAL", "files": files,
               "status": metadata["status"], "export_sha256": metadata.get("export_sha256")})
    if metadata.get("classes"):
        import yaml
        mapping = ROOT / "sortv1/training/datasets/class_mapping.yaml"
        current = yaml.safe_load(mapping.read_text()) if mapping.exists() else {"default": "CHALLENGE_OOD", "classes": {}}
        current["status"] = "PENDING_REVIEW"
        for name in metadata["classes"]:
            current.setdefault("classes", {}).setdefault(str(name), {"source_class_id": None, "source_class_name": str(name),
                "semantic_meaning": "UNKNOWN", "verification_source": "ROBOFLOW_METADATA",
                "verification_confidence": "PENDING_REVIEW", "target": "CHALLENGE_OOD",
                "reason": "Numeric or ambiguous name; material semantics not verified", "reviewed": False})
        mapping.write_text(yaml.safe_dump(current, sort_keys=True, allow_unicode=True), encoding="utf-8")
        report = ROOT / "docs/ml/TRASHIA_MAPPING_REPORT.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# TrashIA class mapping\n\nPublic metadata is verified separately from API/export access. "
                          "See [metadata](../../sortv1/training/datasets/roboflow/trashia_metadata.json) and "
                          "[public sources](../../sortv1/training/datasets/roboflow/public_metadata.json). "
                          "Hosted inference is research only; final SorTV1 uses local MobileNetV3/ONNX.\n\n"
                          + "| source_class | meaning_verified | target | reason | reviewed | evidence |\n| --- | --- | --- | --- | --- | --- |\n"
                          + "\n".join(f"| {n} | {current['classes'][str(n)].get('semantic_meaning', 'UNKNOWN')} | {current['classes'][str(n)]['target']} | {current['classes'][str(n)]['reason']} | {current['classes'][str(n)].get('reviewed', False)} | {current['classes'][str(n)].get('verification_source', 'PENDING_REVIEW')} |" for n in metadata["classes"])
                          + "\n\nNumeric class names are not material labels or verified annotation IDs. External splits are train_external/challenge, never final LOCAL_PHYSICAL validation/test. No accuracy or physical acceptance is claimed.\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", type=int); parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument("--import-zip", type=Path); parser.add_argument("--metadata", type=Path)
    parser.add_argument("--format", default="coco")
    args = parser.parse_args()
    metadata = initial_metadata()
    destination = None
    if args.import_zip:
        if args.metadata is None: parser.error("ZIP import requires --metadata from the actual export/project")
        supplied = json.loads(args.metadata.read_text(encoding="utf-8"))
        for field in ("task_type", "classes", "versions", "selected_version", "license", "images", "splits", "preprocessing"):
            metadata[field] = supplied.get(field)
        if (not metadata["license"] or not metadata["classes"] or not metadata["task_type"]
                or type(metadata["selected_version"]) is not int):
            parser.error("Actual version, classes, task type and licence must be provided")
        if args.version is not None and args.version != metadata["selected_version"]: parser.error("Version mismatch")
        metadata.update(status="DATASET_DOWNLOADED", metadata_access="MANUAL_EXPORT_VERIFIED",
                        dataset_export_access="DATASET_EXPORT_VERIFIED", dataset_downloaded=True,
                        export_sha256=sha256(args.import_zip))
        destination = ROOT / "sortv1/training/datasets/external/trashia" / str(metadata["selected_version"])
        if destination.exists(): parser.error("Destination exists; refusing to overwrite a pinned export")
        safe_extract(args.import_zip, destination)
    else:
        key = os.environ.get("ROBOFLOW_API_KEY")
        if not key:
            metadata["error"] = "ROBOFLOW_API_KEY_REQUIRED; public metadata preserved; inference/export not verified"
            publish_metadata(metadata, None); print(metadata["error"]); return 2
        try:
            from roboflow import Roboflow
            from roboflow.adapters import rfapi
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                project = Roboflow(api_key=key).workspace("trashia").project("trashia")
                versions = project.versions()
            # Use official SDK authentication for project metadata/licence too.
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                raw = rfapi.get_project(key, "trashia", "trashia")
            raw_project = raw.get("project", raw)
            metadata.update(status="METADATA_ACCESS_VERIFIED", metadata_access="METADATA_ACCESS_VERIFIED", task_type=project.type, classes=list(project.classes),
                            versions=[int(v.version) for v in versions], images=project.images,
                            splits=project.splits, license=raw_project.get("license") or metadata["license"])
            if args.version is not None:
                if args.version not in metadata["versions"]: raise ValueError("Requested version not available")
                selected = next(v for v in versions if int(v.version) == args.version)
                metadata.update(selected_version=args.version, preprocessing=selected.preprocessing,
                                augmentation=selected.augmentation, images=selected.images, splits=selected.splits)
                if not args.inspect_only:
                    if not metadata["license"]: raise ValueError("Licence not verified: download blocked")
                    destination = ROOT / "sortv1/training/datasets/external/trashia" / str(args.version)
                    if destination.exists(): raise ValueError("Pinned export already exists")
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        digest = download_export(selected, key, args.format, destination)
                    metadata.update(status="DATASET_DOWNLOADED", dataset_export_access="DATASET_EXPORT_VERIFIED",
                                    dataset_downloaded=True, export_sha256=digest)
            elif not args.inspect_only:
                metadata["status"] = "VERSION_SELECTION_REQUIRED"
        except Exception as error:
            # SDK errors can contain signed URLs/API keys. Never print exception details.
            metadata.update(status="API_OR_EXPORT_ACCESS_REQUIRED", error=type(error).__name__)
            publish_metadata(metadata, None); print("Inspection failed; see metadata status. No credentials logged."); return 2
    publish_metadata(metadata, destination)
    print(json.dumps({k: metadata[k] for k in ["status", "versions", "selected_version", "task_type", "classes", "license"]}))
    return 0 if metadata["status"] != "VERSION_SELECTION_REQUIRED" else 2

if __name__ == "__main__": raise SystemExit(main())
