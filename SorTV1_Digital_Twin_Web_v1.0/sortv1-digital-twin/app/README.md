# Aplicación física de SorTV1

La aplicación destinada a Raspberry Pi se especifica en `docs/production-contracts.md` y en el documento de ingeniería. El gemelo ejecutable vive en `src/`; no se conecta a motores físicos ni sustituye al software de producción.

Contratos obligatorios: `capture`, `quality`, `inference`, `decision`, `transport`, `controller`, `evidence`, `operator_ui`.
