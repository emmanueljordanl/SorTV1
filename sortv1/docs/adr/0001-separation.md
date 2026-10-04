# ADR 0001 Autoridad del control físico

Estado: aceptada como arquitectura; integración física pendiente.

La Pi usa Python para percepción y evidencia. El Pico W usa C++ y Pico SDK para estados y actuadores. USB CDC transporta intenciones de ciclo. El corte DC de actuadores depende de paro y resguardos además de las señales leídas por firmware. La aplicación no tiene órdenes de PWM, STEP ni rearme remoto.

Consecuencia: se pueden probar contratos sin hardware, pero esos resultados deben estar rotulados SIMULATION y no cuentan como aceptación de la máquina. El gemelo digital web permanece en su carpeta original y no se usa como autoridad física.
