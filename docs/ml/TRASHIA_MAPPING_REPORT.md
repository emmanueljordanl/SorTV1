# TrashIA class mapping

Public metadata is verified separately from API/export access. See [metadata](../../sortv1/training/datasets/roboflow/trashia_metadata.json) and [public sources](../../sortv1/training/datasets/roboflow/public_metadata.json). Hosted inference is research only; final SorTV1 uses local MobileNetV3/ONNX.

| source_class | meaning_verified | target | reason | reviewed | evidence |
| --- | --- | --- | --- | --- | --- |
| 0 | UNKNOWN | CHALLENGE_OOD | Numeric or ambiguous name; material semantics not verified | False | ROBOFLOW_METADATA |
| 1 | UNKNOWN | CHALLENGE_OOD | Numeric or ambiguous name; material semantics not verified | False | ROBOFLOW_METADATA |
| 2 | UNKNOWN | CHALLENGE_OOD | Numeric or ambiguous name; material semantics not verified | False | ROBOFLOW_METADATA |
| 3 | UNKNOWN | CHALLENGE_OOD | Numeric or ambiguous name; material semantics not verified | False | ROBOFLOW_METADATA |
| 4 | UNKNOWN | CHALLENGE_OOD | Numeric or ambiguous name; material semantics not verified | False | ROBOFLOW_METADATA |
| 5 | UNKNOWN | CHALLENGE_OOD | Numeric or ambiguous name; material semantics not verified | False | ROBOFLOW_METADATA |

Numeric class names are not material labels or verified annotation IDs. External splits are train_external/challenge, never final LOCAL_PHYSICAL validation/test. No accuracy or physical acceptance is claimed.
