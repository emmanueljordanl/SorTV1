# Ensamblaje SorTV1

## 32 Construcción física

El asistente ENSAMBLAJE reproduce estas 22 etapas. Se completa primero la ruta mecánica y se habilita energía progresivamente. No continuar por calendario si el gate actual falla. Los 50 pasos manuales no se reemplazan por una animación, y los 200 ciclos digitales no cuentan como prueba de construcción.

Cada etapa conserva entrada, trabajo, medición, criterio PASS, error típico y condición de parada. Las herramientas se presuponen prestadas según el plan: multímetro, calibrador, soldadura/crimpado, llaves, báscula y acceso de taller. No se suman a la BOM82 como adquisiciones silenciosas.

La entrega al taller se autoriza con cotas MEASURED revisadas y luego FROZEN, indicando material, espesor, tolerancias funcionales, acceso a montaje y una ronda de ajuste. Se solicitan STEP editables donde aplique, DXF de panel, STL de impresos y planos acotados. Los meshes de la app no son sustitutos de esos archivos de fabricación.
### Etapa 01 Medir recipientes

**Entrada:** Cuatro recipientes reales. **Trabajo:** Medir reborde, boca, base, altura y asas; numerar cada uno.

**Medición:** Cotas bin0..3, variación entre piezas y extracción. **PASS:** Los cuatro caben y salen sin deformarse.

**Error típico:** Suponer que 5 L define dimensiones. **No continuar si:** No existe recorrido de retirada.

**Herramientas y fijación:** Cinta, calibrador, escuadra; Sin tornillos. **IDs:** BIN-00, BIN-01, BIN-02, BIN-03.

### Etapa 02 Medir componentes reales

**Entrada:** Componentes recibidos y fichas. **Trabajo:** Identificar modelos y contactos; medir huellas, ejes y conectores.

**Medición:** Dimensiones y ratings de todos los TBC. **PASS:** No hay incompatibilidades sin registrar.

**Error típico:** Usar dimensiones de anuncio para perforar. **No continuar si:** Faltan contactos/interfaces de corte.

**Herramientas y fijación:** Calibrador, multímetro, cámara; Registrar sin modificar. **IDs:** ACT-09, ACT-15, MECH-11, MECH-70-0, CMP-02.

### Etapa 03 Maqueta de cartón

**Entrada:** Recipientes medidos y diez muestras límite. **Trabajo:** Armar niveles A-D y guía, sin energía.

**Medición:** Barrido hoja, guía y bocas; encuadre. **PASS:** Recorrido continuo y acceso de mantenimiento.

**Error típico:** Bajar altura sin reservar barrido de hoja. **No continuar si:** Eje invade canal u objeto puentea.

**Herramientas y fijación:** Cartón, regla, cinta; Uniones temporales. **IDs:** MECH-65, MECH-66, MECH-67, MECH-68.

### Etapa 04 50 descargas manuales

**Entrada:** Maqueta con resguardos y destinos conocidos. **Trabajo:** Descargar familias variadas; rotor siempre vacío.

**Medición:** Intervenciones, rutas, atascos, orientación. **PASS:** 50 ensayos documentados; resolver cada atasco antes automatizar.

**Error típico:** Descartar silenciosamente fallos. **No continuar si:** No pasa objeto límite o papel evita haz.

**Herramientas y fijación:** Muestras, registro, cámara; No motores. **IDs:** MECH-66, MECH-67, MECH-68, BIN-00.

### Etapa 05 Congelar geometría

**Entrada:** Cotas reales y acta maqueta. **Trabajo:** Pasar MEASURED a FROZEN solo tras revisar ensamblaje.

**Medición:** Holguras, CG, FOV, tolerancias. **PASS:** CAD revisado con criterios y responsable.

**Error típico:** Confundir visualización con plano de corte. **No continuar si:** Hay BLOCKER eléctrico o dimensión crítica sin medir.

**Herramientas y fijación:** CAD/plantillas; No fijar pares universales. **IDs:** MECH-65, MECH-68.

### Etapa 06 Fabricar bastidor

**Entrada:** CAD aprobado y material. **Trabajo:** Cortar, desbarbar, escuadrar y montar travesaños.

**Medición:** Diagonales, verticalidad y apoyo. **PASS:** Estructura estable, cantos protegidos.

**Error típico:** Cerrar paneles antes probar acceso. **No continuar si:** Balancea o choca extracción.

**Herramientas y fijación:** Escuadra, taladro, llaves; M4/M5; par por material validado. **IDs:** MECH-65, MECH-LEFT, MECH-RIGHT.

### Etapa 07 Montar rodamientos y eje

**Entrada:** Bastidor escuadrado. **Trabajo:** Alinear alojamientos y dejar eje libre; collarines sin precarga indebida.

**Medición:** Coaxialidad, juego axial, giro manual. **PASS:** Gira suave sin motor.

**Error típico:** Forzar eje con acople. **No continuar si:** Hay dureza o holgura no explicada.

**Herramientas y fijación:** Calibrador, reloj comparador, llaves; Ajuste definido por rodamientos recibidos. **IDs:** MECH-69, MECH-70-0, MECH-70-1, MECH-71-0, MECH-71-1.

### Etapa 08 Montar desviador

**Entrada:** Apoyos de eje validados. **Trabajo:** Fijar hub bajo piso del canal; comprobar cuatro salidas.

**Medición:** Envolvente 360°, paso mínimo y pendiente. **PASS:** Sin colisión ni invasión del eje al flujo.

**Error típico:** Usar motor como único rodamiento. **No continuar si:** Roza bins, arnés o compuerta.

**Herramientas y fijación:** Plantillas, galgas; Fijación cautiva al hub. **IDs:** MECH-68.

### Etapa 09 Montar NEMA

**Entrada:** Rotor manual libre. **Trabajo:** Fijar soporte y acople sin empujar eje motor.

**Medición:** Coaxialidad y marcas testigo. **PASS:** Motor transmite par, apoyos toman carga radial.

**Error típico:** Prisionero sobre zona equivocada. **No continuar si:** Eje se desplaza al apretar.

**Herramientas y fijación:** Allen, escuadra; M3 motor; M4/M5 bastidor. **IDs:** ACT-09, MECH-10, MECH-11.

### Etapa 10 Bandeja y celda

**Entrada:** Bastidor y celda identificada. **Trabajo:** Fijar extremo correcto; carga por extremo libre y topes separados.

**Medición:** Tara total, deflexión y carga excéntrica. **PASS:** Tara+objeto dentro capacidad validada; no apoyo paralelo.

**Error típico:** Cable tenso o bandeja toca marco. **No continuar si:** Se supera capacidad o histéresis.

**Herramientas y fijación:** Báscula, masas, galgas; Tornillos según roscas celda. **IDs:** SENS-19, ELEC-HX711, MECH-66.

### Etapa 11 Compuerta y servo

**Entrada:** Subconjunto de pesaje. **Trabajo:** Montar todo en lado pesado; ajustar varilla sin punto muerto.

**Medición:** Torque, ángulos, barrido y switches. **PASS:** OPEN/CLOSED con margen; sin zumbido en tope.

**Error típico:** Servo fijo al bastidor deriva fuerza de peso. **No continuar si:** No cierra, calienta o roza guía.

**Herramientas y fijación:** Llaves, dinamómetro, transportador; Pasadores cautivos; par del servo proveedor. **IDs:** MECH-67, MECH-72, ACT-15, MECH-16, MECH-17.

### Etapa 12 Cámara e iluminación

**Entrada:** Bandeja completa y soporte fijo. **Trabajo:** Cámara al bastidor; difusor sin tapar lente; CSI holgado.

**Medición:** FOV techo objeto, foco, uniformidad. **PASS:** Objeto íntegro a 150 mm de altura en ROI final.

**Error típico:** Probar solo bandeja vacía. **No continuar si:** Recorta esquina o lente golpea tapa.

**Herramientas y fijación:** Carta patrón, regla; M2/M3 según módulo; agujeros TBC. **IDs:** CMP-02, ELEC-45, MECH-46, HAR-07.

### Etapa 13 Sensores

**Entrada:** Mecánica libre. **Trabajo:** Montar cuatro reed, cuatro ToF, cuatro barreras y límites.

**Medición:** Ventanas exclusivas, cobertura y polaridades. **PASS:** Todos con soporte, ruta y prueba individual.

**Error típico:** Sensor usado como tope duro. **No continuar si:** Haz no detecta papel o dos reed simultáneos.

**Herramientas y fijación:** Multímetro, muestras, soporte ranurado; PETG incluido; geometría por medir. **IDs:** SENS-22, SENS-23, SENS-24, SENS-25, SENS-ROT0, SENS-TOF0, SENS-27.

### Etapa 14 Panel electrónico

**Entrada:** Componentes y esquema resuelto. **Trabajo:** Montar zona alta lógica, baja potencia y HX cerca celda.

**Medición:** Ventilación, acceso tornillos, distancia arnés. **PASS:** Separado del residuo y accesible.

**Error típico:** Cooler contra pared o bornera colgante. **No continuar si:** Queda interfaz de potencia sin resolver.

**Herramientas y fijación:** Taladro, separadores, multímetro; M3 y soporte aislante. **IDs:** CMP-01, CMP-06, ELEC-12, ELEC-32, SAFE-34.

### Etapa 15 Arnés

**Entrada:** Panel sin alimentación. **Trabajo:** Cortar a ruta medida; etiquetar ambos extremos; crimpar y revisar.

**Medición:** Wire-from/to, continuidad, caída y tirón. **PASS:** Sin positivos unidos ni retorno de motor por Pico.

**Error típico:** Usar color como única identificación. **No continuar si:** Corto, cobre expuesto o borde vivo.

**Herramientas y fijación:** Crimpadora, multímetro, termorretráctil; PG7/9 y cinchos con holgura. **IDs:** HAR-53, HAR-54, HAR-55, HAR-56, HAR-57, HAR-58.

### Etapa 16 Resguardos

**Entrada:** Arnés validado sin energía. **Trabajo:** Cerrar zonas móviles y contactos; validar accesos.

**Medición:** Apertura antes de acceso, volumen de parada. **PASS:** Interrupción física verificable.

**Error típico:** Confiar en UI para detener. **No continuar si:** Contactos no cortan o resguardo alcanzable.

**Herramientas y fijación:** Plantilla acceso, multímetro; Tornillos desmontables. **IDs:** SAFE-78, MECH-TOP, MECH-DOOR, SAFE-33.

### Etapa 17 Firmware sin motores

**Entrada:** Sensores y USB, potencia aislada. **Trabajo:** Verificar boot, GPIO, CRC, temporizadores y estados.

**Medición:** Estados nEN/PWM desde reset. **PASS:** Sin pulsos intempestivos; identidad nueva.

**Error típico:** Probar solo tras init software. **No continuar si:** nEN arranca habilitado.

**Herramientas y fijación:** Analizador lógico, laptop; No conectar motores. **IDs:** CMP-06.

### Etapa 18 Motor de banco

**Entrada:** DRV identificado y sensor índice de prueba. **Trabajo:** Leer Rsense; corriente conservadora; rampa lenta.

**Medición:** Fase, VREF, temperatura y pérdida de pasos. **PASS:** Repetible sin exceder térmica.

**Error típico:** Conectar bobinas con VMOT vivo. **No continuar si:** Sin control de corriente o calor excesivo.

**Herramientas y fijación:** Multímetro, sonda térmica; Resguardado y descargado. **IDs:** ACT-09, ELEC-12, ELEC-13.

### Etapa 19 Servo de banco

**Entrada:** Buck calibrado sin carga. **Trabajo:** Alimentar externo; probar recorrido sin forzar tope.

**Medición:** Tensión 6 V bajo pico, consumo, pulsos. **PASS:** Movimiento repetible sin stall.

**Error típico:** Usar bloqueo como régimen. **No continuar si:** Buck cae o servo zumba sin mover.

**Herramientas y fijación:** Multímetro, fuente protegida; Montaje firme sin residuo. **IDs:** ACT-15, ELEC-32.

### Etapa 20 Integración

**Entrada:** C0-C8 y fallos básicos. **Trabajo:** Ciclo diagnóstico protegido; destino conocido separado de IA.

**Medición:** Cadena causa-señal-movimiento-confirmación. **PASS:** Cuatro destinos y recuperaciones correctas.

**Error típico:** Contar ACK como caída. **No continuar si:** Un solo movimiento no autorizado.

**Herramientas y fijación:** Registros y observación externa; Resguardos cerrados. **IDs:** MECH-68, MECH-67, CMP-06, CMP-01.

### Etapa 21 Clasificación IA

**Entrada:** Modelo y preprocessing con hash. **Trabajo:** Activar decisiones a partir de tres imágenes nuevas.

**Medición:** Recall, pureza, cobertura y latencias. **PASS:** P08/P09, paquete coherente y sin fuga.

**Error típico:** Entrenar usando test o fondo sesgado. **No continuar si:** No hay modelo validado o frame viejo.

**Herramientas y fijación:** Laptop entrenamiento; Pi inferencia; No alterar hardware para acertar. **IDs:** CMP-01, CMP-02.

### Etapa 22 Pruebas de aceptación

**Entrada:** Versión congelada. **Trabajo:** P01-P16; F01-F30; 200 ciclos y térmica.

**Medición:** Denominadores, evidencia y fallos preservados. **PASS:** Criterios cumplidos con evidencia física.

**Error típico:** Rellenar PHYSICAL con simulación. **No continuar si:** Hay fallo de protección o resultado incierto.

**Herramientas y fijación:** Checklist, muestras, logs; Revisar tornillos tras sesión. **IDs:** MECH-65, CMP-01, CMP-06.
