# Firmware RP2040

El firmware conceptual se modela en `src/core/StateMachine.js`, `src/protocol/Protocol.js` y `data/pinout.json`. El código de producción para Pico W debe conservar GPIO, guards, CRC, boot_id/cycle_id/request e idempotencia definidos en `docs/production-contracts.md`.
