# Archivo histórico

El ZIP original del gemelo v1.0 se conserva íntegro desde la aportación inicial; no es la fuente de desarrollo ni se regenera aquí. El tag `v0.1.0` conserva la disposición anterior y los assets `dist/` históricos. No se reescribe historial.

La fuente vigente es la carpeta del gemelo. `python scripts/build_distribution.py` crea un ZIP con commit y SHA-256 en `artifacts/`; CI lo publica como artifact. `dist/` se genera con npm y deja de versionarse. No se declara SorTV1 físico v1.0.
