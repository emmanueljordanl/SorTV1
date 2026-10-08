# ECN REV2

Base main 5d7893049b1d6ec5d206d28fb51c9626b30e7f42, develop 26d989d2ce8ee81f2ff1214f43d70747bd263657; same tree a6dda4483fd928286055946d7ff866582a03749b.

B09: successful VALIDATION selection is bound to model/dataset. TEST evaluates its exact thresholds. Export refuses missing or mismatched selection/TEST report and hashes both provenance files. CLI now requires --thresholds and export --test-report. Update automation accordingly. Runtime labels and image contracts remain unchanged.

B07: separate sortv1_bench image for manually requested isolated characterization. Hardware cut remains independent. Bounds and leases do not establish actuator compatibility. No generic calibration values or physical PASS are added. Production image continues to require signed calibration.

B01: GPIO2 remains high=disabled, low=enabled. An optocoupler with independent driver pullup prevents unpowered Pico backfeed. The electrical design and physical checks are specified in the REV2 manual, and are not approved hardware merely by this PR.

Validation: Python contracts, C++ policy/physical contracts, repository generators, SDK compilation and synthetic ONNX smoke are required. Physical P01-P16 remain PENDING. This change makes no CE, UL, PL or SIL claim. Do not merge or energize solely because CI passes.
