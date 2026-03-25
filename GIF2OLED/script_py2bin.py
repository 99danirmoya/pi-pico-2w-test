import importlib.util
import struct
import sys
import os
import types

# --- Rutas ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
BIN_DIR    = os.path.join(SCRIPT_DIR, "output bin")

os.makedirs(BIN_DIR, exist_ok=True)

FRAME_SIZE = 128 * 64 // 8  # 1024 bytes por frame

# --- Mock de framebuf para que el import no falle ---
framebuf_mock = types.ModuleType("framebuf")
framebuf_mock.FrameBuffer = None
framebuf_mock.MONO_VLSB   = 0
sys.modules["framebuf"] = framebuf_mock

# --- Archivos .py en output/ en orden alfabético ---
py_files = sorted([
    f for f in os.listdir(OUTPUT_DIR)
    if f.endswith(".py") and not f.startswith("__")
])

print(f"Archivos .py encontrados en output/ ({len(py_files)}):")
for i, f in enumerate(py_files, 1):
    print(f"  gif{i}_oled.bin  <-  {f}")
print()

def convertir(py_path, bin_path, gif_name):
    spec = importlib.util.spec_from_file_location(gif_name, py_path)
    mod  = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"  [ERROR al cargar {os.path.basename(py_path)}]: {e}")
        return False

    if not hasattr(mod, "FRAMES"):
        print(f"  [ERROR] {os.path.basename(py_path)} no tiene FRAMES")
        return False

    frames     = mod.FRAMES
    num_frames = len(frames)

    with open(bin_path, "wb") as f:
        f.write(struct.pack("<I", num_frames))
        for i, frame in enumerate(frames):
            data = bytes(frame)
            if len(data) != FRAME_SIZE:
                print(f"  [AVISO] Frame {i} tiene {len(data)} bytes (se esperan {FRAME_SIZE})")
            f.write(data)

    size_kb = os.path.getsize(bin_path) / 1024
    print(f"  OK -> {os.path.basename(bin_path)}  |  {num_frames} frames  |  {size_kb:.1f} KB")
    return True

# --- Convertir ---
print("Convirtiendo...\n")
ok = 0
for idx, py_file in enumerate(py_files, 1):
    py_path  = os.path.join(OUTPUT_DIR, py_file)
    bin_name = f"gif{idx}_oled.bin"
    bin_path = os.path.join(BIN_DIR, bin_name)
    gif_name = f"gif{idx}_oled"

    if convertir(py_path, bin_path, gif_name):
        ok += 1

print(f"\nListo. {ok}/{len(py_files)} GIFs convertidos en 'output bin/'")
print("Copia los .bin a la raiz de tu SD.")