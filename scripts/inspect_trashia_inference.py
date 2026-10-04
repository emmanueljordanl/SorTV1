"""Research-only hosted inspection; never imported by the edge sorter."""
import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path

MODEL_ID = "trashia/1"


def sanitized_response(response, secret):
    """Allow only the detection contract; discard URLs, headers and unknown fields."""
    if not isinstance(response, dict):
        raise ValueError("Unexpected response contract")
    clean = {"predictions": []}
    for item in response.get("predictions", []):
        prediction = {}
        for key in ("x", "y", "width", "height", "confidence", "class_id"):
            value = item.get(key)
            if type(value) in (int, float) and math.isfinite(value):
                prediction[key] = value
        for key in ("class", "class_name"):
            value = item.get(key)
            if isinstance(value, str) and len(value) <= 128:
                if secret in value or "://" in value or "bearer " in value.lower():
                    raise ValueError("Unsafe class text")
                prediction[key] = value
        clean["predictions"].append(prediction)
    image = response.get("image", {})
    clean["image"] = {k: image[k] for k in ("width", "height")
                      if type(image.get(k)) is int and image[k] > 0}
    if secret in json.dumps(clean):
        raise ValueError("Unsafe response")
    return clean


def inspect_image(image, output):
    secret = os.environ.get("ROBOFLOW_API_KEY")
    if not secret:
        raise ValueError("ROBOFLOW_API_KEY_REQUIRED")
    if not image.is_file() or image.stat().st_size > 20 * 1024**2:
        raise ValueError("Local image required, maximum 20 MiB")
    from inference_sdk import InferenceConfiguration, InferenceHTTPClient
    # No request/response logging or raw exceptions: SDK messages can contain secrets.
    previous_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            client = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=secret)
            client.configure(InferenceConfiguration(api_key_transport="header", disable_active_learning=True))
            response = client.infer(str(image), model_id=MODEL_ID)
    finally:
        logging.disable(previous_logging)
    record = dict(source="ROBOFLOW_HOSTED_INFERENCE", status="INFERENCE_ACCESS_VERIFIED",
                  model_id=MODEL_ID, timestamp=datetime.now(timezone.utc).isoformat(),
                  image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                  software_version=importlib.metadata.version("inference-sdk"),
                  response=sanitized_response(response, secret),
                  physical_acceptance=False, sortv1_accuracy=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        inspect_image(args.image, args.output)
    except Exception:
        print("INFERENCE_ACCESS_REQUIRED_OR_REQUEST_FAILED; no credentials or exception details logged")
        return 2
    print("INFERENCE_ACCESS_VERIFIED; sanitized research response saved; not physical acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
