# Mapeo TrashIA

Estado: ACCESS_REQUIRED. La página pública devolvió 403 y la API devolvió 401; no se pudieron verificar task type, clases, versión, licencia, imágenes, splits o preprocessing. Esos campos son `null` en los metadatos; no se inventaron nombres ni mapeos. Falta ROBOFLOW_API_KEY local autorizada o un ZIP exportado con metadata/licencia verificable.

`scripts/fetch_trashia.py --inspect-only` usa SDK oficial. Luego elegir explícitamente `--version N`; nunca “latest”. El script incorpora todas las clases descubiertas a `class_mapping.yaml`, cada una por defecto CHALLENGE_OOD con `reviewed: false`, y regenera este reporte por clase. Para usar una clase interna, un operador debe revisar catálogo, material y justificación y marcar `reviewed: true`.

Las únicas etiquetas entrenables son PET, PAPEL_CARTON, METAL_LATAS y OTRO_SECO_CONOCIDO. “Plastic” no demuestra PET; vidrio, comida, pilas, húmedos, peligrosos y fuera de catálogo no son OTRO. CHALLENGE_OOD y EXCLUDE no son clases entrenables; RECHAZO es decisión. Los externos siempre train_external o challenge, incluso si el export público tenía valid/test. Validación y selección final dependen de LOCAL_PHYSICAL.

Convertidor COCO recorta bbox/máscaras con margen conservador y conserva versión, original, anotación, clase y hashes. Si un original contiene un objeto challenge, todos sus crops quedan challenge para evitar fuga por source_image_id. Un crop tiene object_id por anotación; no se declara objeto físico independiente de evaluación. Importador classification preserva los mismos campos. ZIP se valida contra traversal, enlaces y tamaños excesivos; una versión importada no se sobrescribe.
