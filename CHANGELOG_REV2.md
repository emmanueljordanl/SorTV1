# REV2 construction guide changes

- Freeze VALIDATION threshold selection with checkpoint and dataset hashes.
- Require that same selection for TEST; export copies runtime values, selection and matching TEST metrics with package hashes. No fallback to baseline during production export.
- Exercise nonbaseline 0.73/0.21 thresholds in the synthetic numeric smoke through TEST and ONNX packaging. This is software evidence, not physical acceptance.
- Add separate guarded, bounded BENCH firmware and interactive manual tool for initial actuator characterization. Production verified=false is preserved.
- Add portable bench policy tests and compile both UF2 targets in CI.
- Raise GPIO2 output drive to 8mA while preserving logical polarity for the REV2 optocoupler interface.
- Historical hardware masters are retained. Active REV2 wiring is a separate controlled annex; its physical validation remains pending.
