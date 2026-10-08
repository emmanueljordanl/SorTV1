# ECN REV2

Base main 5d7893049b1d6ec5d206d28fb51c9626b30e7f42, develop 26d989d2ce8ee81f2ff1214f43d70747bd263657; same tree a6dda4483fd928286055946d7ff866582a03749b.

B09: successful VALIDATION selection is bound to model/dataset. TEST evaluates its exact thresholds. Export refuses missing or mismatched selection/TEST report and hashes both provenance files. CLI now requires --thresholds and export --test-report. Update automation accordingly. Runtime labels and image contracts remain unchanged.

B07: separate sortv1_bench image for manually requested isolated characterization. Hardware cut remains independent. Bounds and leases do not establish actuator compatibility. No generic calibration values or physical PASS are added. Production image continues to require signed calibration.

B01: GPIO2 remains high=disabled, low=enabled. An optocoupler with independent driver pullup prevents unpowered Pico backfeed. The electrical design and physical checks are specified in the REV2 manual, and are not approved hardware merely by this PR.

Validation: Python contracts, C++ policy/physical contracts, repository generators, SDK compilation and synthetic ONNX smoke are required. Physical P01-P16 remain PENDING. This change makes no CE, UL, PL or SIL claim. Do not merge or energize solely because CI passes.

B05: Active wiring powers Adafruit2168 TX and RX from independent 3.3V AUX; receiver open-collector outputs have separate 10k pulls to Pico 3V3. Test voltage/polarity before GPIO attachment.

B08: Generic KF301 are not used in active distribution. WAGO221-415 junction blocks have numbered contacts and explicit bridge leads in active_rev2.csv. Mount the junctions in compatible carriers and label each potential; never connect different potentials within one common block. Inspections and measurements are mandatory before installation/energization. Active interface uses D36V50F6 #4092, not a D24V22F6.
