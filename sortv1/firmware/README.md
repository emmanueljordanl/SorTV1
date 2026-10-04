# Firmware del Pico W

Base de contratos C++17. Los headers describen estados, guardas, interfaces de drivers, CRC y temporizadores. No hay un programa Pico SDK, binario UF2 ni control físico integrado. Estos headers aún requieren compilación y pruebas en el entorno del Pico.

Al implementar el firmware: salidas deshabilitadas en BOOT_SAFE, nuevo boot_id en cada arranque, rearme exclusivamente físico, homing después de inspección de recorrido vacío y bucle cooperativo sin esperas largas. Guardar operación activa e historial acotado; un request nuevo no permite repetir una descarga del mismo ciclo. No alimentar watchdog sin completar el bucle de comprobación.

El corte de potencia de tapa, servicio y paro es independiente del software. El contrato de protocolo completo está en `../docs/architecture/protocol.md` y el pinout en `../hardware/pinout/pico.csv`. Los adaptadores de entradas deben convertir polaridad eléctrica y estados inválidos explícitamente; las guardas no son un circuito de protección.
