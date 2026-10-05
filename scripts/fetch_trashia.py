"""Inspect/download TrashIA with official SDK, or import a reproducible local ZIP."""
import argparse
import contextlib
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import sys
import time
import re
from urllib.parse import urlsplit
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sortv1"))
from app.utils import sha256, write_json

METADATA = ROOT / "sortv1/training/datasets/roboflow"

VERIFIED = {"PUBLIC_METADATA_VERIFIED", "METADATA_ACCESS_VERIFIED", "MANUAL_EXPORT_VERIFIED",
            "DATASET_EXPORT_VERIFIED", "DATASET_DOWNLOADED", "REINDEXED_EXISTING_DATASET"}
STATE_FIELDS = {"status", "selected_version", "task_type", "license", "classes", "class_ids", "versions",
                "images", "project_images", "splits", "preprocessing", "augmentation", "metadata_access",
                "inference_access", "dataset_export_access", "dataset_downloaded", "export_sha256",
                "class_mapping", "index_status", "export_sha256_source"}
INSPECTION_STATE_FIELDS = {"selected_version", "dataset_downloaded", "dataset_export_access",
                           "export_sha256", "metadata_access"}
SUMMARY_FIELDS = {"workspace", "project", "version", "source", "status", "dataset_downloaded",
                  "file_count", "total_bytes", "full_manifest_sha256", "export_sha256", "index_status",
                  "generated_from", "full_manifest_path"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def sanitized(value):
    """Only data/provenance may be persisted; SDK headers and signed links are not metadata."""
    if isinstance(value, dict):
        return {key: sanitized(item) for key, item in value.items()
                if str(key).lower() not in {"api_key", "roboflow_api_key", "authorization", "headers",
                                            "signed_url", "signed_urls", "access_token", "token"}}
    if isinstance(value, list):
        return [sanitized(item) for item in value]
    if isinstance(value, str):
        secret = os.environ.get("ROBOFLOW_API_KEY")
        if (secret and secret in value) or "bearer " in value.lower():
            raise ValueError("Credential content refused")
        if "://" in value and (urlsplit(value).query or urlsplit(value).fragment):
            raise ValueError("Signed or parameterized URL refused")
    return value


def same_version(record, version):
    return (record.get("workspace") == "trashia" and record.get("project") == "trashia"
            and type(version) is int and version > 0
            and record.get("selected_version", record.get("version")) == version)


def verified_record(record, version):
    return same_version(record, version) and (record.get("status") in VERIFIED
                                            or record.get("metadata_access") in VERIFIED)


def verified_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def previous_manifest(version):
    record = read_json(METADATA / "source_manifest.json")
    return sanitized(record) if verified_record(record, version) else {}


def initial_metadata(version=None):
    metadata = json.loads((METADATA / "public_metadata.json").read_text(encoding="utf-8"))
    metadata.update(url="https://universe.roboflow.com/trashia/trashia",
                    metadata_access="PUBLIC_METADATA_VERIFIED", inference_access="ACCESS_REQUIRED",
                    dataset_export_access="ACCESS_REQUIRED", dataset_downloaded=False,
                    class_mapping="PENDING_REVIEW")
    previous = read_json(METADATA / "trashia_metadata.json")
    selected = previous.get("selected_version") if version is None else version
    if verified_record(previous, selected):
        metadata.update(sanitized({k: v for k, v in previous.items() if k in STATE_FIELDS}))
        manifest = previous_manifest(selected)
        if not verified_hash(metadata.get("export_sha256")) and verified_hash(manifest.get("export_sha256")):
            metadata["export_sha256"] = manifest["export_sha256"]
        if manifest.get("dataset_downloaded") is True:
            metadata["dataset_downloaded"] = True
            if manifest.get("index_status"):
                metadata["index_status"] = manifest["index_status"]
        if metadata.get("dataset_downloaded") is True:
            metadata["status"] = "DATASET_DOWNLOADED"
    if not verified_hash(metadata.get("export_sha256")):
        metadata["export_sha256"] = None
    return sanitized(metadata)


def full_manifest_path(version):
    if type(version) is not int or version <= 0:
        raise ValueError("Explicit positive pinned version required")
    return ROOT / "datasets-cache/trashia-manifests" / f"source_manifest_v{version}_full.json"


def write_manifest_json(path, record):
    """Stable keys and LF bytes: identical inputs produce identical artifact hashes."""
    payload = (json.dumps(sanitized(record), indent=2, sort_keys=True, ensure_ascii=True,
                          allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def source_manifest_summary(metadata, previous, files=None):
    version = metadata.get("selected_version")
    summary = dict(workspace="trashia", project="trashia", version=version, source="EXTERNAL",
                   status=metadata.get("index_status", metadata["status"]),
                   dataset_downloaded=metadata.get("dataset_downloaded") is True,
                   file_count=0, total_bytes=0, full_manifest_sha256=None,
                   export_sha256=None, index_status=metadata.get("index_status", "NOT_INDEXED"),
                   generated_from="ROBOFLOW_METADATA")
    summary.update({k: v for k, v in previous.items() if k in SUMMARY_FIELDS})
    # Migrate a verified legacy tracked index without inspecting/downloading images.
    if files is None and previous.get("files"):
        files = previous["files"]
    if files is not None:
        entries = []
        for item in files:
            if (not isinstance(item.get("path"), str) or not verified_hash(item.get("sha256"))
                    or type(item.get("bytes")) is not int or item["bytes"] < 0):
                raise ValueError("Invalid per-file provenance")
            entries.append({"path": item["path"].replace("\\", "/"), "sha256": item["sha256"],
                            "bytes": item["bytes"]})
        entries.sort(key=lambda item: item["path"])
        full = dict(workspace="trashia", project="trashia", version=version, source="EXTERNAL", files=entries)
        artifact = full_manifest_path(version)
        write_manifest_json(artifact, full)
        summary.update(file_count=len(entries), total_bytes=sum(item["bytes"] for item in entries),
                       full_manifest_sha256=sha256(artifact),
                       full_manifest_path=artifact.relative_to(ROOT).as_posix(),
                       generated_from=f"sortv1/training/datasets/external/trashia/{version}")
        if summary["index_status"] == "NOT_INDEXED":
            summary["index_status"] = "INDEXED_DATASET"
    summary["dataset_downloaded"] = (summary["dataset_downloaded"] is True
                                      or metadata.get("dataset_downloaded") is True)
    if verified_hash(metadata.get("export_sha256")):
        summary["export_sha256"] = metadata["export_sha256"]
    elif not verified_hash(summary["export_sha256"]):
        summary["export_sha256"] = None
    return sanitized(summary)


def index_files(destination):
    destination = destination.resolve()
    files = []
    for path in sorted(destination.rglob("*")):
        if path.is_symlink() or not path.resolve().is_relative_to(destination):
            raise ValueError("Dataset links/outside paths refused")
        if path.is_file():
            files.append({"path": path.relative_to(destination).as_posix(), "sha256": sha256(path),
                          "bytes": path.stat().st_size})
    return sanitized(files)


def recover_zip_hash(archive, files):
    """Explicit cache ZIP recovery: every payload must match the pinned on-disk index."""
    archive = archive.resolve()
    if not archive.is_relative_to((ROOT / "datasets-cache").resolve()) or not archive.is_file():
        raise ValueError("Original ZIP must exist in datasets-cache")
    expected = {item["path"]: item for item in files}
    with zipfile.ZipFile(archive) as handle:
        entries = [item for item in handle.infolist() if not item.is_dir()]
        if len(entries) != len(expected) or {item.filename for item in entries} != set(expected):
            raise ValueError("ZIP does not match pinned dataset files")
        for item in entries:
            if item.file_size != expected[item.filename]["bytes"]:
                raise ValueError("ZIP size mismatch")
            with handle.open(item) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != expected[item.filename]["sha256"]:
                raise ValueError("ZIP payload hash mismatch")
    return sha256(archive)


def reindex_existing(version, export_zip=None):
    if type(version) is not int or version <= 0:
        raise ValueError("Explicit positive pinned version required")
    destination = ROOT / "sortv1/training/datasets/external/trashia" / str(version)
    if not destination.is_dir() or destination.is_symlink():
        raise ValueError("Pinned dataset directory does not exist")
    metadata = initial_metadata(version)
    if not same_version(metadata, version) or not all(metadata.get(k) for k in ("task_type", "license", "classes")):
        raise ValueError("Verified metadata for the pinned version required")
    files = index_files(destination)
    if not files:
        raise ValueError("Pinned dataset is empty")
    if export_zip is not None:
        digest = recover_zip_hash(export_zip, files)
        if verified_hash(metadata.get("export_sha256")) and metadata["export_sha256"].lower() != digest:
            raise ValueError("Original export SHA conflicts with verified provenance")
        metadata.update(export_sha256=digest, export_sha256_source="VERIFIED_CACHE_ZIP")
    metadata.update(status="DATASET_DOWNLOADED", dataset_downloaded=True,
                    index_status="REINDEXED_EXISTING_DATASET")
    publish_metadata(metadata, destination, files=files)
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

def publish_metadata(metadata: dict, destination: Path | None, *, files=None) -> None:
    metadata = sanitized(metadata)
    # Inspection preserves the summary even if the local cache artifact is absent.
    previous = previous_manifest(metadata.get("selected_version"))
    if destination is not None:
        manifest = source_manifest_summary(metadata, {}, index_files(destination) if files is None else files)
    else:
        manifest = source_manifest_summary(metadata, previous)
    mapping = ROOT / "sortv1/training/datasets/class_mapping.yaml"
    if mapping.is_file() and metadata.get("classes"):
        import yaml
        current = yaml.safe_load(mapping.read_text())
        if all(current.get("classes", {}).get(str(name), {}).get("reviewed") is True for name in metadata["classes"]):
            metadata["class_mapping"] = current.get("status", "REVIEWED")
    write_json(METADATA / "trashia_metadata.json", metadata)
    license_text = metadata.get("license")
    attribution = ("# TrashIA attribution\n\nSource: https://universe.roboflow.com/trashia/trashia\n\n"
                   f"Verification: {metadata['status']}\n\nLicense: {license_text or 'NOT_VERIFIED — download/use blocked'}\n\n"
                   f"Pinned version: {metadata.get('selected_version')}\n")
    METADATA.mkdir(parents=True, exist_ok=True)
    (METADATA / "ATTRIBUTION.md").write_text(attribution, encoding="utf-8")
    write_manifest_json(METADATA / "source_manifest.json", manifest)
    if metadata.get("classes"):
        import yaml
        mapping = ROOT / "sortv1/training/datasets/class_mapping.yaml"
        current = yaml.safe_load(mapping.read_text()) if mapping.exists() else {"default": "CHALLENGE_OOD", "classes": {}}
        changed = False
        for name in metadata["classes"]:
            if str(name) in current.setdefault("classes", {}):
                continue
            changed = True
            current["classes"][str(name)] = {"source_class_id": None, "source_class_name": str(name),
                "semantic_meaning": "UNKNOWN", "verification_source": "ROBOFLOW_METADATA",
                "verification_confidence": "PENDING_REVIEW", "target": "CHALLENGE_OOD",
                "reason": "Numeric or ambiguous name; material semantics not verified", "reviewed": False}
        if changed:
            current["status"] = "PENDING_REVIEW"
            mapping.write_text(yaml.safe_dump(current, sort_keys=True, allow_unicode=True), encoding="utf-8")
        # A human-reviewed report is not generated/overwritten by inspection or indexing.

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", type=int)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--inspect-only", action="store_true")
    modes.add_argument("--reindex-existing", action="store_true")
    modes.add_argument("--import-zip", type=Path)
    parser.add_argument("--metadata", type=Path); parser.add_argument("--export-zip", type=Path)
    parser.add_argument("--format", default="coco")
    args = parser.parse_args(argv)
    if args.export_zip and not args.reindex_existing: parser.error("--export-zip requires --reindex-existing")
    if args.reindex_existing:
        try:
            metadata = reindex_existing(args.version, args.export_zip)
        except (ValueError, OSError, zipfile.BadZipFile):
            print("REINDEX_FAILED; pinned files and verified metadata were not replaced")
            return 2
        print("REINDEXED_EXISTING_DATASET; DATASET_DOWNLOADED; version=" + str(args.version))
        return 0
    metadata = initial_metadata(None if args.inspect_only else args.version)
    original = dict(metadata)
    prior_verified = verified_record(read_json(METADATA / "trashia_metadata.json"),
                                     original.get("selected_version"))
    destination = None
    pinned = ROOT / "sortv1/training/datasets/external/trashia" / str(args.version or metadata.get("selected_version"))
    if not args.inspect_only and not args.import_zip and pinned.exists():
        print("PINNED_DATASET_EXISTS; no download/overwrite; use --reindex-existing to rebuild its index")
        return 2
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
            metadata["inspection_status"] = "API_ACCESS_REQUIRED"
            publish_metadata(metadata, None)
            print("ROBOFLOW_API_KEY_REQUIRED; verified metadata and existing index preserved")
            return 0 if args.inspect_only and metadata.get("dataset_downloaded") is True else 2
        try:
            previous_logging = logging.root.manager.disable
            logging.disable(logging.CRITICAL)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                from roboflow import Roboflow
                from roboflow.adapters import rfapi
                project = Roboflow(api_key=key).workspace("trashia").project("trashia")
                versions = project.versions()
            # Use official SDK authentication for project metadata/licence too.
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                raw = rfapi.get_project(key, "trashia", "trashia")
            raw_project = raw.get("project", raw)
            inspected = sanitized(dict(task_type=project.type, classes=list(project.classes),
                            versions=[int(v.version) for v in versions], images=project.images,
                            splits=project.splits, license=raw_project.get("license") or metadata["license"]))
            metadata.update(inspected)
            if not original.get("dataset_downloaded"):
                metadata.update(status="METADATA_ACCESS_VERIFIED", metadata_access="METADATA_ACCESS_VERIFIED")
            if args.version is not None:
                if args.version not in metadata["versions"]: raise ValueError("Requested version not available")
                selected = next(v for v in versions if int(v.version) == args.version)
                metadata.update(sanitized(dict(selected_version=args.version, preprocessing=selected.preprocessing,
                                augmentation=selected.augmentation, images=selected.images, splits=selected.splits)))
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
        except Exception:
            # SDK errors can contain signed URLs/API keys. Never print exception details.
            metadata = original
            metadata["inspection_status"] = "API_OR_EXPORT_ACCESS_REQUIRED"
            publish_metadata(metadata, None); print("Inspection failed; see metadata status. No credentials logged."); return 2
        finally:
            logging.disable(previous_logging)
    if args.inspect_only:
        # Inspecting another API version cannot replace provenance of the local pinned export.
        preserved = STATE_FIELDS if original.get("dataset_downloaded") is True else INSPECTION_STATE_FIELDS
        if prior_verified:
            for field in preserved:
                if field in original: metadata[field] = original[field]
                else: metadata.pop(field, None)
        if original.get("dataset_downloaded") is True: metadata["status"] = "DATASET_DOWNLOADED"
        metadata["inspection_status"] = "METADATA_ACCESS_VERIFIED"
    publish_metadata(metadata, destination)
    print(json.dumps({k: metadata[k] for k in ["status", "versions", "selected_version", "task_type", "classes", "license"]}))
    return 0 if metadata["status"] != "VERSION_SELECTION_REQUIRED" else 2

if __name__ == "__main__": raise SystemExit(main())
