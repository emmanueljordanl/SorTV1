# TrashIA class mapping

TrashIA v1 está descargado localmente: workspace/project trashia, task_type object-detection, licencia CC BY 4.0. Ver [metadata](../../sortv1/training/datasets/roboflow/trashia_metadata.json), [fuentes públicas](../../sortv1/training/datasets/roboflow/public_metadata.json) y [atribución](../../sortv1/training/datasets/roboflow/ATTRIBUTION.md).

El operador confirmó revisión visual manual de múltiples muestras por clase. Las anotaciones COCO de train/valid/test corroboran los nombres y sus category_id; las etiquetas numéricas no se interpretan por su número. Evidencia: **ROBOFLOW_METADATA + COCO_ANNOTATIONS + MANUAL_VISUAL_REVIEW**. La revisión manual es la proporcionada por el usuario; esta corrección no afirma una nueva inspección visual ni resultados físicos.

| source_class | COCO category_id | meaning_verified | target | reason | reviewed | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | GLASS | CHALLENGE_OOD | Vidrio fuera del dominio validado del MVP | true | ROBOFLOW_METADATA + COCO_ANNOTATIONS + MANUAL_VISUAL_REVIEW |
| 1 | 2 | CARDBOARD | PAPEL_CARTON | Muestras de cartón revisadas por el operador | true | ROBOFLOW_METADATA + COCO_ANNOTATIONS + MANUAL_VISUAL_REVIEW |
| 2 | 3 | MEDICAL_WASTE | CHALLENGE_OOD | Residuos médicos fuera del dominio | true | ROBOFLOW_METADATA + COCO_ANNOTATIONS + MANUAL_VISUAL_REVIEW |
| 3 | 4 | METAL | METAL_LATAS | Muestras de metal revisadas; distribución final definida por datos locales | true | ROBOFLOW_METADATA + COCO_ANNOTATIONS + MANUAL_VISUAL_REVIEW |
| 4 | 5 | PAPER | PAPEL_CARTON | Muestras de papel revisadas por el operador | true | ROBOFLOW_METADATA + COCO_ANNOTATIONS + MANUAL_VISUAL_REVIEW |
| 5 | 6 | MIXED_PLASTIC | CHALLENGE_OOD | Plásticos mezclados; no convertir toda la clase a PET | true | ROBOFLOW_METADATA + COCO_ANNOTATIONS + MANUAL_VISUAL_REVIEW |

COCO category_id=0/name=trash es la categoría contenedora, no una séptima clase material. El mapping existente en class_mapping.yaml se conserva. PET no recibe datos externos limpios de esta revisión: MIXED_PLASTIC completo permanece CHALLENGE_OOD.

El manifest deduplicado y el auxiliar contienen 19 925 imágenes EXTERNAL, repartidas únicamente en train_external/challenge. TrashIA es auxiliar y **no valida SorTV1**. Selección de umbrales y evaluación final siguen requiriendo LOCAL_PHYSICAL validation y LOCAL_PHYSICAL test. No se atribuyen precisión SorTV1, benchmarks de Pi ni aceptación física a este dataset.
