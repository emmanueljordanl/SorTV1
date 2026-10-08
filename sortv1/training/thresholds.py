"""A frozen VALIDATION selection is carried unchanged into TEST and export."""
import json
import math
from pathlib import Path
from app.utils import sha256

KEYS = ("top1_min_exclusive", "margin_min_exclusive", "frames_required", "consensus_required")

def selection(top1, margin, checkpoint, manifest, *, status="VALIDATION_SELECTED", source="LOCAL_PHYSICAL"):
    return dict(schema=1, status=status, split="validation", source=source,
                checkpoint_sha256=sha256(checkpoint), dataset_manifest_sha256=sha256(manifest),
                top1_min_exclusive=top1, margin_min_exclusive=margin, frames_required=3, consensus_required=2)

def load_selection(path, checkpoint, manifest, *, technical_smoke=False):
    value=json.loads(Path(path).read_text())
    allowed={"VALIDATION_SELECTED"} | ({"TECHNICAL_FIXTURE"} if technical_smoke else set())
    if value.get("schema") != 1 or value.get("status") not in allowed or value.get("split") != "validation":
        raise ValueError("Require a frozen successful VALIDATION selection")
    if not technical_smoke and value.get("source") != "LOCAL_PHYSICAL":
        raise ValueError("Production selection requires LOCAL_PHYSICAL")
    for key, file in (("checkpoint_sha256",checkpoint),("dataset_manifest_sha256",manifest)):
        if value.get(key) != sha256(file): raise ValueError("Threshold selection binding changed: "+key)
    for key in KEYS[:2]:
        number=value.get(key)
        if isinstance(number,bool) or not isinstance(number,(int,float)) or not math.isfinite(number) or not 0 <= number < 1:
            raise ValueError("Invalid selected threshold: "+key)
    if value.get("frames_required") != 3 or value.get("consensus_required") != 2:
        raise ValueError("SorTV1 requires three frames and consensus of two")
    return value

def runtime_values(value):
    return {key:value[key] for key in KEYS}

def copy_selected(path, checkpoint, manifest, output, *, technical_smoke=False):
    value=load_selection(path,checkpoint,manifest,technical_smoke=technical_smoke)
    # Byte-for-byte provenance as well as a minimal runtime contract.
    output=Path(output)
    (output/"threshold_selection.json").write_bytes(Path(path).read_bytes())
    (output/"thresholds.json").write_text(json.dumps(runtime_values(value),indent=2)+"\n")
    return {name:sha256(output/name) for name in ("threshold_selection.json","thresholds.json")}
