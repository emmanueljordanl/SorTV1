import argparse
import json
import time
from pathlib import Path
from uuid import uuid4
from PIL import Image
from app.capture.picamera2_capture import PicameraCapture
from app.contracts import Cycle
from app.utils import sha256, load_json, write_json
from training.datasets.validate import read_rows, write_rows, validate_manifest

def main():
    p = argparse.ArgumentParser(); p.add_argument("--object-id", required=True); p.add_argument("--session-id", required=True)
    p.add_argument("--class-id", choices=list(map(str, range(4))), required=True)
    p.add_argument("--split", choices=["train", "validation", "test", "challenge"], required=True)
    p.add_argument("--lighting-setup", required=True); p.add_argument("--operator", required=True)
    p.add_argument("--manifest", type=Path, default=Path("training/datasets/local/manifest.csv")); p.add_argument("--frames", type=int, default=3)
    a = p.parse_args(); rows = read_rows(a.manifest) if a.manifest.exists() else []
    if any(r["object_id"] == a.object_id and (r["split"] != a.split or r["class_id"] != a.class_id) for r in rows): p.error("Object already assigned to another split/class")
    config = load_json(Path("config/camera.json")); camera = PicameraCapture(config)
    try:
        cycle = Cycle(a.session_id, time.time_ns() & 0xFFFFFFFF); camera.begin(cycle)
        for _ in range(a.frames):
            frame = camera.capture(cycle); path = a.manifest.parent / a.split / (uuid4().hex+".png")
            path.parent.mkdir(parents=True, exist_ok=True); Image.fromarray(frame.rgb).save(path)
            write_json(path.with_suffix(".json"), {"controls": frame.controls, "frame_id": frame.frame_id, "captured_ns": frame.captured_ns, "camera_config": config})
            rows.append(dict(object_id=a.object_id, session_id=a.session_id, class_id=a.class_id, split=a.split,
                             image_path=str(path.resolve()), source="LOCAL_PHYSICAL", source_dataset="SorTV1_tray", source_version=a.session_id,
                             source_image_id=frame.frame_id, source_annotation_id="", original_class=a.class_id, lighting_setup=a.lighting_setup,
                             operator=a.operator, sha256=sha256(path), excluded_reason=""))
        write_rows(a.manifest, rows); validate_manifest(a.manifest, strict=True)
        print(json.dumps({"source": "LOCAL_PHYSICAL", "rows": len(rows)}))
    finally: camera.close()
if __name__ == "__main__": main()
