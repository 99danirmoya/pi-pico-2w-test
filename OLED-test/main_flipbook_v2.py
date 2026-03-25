from machine import Pin, I2C, ADC, SPI
import ssd1306
import framebuf
import time
import os
import struct
import sdcard
import gc

# ------------- CONFIGURACIÓN GENERAL -------------
WIDTH  = 128
HEIGHT = 64
FRAME_SIZE = WIDTH * HEIGHT // 8  # 1024 bytes

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

# ------------- SD CARD POR SPI -------------
# MISO -> GP12 | MOSI -> GP11 | SCK -> GP10 | CS -> GP13
spi = SPI(1, baudrate=4_000_000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11), miso=Pin(12))
cs = Pin(13, Pin.OUT)

try:
    sd = sdcard.SDCard(spi, cs)
    os.mount(sd, "/sd")
except Exception as e:
    oled.fill(0)
    oled.text("Error SD:", 0, 0)
    oled.text(str(e)[:16], 0, 10)
    oled.show()
    raise

# ------------- DETECTAR GIFS EN LA SD -------------
GIF_FILES = sorted([
    "/sd/" + f for f in os.listdir("/sd")
    if f.endswith(".bin")
])

num_gifs = len(GIF_FILES)

oled.fill(0)
if num_gifs == 0:
    oled.text("No hay GIFs", 0, 20)
    oled.text("en la SD", 0, 30)
    oled.show()
    raise SystemExit
else:
    title = " *o. flipbook .o* "
    text_width = len(title) * 8
    x_text = (WIDTH - text_width) // 2
    y_text = 16
    oled.text(title, x_text, y_text)
    oled.text("GIFs en SD: " + str(num_gifs), 0, 36)
    oled.show()

time.sleep(1.5)
led_builtin.value(0)

# ------------- GESTIÓN DE GIF ACTUAL DESDE .bin -------------
current_gif_index = 0
gif_file     = None
num_frames   = 0

def open_gif(index):
    """Abre el archivo .bin del GIF indicado y lee la cabecera."""
    global gif_file, num_frames
    if gif_file:
        gif_file.close()
        gif_file = None
        gc.collect()
    gif_file   = open(GIF_FILES[index], "rb")
    header     = gif_file.read(4)
    num_frames = struct.unpack("<I", header)[0]
    gc.collect()

def read_frame(frame_idx, buf):
    """Lee el frame indicado directamente del .bin al buffer."""
    offset = 4 + frame_idx * FRAME_SIZE
    gif_file.seek(offset)
    gif_file.readinto(buf)

# ------------- BUFFER GLOBAL -------------
video_buffer = bytearray(FRAME_SIZE)
fb = framebuf.FrameBuffer(video_buffer, WIDTH, HEIGHT, framebuf.MONO_VLSB)

# ------------- INTRODUCCIÓN CENTRADA -------------
def show_intro():
    target_text = "es rey<3 literal"
    center_y    = (HEIGHT - 8) // 2
    current_line = ""
    for char in target_text:
        current_line += char
        pixel_width = len(current_line) * 8
        center_x    = (WIDTH - pixel_width) // 2
        oled.fill(0)
        oled.text(current_line, center_x, center_y)
        oled.show()
        time.sleep(0.20)
    time.sleep(1.0)

# ------------- LECTURA POTENCIÓMETRO -> FRAME -------------
def read_pot_raw():
    return pot.read_u16()

def pot_to_frame_index(raw, n):
    if n <= 1:
        return 0
    pos_inv = 1.0 - raw / 65535.0
    idx = int(pos_inv * n)
    return min(idx, n - 1)

# ------------- LED: FRECUENCIA SEGÚN FRAME -------------
LED_MIN_DELAY = 0.05
LED_MAX_DELAY = 0.50

def frame_to_led_delay(frame_idx, n):
    if n <= 1:
        return LED_MAX_DELAY
    pos = (frame_idx / (n - 1)) ** 2
    return LED_MAX_DELAY - pos * (LED_MAX_DELAY - LED_MIN_DELAY)

smoothed_led_delay = LED_MAX_DELAY
SMOOTH_FACTOR      = 0.2

# ------------- INTERRUPCIÓN DEL BOTÓN -------------
button_flag = False

def button_irq(pin):
    global button_flag
    button_flag = True

button.irq(trigger=Pin.IRQ_FALLING, handler=button_irq)

# ------------- EJECUCIÓN -------------
show_intro()

open_gif(current_gif_index)
print("Sistema iniciado.", num_gifs, "GIFs en SD.")

led_state       = False
led_builtin.value(led_state)
last_led_toggle = time.ticks_ms()

try:
    while True:
        # A. Botón: cambiar de GIF
        if button_flag:
            button_flag = False
            time.sleep_ms(80)
            if button.value() == 0:
                current_gif_index = (current_gif_index + 1) % num_gifs
                oled.fill(0)
                oled.show()
                open_gif(current_gif_index)
                print("GIF", current_gif_index + 1, "de", num_gifs)

        # B. Potenciómetro -> índice de frame
        raw       = read_pot_raw()
        frame_idx = pot_to_frame_index(raw, num_frames)

        # C. Leer frame del .bin al buffer y mostrar
        read_frame(frame_idx, video_buffer)
        oled.blit(fb, 0, 0)
        oled.show()

        # D. LED según frame (suavizado)
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

        time.sleep(0.01)

except KeyboardInterrupt:
    if gif_file:
        gif_file.close()
    oled.fill(0)
    oled.show()
    led_builtin.value(0)
    try:
        os.umount("/sd")
    except OSError:
        pass
    print("Programa detenido")
