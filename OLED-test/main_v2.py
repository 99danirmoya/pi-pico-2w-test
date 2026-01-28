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

led_builtin.value(1)

# --- IMPORTA AQUÍ TUS GIFS ---
import gif1_oled
import gif2_oled
import gif3_oled

led_builtin.value(0)

GIF_LIST = [
    gif1_oled.FRAMES,
    gif2_oled.FRAMES,
    gif3_oled.FRAMES,
]

# Índice del GIF actual
current_gif_index = 0
current_frame_index = 0

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
        time.sleep(0.15)
        
    time.sleep(2.0)

# ------------- FUNCIONES DE CONTROL -------------
MAX_SPEED = 0.008
DEAD_ZONE = 0.05

def read_pot_normalized():
    raw = pot.read_u16()
    x = raw / 65535.0
    v = (x - 0.5) * 2.0
    if -DEAD_ZONE < v < DEAD_ZONE:
        return 0.0
    return v

def get_delay_and_direction():
    v = read_pot_normalized()
    if v == 0.0:
        return None, 0
    
    speed = abs(v)
    delay = MAX_SPEED / speed 
    direction = 1 if v > 0 else -1
    return delay, direction

# ------------- INTERRUPCIÓN DEL BOTÓN -------------
def button_irq(pin):
    global button_flag
    button_flag = True

button.irq(trigger=Pin.IRQ_FALLING, handler=button_irq)

# ------------- EJECUCIÓN -------------

# 1. MOSTRAR INTRO
show_intro()

print(f"Sistema iniciado. {len(GIF_LIST)} GIFs cargados.")

# Variables para el parpadeo del LED
led_timer = 0
led_state = False

try:
    while True:
        # A. GESTIÓN BOTÓN
        if button_flag:
            button_flag = False
            time.sleep_ms(50)
            if button.value() == 0:
                current_gif_index = (current_gif_index + 1) % len(GIF_LIST)
                current_frame_index = 0
                oled.fill(0)
                oled.show()
                print(f"Cambiado a GIF {current_gif_index}")
        
        # B. GESTIÓN MOVIMIENTO
        delay, direction = get_delay_and_direction()
        
        if direction == 0:
            # Parado: apagamos LED y esperamos
            led_builtin.value(0)
            time.sleep(0.05)
            continue
            
        # C. REPRODUCIR FRAMES
        frames = GIF_LIST[current_gif_index]
        num_frames = len(frames)
        current_frame_index = (current_frame_index + direction) % num_frames
        
        source_frame = frames[current_frame_index]
        video_buffer[:] = source_frame
        
        oled.blit(fb, 0, 0)
        oled.show()
        
        # D. GESTIÓN LED (Parpadeo cada 5 frames)
        led_timer += 1
        if led_timer >= 3: 
            led_timer = 0
            led_state = not led_state
            led_builtin.value(led_state)
        
        # E. ESPERA
        if delay is not None:
            time.sleep(delay)

except KeyboardInterrupt:
    oled.fill(0)
    oled.show()
    led_builtin.value(0)
    print("Programa detenido")
