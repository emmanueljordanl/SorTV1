# Dependencia fijada

Pololu VL53L0X Arduino, commit `9f3773cb48d4e4e844d689cfc529a06f96d1d264`, licencia MIT incluida en `vl53l0x/LICENSE.txt`. Archivos `.h/.cpp` sin modificaciones. Origen: https://github.com/pololu/vl53l0x-arduino/tree/9f3773cb48d4e4e844d689cfc529a06f96d1d264.

`shim/` es el adaptador propio Pico SDK: cada transacción I2C tiene timeout de 1 ms. Inicialización secuencial XSHUT exclusivamente en BOOT_SAFE, antes de activar watchdog, con timeout interno de 50 ms. Lecturas continuas solamente tras comprobar data-ready. Los errores de bus, rango inválido o antigüedad producen UNKNOWN.
