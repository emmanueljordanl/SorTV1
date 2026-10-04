# Contratos del software de producción

## 22 Raspberry Pi 5

CMP-01 ejecutará Raspberry Pi OS de 64 bits y servicios pequeños sin escritorio cuando no haga falta. microSD64 almacena OS, modelo y evidencia; Active Cooler y ventilación se ensayan en gabinete cerrado. Se mide RAM, swap, CPU, temperatura y latencia durante sesión, no solo una inferencia aislada.

El servicio productivo se instala con usuario dedicado, dependencias fijadas, configuración legible y reinicio limitado. Arrancar Pi no arma el Pico ni reenvía automáticamente una orden pendiente. Tras reconectar: HELLO/STATUS, comprobar boot_id, revisar journal, esperar READY y crear solo el siguiente ciclo físico autorizado.

No se entrena en Pi. No se usan nube, internet obligatorio, ROS 2, otra SBC o acelerador. ONNX Runtime CPU con batch1 y FP32 es el baseline. INT8 solo se acepta tras medir mejora de latencia y conservación de criterios de calidad.

La ubicación alta responde al límite CSI. La alimentación USB-C, microSD y USB de Pico permanecen alcanzables desde mantenimiento. No encerrar cooler contra un panel ni poner el cable CSI sobre su ventilador. Las versiones exactas del entorno físico se registran al instalar y comprobar la imagen real; la versión de Three.js del gemelo no es una dependencia de Pi.
## 23 Pico como autoridad física

FW-01 es el contrato de máquina de estados; FW-02 adquisición/antirrebote; FW-03 temporizadores y watchdog; FW-04 protocolo; FW-05 control STEP/DIR/PWM. El firmware real usará C++ y Pico SDK con bucle no bloqueante, tick objetivo de 1 ms, PWM hardware y temporizador/PIO para STEP. El watchdog solo se alimenta después de completar todas las comprobaciones del bucle.

SORT destination=N es una intención. No existen comandos productivos «servo 80°» o «437 pasos». El controlador comprueba ciclo, boot, vigencia, resguardos, potencia, CLOSED, presencia estable, guía vacía y destino disponible antes de aceptar. La interfaz de operador productiva solo consulta y exporta.

La simulación ejecuta JavaScript equivalente a ese contrato, con un tick de 20 ms y planta idealizada; no emula un RP2040 ni certifica tiempos de interrupción. Menos de 50 ms de reconocimiento lógico es una meta física que se mide con señal de entrada y salida. El corte eléctrico es independiente de esa meta y su tiempo también se mide.

Durante reset: nEN deshabilitado, PWM ausente, nuevo boot_id, ciclo anterior inválido y permiso de rearme perdido. El homing solo se permite después de inspección de recorrido vacío. Los fines de carrera no se fuerzan por tiempo: un PWM terminado sin señal válida no cambia el resultado a confirmado.
## 24 Arquitectura software

La arquitectura productiva se mantiene separada de los archivos del navegador. Estructura prevista: app/capture.py, quality.py, inference.py, decision.py, transport.py, controller.py, evidence.py y operator_ui/; training/; firmware/; tests/; config/; models/; docs/; evidence/. docs/production-contracts.md describe entradas/salidas y gates de integración. No se entrega código flasheable ni un modelo entrenado ficticio.

El gemelo usa src/core, simulation, sensors, protocol, three, engineering y evidence. ModelBuilder/SceneManager agrupan geometría y vistas para evitar duplicar piezas en decenas de archivos vacíos. La UI aplica estímulos de laboratorio virtual —tapa, objeto, paro—; no recibe acceso directo a las salidas de motor. La selección manual de objeto se convierte en evidencia sintética de percepción, claramente rotulada.

Frame contiene frame_id, cycle_id, timestamp monótono Pi, RGB y controles exposure/gain/WB. Los timestamps de firmware y Pi no se restan entre sí sin sincronización: edad de imagen se calcula en Pi; plazo de decisión desde INSPECT se mide en Pico. Se preservan ambos dominios en registro.

Las pruebas de software reales deben incluir imágenes y tensores de referencia, parser bajo fragmentación, estados contradictorios y reinicio. La prueba del gemelo acredita únicamente la implementación digital; cada adaptador de hardware requerirá sus ensayos.
| ID módulo | Entrada | Proceso y salida | Fallos/dependencias |
| --- | --- | --- | --- |
| SW-01 capture | INSPECT(cycle_id) | Picamera2 produce tres frames RGB nuevos, timestamp monótono y controles → Frame{frame_id,cycle_id,timestamp,RGB,exposure,gain,WB} | buffer viejo, cámara ausente / CMP-02, reloj Pi |
| SW-02 quality | Frame y ROI calibrada | Verifica edad≤300 ms, ocupación, foco y exposición → QualityResult{valid,reason} | tapada, blur, ROI inválida / SW-01, configuración |
| SW-03 inference | Tensor FP32 1×3×224×224 | ONNX Runtime CPU batch1 MobileNetV3 Small → probabilities[4], model_sha256 | modelo faltante, salida inválida / models/, SW-02 |
| SW-04 decision | Tres predicciones válidas | top1>0.80, margen>0.15, consenso≥2/3 → Decision{predicted_class,decision,requested_bin} | incertidumbre u OOD no detectado / SW-03, labels/thresholds |
| SW-05 transport | JSON compacto y CRC16 | Acota 512 bytes, timeout, clave idempotente → ACK/NACK/DONE/FAULT | CRC, truncado, boot viejo / USB CDC, FW-01 |
| SW-06 controller | Eventos un ciclo | No pide SORT hasta persistir intención; vigencia de sesión → Intención y estado lógico | reinicio o duplicado de ciclo / SW-01..07 |
| SW-07 evidence | Eventos y resumen | JSONL append, flush/fsync de intent antes SORT; deduplicación → CSV/JSONL/hash | ENOSPC, corte antes commit / microSD, reloj Pi |
| SW-08 operator_ui | Snapshot inmutable | Consulta/exporta estado → Visualización sin mando motor | estado obsoleto, enlace ausente / SW-06/07 |
## 25 IA y dataset

MobileNetV3 Small parte de pesos ImageNet y una cabeza de cuatro salidas; la arquitectura está disponible en Torchvision [S7]. El orden contractual es [PET, PAPEL_CARTON, METAL_LATAS, OTRO_SECO_CONOCIDO] y su mapping a bins es [0,1,2,3]. labels.json, el índice de salida y destination mapping deben coincidir exactamente. Un modelo correcto con etiquetas permutadas descarga en un bin incorrecto.

Preprocesamiento único: ROI calibrada que preserve objeto entero → RGB explícito → resize224×224 según política congelada → float32 → /255 → normalización mean[0.485,0.456,0.406], std[0.229,0.224,0.225] → NCHW 1×3×224×224. Si se usa letterbox se congela su relleno y se reproduce en entrenamiento. No mezclar BGR de una librería con RGB supuesto por otra.

Entrenamiento de referencia: backbone congelado 5 epochs, AdamW lr0.001 y batch32; después bloques finales descongelados, 10–20 epochs, lr0.0001 y early stopping≈5. Seleccionar por macro-F1 de validación. Conservar semilla, versiones, manifest, transformaciones, pesos iniciales y registro de experimento. Son parámetros de partida, no promesa de convergencia.

Paquete: model.onnx FP32 shape fija; labels.json; preprocess.json; thresholds.json; dataset_manifest.csv; training/entrenamiento.json; SHA-256 por archivo. Comprobar equivalencia PyTorch/ONNX en al menos 50 imágenes, comparar logits/probabilidades y clases con tolerancia explicada, y ejecutar el mismo tensor en laptop y Pi antes de aceptar latencias.

Baseline de captura: TRAIN 25 objetos por clase ×4 ×12 imágenes≈1200; VALID 10×4×4≈160; TEST 15×4×4≈240; 40 desafíos fuera del catálogo. El split es por objeto físico, no por imagen. Todas las vistas de un objeto quedan en una partición; considerar además sesión/familia. El test se congela antes de elegir umbrales y no se reutiliza para ajustar.

Manifest mínimo: object_id, session_id, class_id, split, image_path, source, lighting_setup, operator y excluded_reason. Mezclar orden y posiciones para no enseñar el fondo. Documentar objetos deformados, materiales compuestos, desconocidos y dos piezas; no borrar errores difíciles sin motivo predefinido.

Política inicial: top1>0.80, margen top1−top2>0.15 y al menos dos de tres frames válidos votan la misma clase. La implementación exige los tres frames válidos antes del consenso; si calidad falla → REVIEW. Softmax alto no demuestra pertenencia al dominio conocido. El operador supervisa restricciones de ingreso y se publican desafíos con alta confianza errónea.

Separar predicted_class, decision, requested_bin, confirmed_bin y physical_result. ACK solo acredita aceptación del contrato. En el gemelo se aplican realmente los umbrales a probabilidades sintéticas; no se ejecuta un archivo ONNX inexistente ni se presenta una exactitud aprendida.
## 26 Protocolo Pi y Pico

El transporte es USB CDC mediante HAR-08. Cada mensaje es JSON ASCII compacto, seguido de |, CRC hexadecimal de cuatro dígitos y LF. CRC16-CCITT-FALSE: polinomio0x1021, inicial0xFFFF, sin reflexión ni XOR final. La entrada de prueba ASCII 123456789 debe producir 29B1. El CRC protege errores accidentales, no autentica mensajes.

Máximo total 512 bytes incluyendo CRC y LF. El parser incremental limita buffer, descarta hasta fin de línea tras exceso y abandona una línea incompleta tras 250 ms de referencia. Rechaza JSON inválido, versión equivocada, campos mal tipados y destino fuera de0–3 antes de actuar. Una línea truncada no bloquea el bucle de control.

Clave idempotente: boot+cycle+request. Repetición idéntica devuelve ACK/status conocido sin actuar otra vez; misma clave y distinto destino → NACK ID_CONFLICT. Además, un request nuevo para el mismo ciclo ya reclamado se rechaza: no sirve cambiar request para repetir una descarga. Un nuevo boot invalida órdenes del anterior.

**Normal:** Pico HELLO/STATUS → Pico INSPECT → Pi persiste intención → Pi SORT → Pico ACK → posición/OPEN/caída/CLOSED → Pico DONE → Pi persiste y suma una vez. **ACK perdido:** Pi QUERY o mismo SORT; el historial devuelve estado sin segunda descarga. **Duplicado conflictivo:** NACK; conservar operación original. **CRC inválido:** NACK y ninguna activación causada por el mensaje. **Truncado:** timeout de parser, recuperar próxima línea. **USB ausente/Pi congelada:** heartbeat vencido, parada y recuperación manual. **Pi reiniciada:** reconecta sin reemitir orden pendiente; conciliar. **Pico reiniciado:** nuevo boot, BOOT_SAFE, sin permiso previo.

Una Pi puede recibir ACK después de que el mecanismo ya comenzó: ACK no prueba resultado físico. Si DONE se pierde pero Pico conserva estado, QUERY puede recuperar el resultado confirmado. Si ambos reinician tras caída y antes de persistencia, no existe una garantía física de exactamente una vez; el journal marca incertidumbre y exige inspección.

La entrega incluye serializador, CRC y parser ejecutables en src/protocol/Protocol.js y tests de fragmentación/error. La consola RAW muestra los bytes generados; DECODED muestra campos y edad en reloj virtual. Los ejemplos y registros llevan source SIMULATION.
| Mensaje | Origen | Efecto |
| --- | --- | --- |
| HELLO/STATUS | Pico | Versión, boot, estado y sensores; no movimiento |
| INSPECT | Pico | Nuevo ciclo e inicio de plazo local |
| SORT | Pi | Intención destino0–3; valida guardas |
| ACK/NACK | Pico | Aceptación/rechazo, no éxito físico |
| DONE/FAULT | Pico | Resultado confirmado o causa de fallo |
| HEARTBEAT | Pi y contrato ambos | Vigencia; cada200 ms referencia |
| QUERY | Pi | Consulta idempotente sin movimiento |

El código de navegador no es firmware listo para producción. Implementar los adaptadores reales solo después de cerrar los bloqueos de hardware.
