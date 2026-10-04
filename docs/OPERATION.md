# Operación supervisada

Desde sortv1: SIMULATION `python -m app --simulate`; DIAGNOSTIC `python -m app --mode diagnostic`; PHYSICAL_AUTO `python -m app --mode physical`. DIAGNOSTIC necesita `--enable-actuators --dest N` para solicitar destino conocido sin IA; Pico conserva interlocks. Todos los logs distinguen modo y fuente. Simulación no valida aceptación.

Antes de rearme: resguardos, energía aislada, bandeja/rotor/trayecto vacíos, compuerta cerrada y sensores conocidos. Habilitar cadena y pulsar rearme físico; CHECK_HOME y LISTO. Un objeto seco de catálogo ≤100×100×150mm y≤200g por ciclo. No admitir húmedos, peligrosos, pilas, vidrio ni objetos no verificados. Peso no decide material.

Primer AUTO supervisado. Configurar admission_record y registrar inspección humana para boot/cycle de INSPECT con `python -m app.tools.admit --operator OPERADOR --boot BOOT --cycle NUM --single-object --dry-known-catalog --within-limits`. Archivo contiene operator, timestamp UNIX, boot, cycle y tres permisos humanos; vence120s y no vale para otro ciclo. IA no acredita catálogo ni seguridad.

UI local: LISTO/PROCESANDO/REVISIÓN/FALLO y datos del último ciclo, tapa/servicio/potencia, llenado orientativo, almacenamiento, modelo y firmware. Consulta/exportación; conciliación por CLI con servicio parado. Paro individual no está instrumentado por GPIO propio: no inferirlo desde power_feedback.

Solo DONE acredita destino/caída correctos + bandeja vacía estable + compuerta cerrada. ACK no cuenta. Incertidumbre de un objeto previamente admitido puede decidir RECHAZO hacia destino3; no es etiqueta entrenable. FULL/UNKNOWN bloquean destino sin reruteo. REVIEW exige retirar objeto y cerrar registro con potencia aislada. FAULT exige identificar causa antes de rearme.
