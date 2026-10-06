# Interfaces de entradas: baseline de ingeniería

Todo este documento es PENDING_PHYSICAL_VALIDATION. Los modelos/rating/terminales concretos requieren TBC_MODEL, polaridad y configuración TBC_CALIBRATE. No modificar `calibration::verified=false` ni llenar `active_high` con supuestas mediciones.

GPIO12 LID_CLOSED,13 GATE_CLOSED,14 GATE_OPEN,15 PHYSICAL_RESET,16–19 ROTOR_INDEX_0..3 y27 SERVICE_CLOSED son los nueve contactos secos. Cada uno:

```text
3V3_LOGIC
    |
10 kOhm externo (1%, 1/4 W o equivalente)
    |
    +---- GPIO
    |
contacto seco lógico
    |
GND_LOGIC
```

Diseño activo-bajo: contacto abierto lleva HIGH y contacto cerrado LOW. Antes de cablear/activar, verificar continuidad, cable abierto, polaridad y nivel en el módulo real. No habilitar gpio_pull_up() como sustituto principal. MVP-87 compra12 resistencias (9 usadas+3 repuestos); las ramas W120–W146 representan pulls y retornos. Los contactos lógicos de tapa/servicio son separados/aislados de sus contactos12V de seguridad; jamás compartir un borne12V.

nEN/GPIO2: MVP-83 añade10kΩ1%1/4W externo del lado driver a3V3_LOGIC persistente. W105/W106 y W029 deben dejar nEN HIGH/deshabilitado durante reset, BOOTSEL, firmware no iniciado y Pico retirado. Verificar que la fuente3V3 del pull y la resistencia siguen presentes en el lado driver con el Pico desconectado; no suponer que su regulador retirado mantiene ese rail. Aprobar módulo y alimentación reales antes de energizar VMOT; no confiar en firmware para este estado. Si la lógica completa no tiene energía, aislar12V hasta verificar la condición de arranque.

HX711_DOUT/GPIO10 no es contacto seco. La [hoja de datos del IC AVIA HX711](https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf) identifica DOUT como salida digital y DVDD como alimentación digital, que debe corresponder a la alimentación del MCU. Esto no verifica el breakout actual: SENS-19/ELEC-HX711 sigue TBC_MODEL. Identificar esquema/puentes y DVDD real, verificar DOUT≤3V3 y PD_SCK compatible; si DVDD está unido a5V, no conectar DOUT al Pico sin adaptación adecuada. No añadir pull-up genérico por falta de esquema. Registrar modelo/datasheet/esquema y medidas antes de aprobar W043/W044.

FALL_BEAM_0..3/GPIO20/21/22/26: módulos TBC_MODEL. Antes de conectar determinar push-pull, open-collector, open-drain u optoaislado, alimentación, tensión de salida y polaridad. Una salida de5V exige adaptación de nivel apropiada; una salida de12V exige interfaz/aislamiento apropiado. Solo después de verificar el tipo de salida se diseña su bias/interfaz específico. No copiar los pulls de contactos secos a estas señales.

ACTUATOR_POWER_FEEDBACK/GPIO28: bus12V cortado → MVP-84 aislamiento/adaptación → salida≤3V3. W107–W110 son propuesta con terminales TBC_MODEL; W058 es referencia histórica no aprobada. Nunca12V directamente a GPIO28, ni pull-up genérico para ocultar un feedback indefinido. Ensayar pérdida de alimentación/salida desconectada/fallo de interfaz y definir estado seguro antes de calibrar.

ACTUATOR_ENABLE/MVP-88 es del latch físico de control12V; no tiene GPIO. PHYSICAL_RESET/BOM-26 pertenece aGPIO15 y a la topología de contacto seco anterior. Cerrar resguardos no habilita el latch. Ver [safety_chain](safety_chain.md) y fuentes canónicas; regenerar con `python scripts/generate_hardware_views.py`, nunca editar solo las vistas.
