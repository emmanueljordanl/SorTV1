# Contribuir a SorTV1

Usar Git y un pull request para cada cambio. El destino normal es `develop`; `main` recibe entregas revisadas desde `develop` o correcciones urgentes justificadas y reintegradas después.

## Empezar una tarea

```bash
git fetch origin --prune
git switch develop
git pull --ff-only origin develop
git switch -c feature/protocol-v1
```

Modificar y verificar solo el alcance de la tarea. Antes del commit, revisar `git diff` y las pruebas pertinentes. Añadir archivos concretos para evitar incorporar registros locales por accidente:

```bash
git add sortv1/app/transport sortv1/tests/protocol
git commit -m "feat(protocol): validar mensajes USB v1"
git push -u origin feature/protocol-v1
```

Crear un PR con base `develop`, describir el problema y comportamiento resultante, indicar pruebas y separar evidencia SIMULATION de PHYSICAL. CI debe pasar. Revisar el PR antes de fusionar; activar una aprobación obligatoria cuando el segundo integrante tenga acceso. El administrador puede fusionar solo mientras no haya otro revisor disponible, conservando PR y comprobaciones.

Fusionar tareas preferentemente con squash. Actualizar `develop` con `pull --ff-only` y borrar la rama de tarea después de integrarla. No conservar ramas de funcionalidades sin trabajo ni mezclar modificaciones físicas no relacionadas en el mismo PR.

## Entregas

Abrir PR `develop` → `main` con alcance, pruebas, versiones y pendientes. Usar merge commit para conservar relación entre ramas y promover `main` a `develop` después de la entrega. Etiquetar versiones verificadas: v0.x para bases y prototipos; v1.0 solo después de cumplir la aceptación física. El tag v0.1.0 corresponde a esta base inicial, no al MVP completo.

En la congelación del día 28 puede abrirse `release/v1.0` desde `develop` si hay que aislar las correcciones de aceptación. No se crea esa rama anticipadamente. Una corrección urgente parte de `main` en `fix/*`, pasa por PR y se reintegra a `develop`.

## Comprobaciones locales

```powershell
py -3 scripts/verify_repository.py
cd sortv1
py -3 -m unittest discover -s tests -v
```

Para cambios del gemelo, ejecutar además `npm ci`, `npm test` y `npm run build` en su carpeta. Al regenerar `dist/`, revisar el diff antes del commit. Los resultados de P01–P16, calibración y hardware siguen un procedimiento físico independiente.

Los binarios pequeños existentes se guardan en Git. Antes de agregar datasets, modelos o CAD grandes, acordar almacenamiento y Git LFS y mantener sus hashes/manifiestos versionados. No agregar credenciales, dependencias descargadas ni entornos locales.
