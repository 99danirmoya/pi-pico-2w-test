from machine import Pin, I2C, ADC
import ssd1306
import framebuf
import time

# ------------- CONFIGURACIÓN GENERAL -------------
WIDTH = 128
HEIGHT = 64

# I2C para Pico 2W (SDA=GP0, SCL=GP1)
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Potenciómetro en GP26 (Pin 31)
pot = ADC(26)

# Botón en GP14 (Pin 19) con pull-up interno
button = Pin(14, Pin.IN, Pin.PULL_UP)

# LED Integrado de la Pico 2W
led_builtin = Pin("LED", Pin.OUT)

# LED encendido continuo durante la carga inicial
led_builtin.value(1)

# ------------- PANTALLA DE CARGA -------------
def draw_loading(progress_fraction):
    """
    Muestra el texto ' *o. flipbook .o* ' y una barra de progreso.
    progress_fraction: 0.0 .. 1.0
    """
    oled.fill(0)

    title = " *o. flipbook .o* "
    text_width = len(title) * 8
    x_text = (WIDTH - text_width) // 2
    y_text = 16

    oled.text(title, x_text, y_text)

    # Barra de progreso
    bar_x = 10
    bar_y = 40
    bar_width = WIDTH - 2 * bar_x   # 108 px
    bar_height = 8

    # Marco
    oled.rect(bar_x, bar_y, bar_width, bar_height, 1)

    # Limitar fracción
    if progress_fraction < 0:
        progress_fraction = 0
    if progress_fraction > 1:
        progress_fraction = 1

    filled_width = int(bar_width * progress_fraction)
    if filled_width > 0:
        # pequeño margen interior
        inner_w = filled_width - 2 if filled_width > 2 else 0
        if inner_w > 0:
            oled.fill_rect(bar_x + 1, bar_y + 1, inner_w, bar_height - 2, 1)

    oled.show()

# Mostrar 0% al inicio de la carga
draw_loading(0.0)

# --- IMPORTA AQUÍ TUS GIFS ---

# Primer GIF -> 1/3 de la barra
import gif1_oled
draw_loading(1.0 / 3.0)

# Segundo GIF -> 2/3 de la barra
import gif2_oled
draw_loading(2.0 / 3.0)

# Tercer GIF -> barra completa
import gif3_oled
draw_loading(1.0)

# LED apagado cuando termina la carga de GIFs
led_builtin.value(0)

GIF_LIST = [
    gif1_oled.FRAMES,
    gif2_oled.FRAMES,
    gif3_oled.FRAMES,
]

# Índice del GIF actual
current_gif_index = 0

# Flag para la interrupción del botón
button_flag = False

# Buffer global para ahorrar memoria
video_buffer = bytearray(WIDTH * HEIGHT // 8)
fb = framebuf.FrameBuffer(video_buffer, WIDTH, HEIGHT, framebuf.MONO_VLSB)

# ------------- INTRODUCCIÓN CENTRADA -------------
def show_intro():
    target_text = "es rey<3 literal"
    center_y = (HEIGHT - 8) // 2
    current_line = ""

    for char in target_text:
        current_line += char
        pixel_width = len(current_line) * 8
        center_x = (WIDTH - pixel_width) // 2
        
        oled.fill(0)
        oled.text(current_line, center_x, center_y)
        oled.show()
        time.sleep(0.20)
        
    time.sleep(1.0)

# ------------- LECTURA POTENCIÓMETRO -> FRAME -------------
def read_pot_raw():
    # Devuelve la lectura cruda del ADC (0..65535)
    return pot.read_u16()

def pot_to_frame_index(raw, num_frames):
    """
    Mapear el valor del potenciómetro (0..65535) a un índice de frame invertido:
    pot mínimo -> último frame
    pot máximo -> primer frame
    """
    if num_frames <= 1:
        return 0

    pos = raw / 65535.0      # 0.0 .. 1.0
    pos_inv = 1.0 - pos      # invertir

    idx = int(pos_inv * num_frames)
    if idx >= num_frames:
        idx = num_frames - 1
    return idx

# ------------- LED: FRECUENCIA SEGÚN POSICIÓN DE FRAME -------------
LED_MIN_DELAY = 0.05   # parpadeo más rápido (final del GIF)
LED_MAX_DELAY = 0.50   # parpadeo más lento (inicio del GIF)

def frame_to_led_delay(frame_idx, num_frames):
    """
    Relaciona la posición del frame (0..num_frames-1) con el delay de parpadeo del LED.
    - Primer frame  -> LED_MAX_DELAY (lento)
    - Último frame  -> LED_MIN_DELAY (rápido)
    Con curva suave (cuadrática) para que los cambios sean más suaves al principio.
    """
    if num_frames <= 1:
        return LED_MAX_DELAY
    pos = frame_idx / (num_frames - 1)  # 0.0 .. 1.0
    pos = pos * pos  # curva cuadrática
    return LED_MAX_DELAY - pos * (LED_MAX_DELAY - LED_MIN_DELAY)

# Suavizado del delay del LED
smoothed_led_delay = LED_MAX_DELAY
SMOOTH_FACTOR = 0.2  # 0..1

# ------------- INTERRUPCIÓN DEL BOTÓN -------------
def button_irq(pin):
    global button_flag
    button_flag = True

button.irq(trigger=Pin.IRQ_FALLING, handler=button_irq)

# ------------- EJECUCIÓN -------------

# 1. MOSTRAR INTRO
show_intro()

print(f"Sistema iniciado. {len(GIF_LIST)} GIFs cargados.")

# Estado inicial del LED para parpadeo
led_state = False
led_builtin.value(led_state)
last_led_toggle = time.ticks_ms()

try:
    while True:
        # A. GESTIÓN BOTÓN: cambiar de GIF
        if button_flag:
            button_flag = False
            time.sleep_ms(50)  # antirrebote
            if button.value() == 0:
                current_gif_index = (current_gif_index + 1) % len(GIF_LIST)
                oled.fill(0)
                oled.show()
                print(f"Cambiado a GIF {current_gif_index}")

        # B. OBTENER FRAMES DEL GIF ACTUAL
        frames = GIF_LIST[current_gif_index]
        num_frames = len(frames)

        # C. LEER POTENCIÓMETRO Y SELECCIONAR FRAME
        raw = read_pot_raw()
        frame_idx = pot_to_frame_index(raw, num_frames)

        # D. MOSTRAR FRAME SELECCIONADO
        source_frame = frames[frame_idx]
        video_buffer[:] = source_frame
        oled.blit(fb, 0, 0)
        oled.show()

        # E. GESTIONAR PARPADEO DEL LED SEGÚN FRAME (SUAVIZADO)
        target_led_delay = frame_to_led_delay(frame_idx, num_frames)
        smoothed_led_delay = (
            smoothed_led_delay * (1.0 - SMOOTH_FACTOR)
            + target_led_delay * SMOOTH_FACTOR
        )

        now = time.ticks_ms()
        if time.ticks_diff(now, last_led_toggle) >= int(smoothed_led_delay * 1000):
            led_state = not led_state
            led_builtin.value(led_state)
            last_led_toggle = now

        # F. PEQUEÑA PAUSA PARA NO SATURAR CPU
        time.sleep(0.01)

except KeyboardInterrupt:
    oled.fill(0)
    oled.show()
    led_builtin.value(0)
    print("Programa detenido")

