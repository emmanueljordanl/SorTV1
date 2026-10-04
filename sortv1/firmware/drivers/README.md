# Drivers físicos

`interfaces.hpp` separa sensores y actuadores. Pendiente: GPIO, PWM hardware, STEP/DIR con temporizador o PIO, HX711, I²C y cuatro ToF. Conocer polaridades y niveles antes de implementar. No usar esperas bloqueantes largas en el bucle cooperativo.
