# Characterization image and procedure

`sortv1_bench.uf2` is a separate, bounded bench image. It does not implement SORT, does not set calibration::verified and cannot run AUTO. GPIO2 retains active-low disable semantics. The REV2 interface uses an active-low optocoupler and a persistent driver rail; production GPIO2 drive is set to 8mA for electrical margin. Do not connect GPIO2 directly to the independent rail.

Hardware fixture prerequisites: only one actuator connected; motor decoupled from rotor or servo horn removed; rigidly mounted actuator and shaft guard; physical E-STOP, lid B and service B cut actuator power; lid A GP12, service A GP27 and power feedback GP28 are low when valid; physical RESET GP15 is a held deadman, low when pressed. External 10k input pullups are required. Test guard and deadman polarity with power removed before using this image. Never bridge a guard to obtain permission.

Boot and reconnect disable motor and PWM and produce a new BENCH1 nonce. Each request carries that nonce, CRC16-CCITT-FALSE and increasing sequence. An action requires guards stable for 100ms, fresh heartbeat (<301ms), USB and held deadman. A guard/deadman/USB/heartbeat interruption latches motion off until a fresh USB session. STEP is 1..32 pulses at 2000..10000us period and DIR0. SERVO is 500..2500us for 20..500ms. These are protocol bounds, not a statement that a particular actuator tolerates the entire range. Use the manufacturer's confirmed range and begin with an unloaded mechanism. Every lease expires, no movement is replayed.

Build alongside production: `cmake -S sortv1/firmware -B build/pico -G Ninja -DPICOTOOL_NO_LIBUSB=1` then `cmake --build build/pico -j2`, SDK 2.3.1 pinned as in CI. Check the SHA256 and commit of the UF2. BOOTSEL copies only the bench image for characterization; afterwards restore the production safe image, then generate calibrated firmware only from actual records.

On Pi, stop `sortv1.service`, activate the project virtual environment and enter the sortv1 directory. Example one motor request, with the fixture already checked:

```
python -m app.tools.bench_characterize --port /dev/ttyACM0 --operator Mane --actuator step --steps 1 --period-us 10000 --fixture-checked --output evidence/experiments/bench-step-001.json
```

The port above is an example: resolve the connected Pico serial identity first. Press and hold physical RESET, type EJECUTAR once and watch the guarded actuator. Review ACCEPTED or REJECTED. The tool never reports physical PASS. Power off before adjusting or reconnecting; do not retry an unknown result. For an unloaded servo, supply `--actuator servo --pulse-us` from the confirmed neutral-pulse specification and `--duration-ms 100`. Do not guess neutral for a commercial variant. Record observed angle, raw current, temperature, physical end positions and manufacturer identity separately. Files remain RECORDED/acceptance PENDING.
