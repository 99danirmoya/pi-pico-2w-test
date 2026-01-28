<div align="center">

# Raspberry Pi Pico 2W test: GIF2OLED

</div>

Este proyecto es una prueba para entender cómo funciona la **Raspberry Pi Pico 2W** usando **Thonny IDE** con **MicroPython**, y un flujo de trabajo en **Python + VS Code** para convertir GIFs en animaciones reproducibles en un OLED SSD1306.

---

## 🧩 Estructura del proyecto

El proyecto cuenta con dos etapas principales:

1. **Python en VS Code**  
   Conversión de archivos **GIF** en buffers de frames binarizados (blanco y negro, 128×64) listos para ser usados en la Pico.
   - Lectura de GIFs desde una carpeta de entrada.
   - Redimensionado y centrado al tamaño del OLED.
   - Conversión a 1‑bit.
   - Generación de archivos `.py` con una lista `FRAMES = [bytearray(...), ...]`.

2. **MicroPython en Thonny (Raspberry Pi Pico 2W)**  
   Selección y lectura de los frames correspondientes a los GIFs ya convertidos.
   - Carga de los módulos `gifX_oled.py` generados en la etapa anterior.
   - Reproducción de los GIFs en el OLED SSD1306 vía I2C.
   - Control interactivo mediante potenciómetro y botón físico.

---

## 🎬 Funcionamiento del dispositivo

Al encender la Raspberry Pi Pico 2W:

1. **Mensaje de bienvenida**  
   Se muestra un texto de intro en el OLED, escribiéndose letra por letra y manteniéndose centrado en la pantalla.

2. **Presentación del primer GIF**  
   Tras la intro, se muestra el primer GIF disponible en la memoria de la Pico.

3. **Navegación entre GIFs (botón)**  
   - Un **botón** conectado a un pin GPIO con resistencia pull‑up interna permite cambiar de GIF.  
   - Cada pulsación avanza al siguiente GIF en orden circular (cuando llega al último, vuelve al primero).

4. **Control de velocidad y sentido (potenciómetro)**  
   - Un **potenciómetro** conectado a una entrada ADC de la Pico controla la reproducción:
     - En el punto medio: la animación se **detiene**.
     - Girando hacia un lado: la animación avanza **hacia adelante**, aumentando la velocidad cuanto más se aleja del centro.
     - Girando hacia el lado contrario: la animación se reproduce **hacia atrás**, con la misma lógica de velocidad.

---

## 🛠️ Tecnologías usadas

- **Hardware**
  - Raspberry Pi Pico 2W  
  - Pantalla OLED SSD1306 (128×64, I2C)  
  - Potenciómetro (entrada analógica)  
  - Botón pulsador (entrada digital con pull‑up interno)

- **Software**
  - Python 3 + VS Code (con entorno virtual)  
  - Librería Pillow para procesado de imágenes (conversión de GIFs)  
  - Thonny IDE  
  - MicroPython para Raspberry Pi Pico 2W  

---

## 🚀 Objetivo del proyecto

Explorar de forma práctica:

- El flujo de trabajo mixto **PC (Python)** + **microcontrolador (MicroPython)**.  
- El uso del **ADC** y de entradas digitales para crear una interfaz física sencilla.  
- La reproducción de animaciones en pantallas OLED de baja resolución a partir de GIFs estándar.

Este repositorio sirve como base para proyectos más complejos de animación, interfaces visuales y pequeños “players” de GIFs en hardware embebido.
