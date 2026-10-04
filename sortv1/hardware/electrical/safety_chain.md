# Cadena independiente del software

PENDING_PHYSICAL_VALIDATION. E-STOP NC enclavable + contacto NC de tapa + contacto NC de servicio en serie autorizan una habilitación **manual enclavada** del dispositivo de corte DC. Abrir cualquiera debe desenergizar su bobina/entrada de seguridad y cortar motor y buck/servo, aunque la Pi/Pico estén bloqueados. Restaurar contactos no debe restaurar automáticamente potencia: requiere pulsador físico de habilitación y después rearme físico del Pico, con bandeja y trayectoria vacías.

W111–W119 definen terminales simbólicos; sustituirlos por números del fabricante tras seleccionar y verificar dispositivo y contactos. No comprar un relé solo porque anuncie “10 A”: verificar rating DC, carga inductiva, corriente de arranque, contactos y circuito de retención. El módulo de un canal del gemelo permanece TBC_MODEL; no está aprobado como componente de seguridad. La arquitectura experimental no acredita un PL/SIL ni certificación de seguridad.

Los contactos de tapa/servicio que notifican GPIO12/27 deben ser eléctricamente separados de los contactos de 12 V de la cadena: usar contactos auxiliares independientes o interfaz aislada verificada. Nunca compartir un borne de 12 V con la entrada lógica. Probar circuito abierto/cable roto y polaridad antes de escribir `active_high` en calibración.

GPIO28 solo recibe salida lógica ≤3V3 de MVP-84. Sin modelo y ensayo de aislamiento/nivel, no conectar W109. nEN tiene pull-up externo para deshabilitar DRV8825 durante reset, BOOTSEL o desconexión MCU. Software añade interlocks y watchdog; nunca sustituye el corte físico.

Prueba progresiva: con actuadores desconectados usar carga de prueba protegida en bus cortado; abrir paro/tapa/servicio, medir desaparición de energía, mantener firmware bloqueado/reiniciado, comprobar no rearranque al cerrar y documentar lectura de feedback. Repetir con cargas reales protegidas tras medir corrientes. Registrar tensión, tiempo de corte, corriente y condición de las cargas como PHYSICAL. Hasta entonces: TBC_MEASURE y P01/P02/P15 PENDING. Detener ante contacto soldado, reinicio automático, feedback falso o energía residual capaz de producir movimiento.
