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

# --- IMPORTA AQUÍ TUS GIFS ---
import gif1_oled
import gif2_oled
import gif3_oled

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
    # Texto a mostrar (la fuente por defecto no tiene el corazón "❣", 
    # así que usamos "<3" o "!" para asegurar que se lea bien)
    target_text = "es rey<3 literal" 
    
    # Posición Y centrada verticalmente (64 altura total - 8 altura texto) / 2
    center_y = (HEIGHT - 8) // 2
    
    current_line = ""
    
    for char in target_text:
        # Añadimos una letra más a la frase actual
        current_line += char
        
        # Calculamos cuánto ocupa la frase que llevamos escrita hasta ahora
        # La fuente por defecto de MicroPython mide 8 píxeles de ancho por caracter
        pixel_width = len(current_line) * 8
        
        # Calculamos la X para que ESTA frase específica quede centrada
        center_x = (WIDTH - pixel_width) // 2
        
        # Dibujamos
        oled.fill(0)
        oled.text(current_line, center_x, center_y)
        oled.show()
        
        # Pausa entre letras (efecto máquina de escribir)
        time.sleep(0.15)
        
    # Pausa final para leer el mensaje completo
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

# 1. MOSTRAR INTRO (SOLO AL ENCENDER)
show_intro()

# 2. BUCLE PRINCIPAL (GIFS)
print(f"Sistema iniciado. {len(GIF_LIST)} GIFs cargados.")

try:
    while True:
        # GESTIÓN DEL BOTÓN
        if button_flag:
            button_flag = False
            time.sleep_ms(50)
            if button.value() == 0:
                current_gif_index = (current_gif_index + 1) % len(GIF_LIST)
                current_frame_index = 0
                oled.fill(0)
                oled.show()
                print(f"Cambiado a GIF {current_gif_index}")
        
        # GESTIÓN DEL MOVIMIENTO
        delay, direction = get_delay_and_direction()
        
        if direction == 0:
            time.sleep(0.05)
            continue
            
        frames = GIF_LIST[current_gif_index]
        num_frames = len(frames)
        current_frame_index = (current_frame_index + direction) % num_frames
        
        source_frame = frames[current_frame_index]
        video_buffer[:] = source_frame
        
        oled.blit(fb, 0, 0)
        oled.show()
        
        if delay is not None:
            time.sleep(delay)

except KeyboardInterrupt:
    oled.fill(0)
    oled.show()
    print("Programa detenido")
