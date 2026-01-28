from PIL import Image
import os

WIDTH = 128
HEIGHT = 64

INPUT_DIR = "input"   # carpeta donde pondrás los .gif
OUTPUT_DIR = "output" # opcional: donde se guardan los .py generados


def frame_to_vlsb_buffer(img_bw):
    img_bw = img_bw.convert("1")
    w, h = img_bw.size
    assert w == WIDTH and h == HEIGHT

    buf = bytearray()
    pages = h // 8

    for page in range(pages):
        for x in range(w):
            b = 0
            for bit in range(8):
                y = page * 8 + bit
                if img_bw.getpixel((x, y)) > 0:
                    b |= (1 << bit)
            buf.append(b)
    return buf


def resize_and_center(frame):
    w, h = frame.size
    frame_ratio = w / h
    target_ratio = WIDTH / HEIGHT

    if frame_ratio > target_ratio:
        new_w = WIDTH
        new_h = int(WIDTH / frame_ratio)
        x = 0
        y = (HEIGHT - new_h) // 2
    else:
        new_h = HEIGHT
        new_w = int(HEIGHT * frame_ratio)
        x = (WIDTH - new_w) // 2
        y = 0

    frame = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("1", (WIDTH, HEIGHT), 0)
    frame_bw = frame.convert("1", dither=Image.FLOYDSTEINBERG)
    canvas.paste(frame_bw, (x, y))
    return canvas


def convert_one_gif(path_in, path_out_py):
    im = Image.open(path_in)
    frames = []

    try:
        idx = 0
        while True:
            im.seek(idx)
            frame = im.convert("RGBA")
            prepared = resize_and_center(frame)
            buf = frame_to_vlsb_buffer(prepared)
            frames.append(buf)
            idx += 1
    except EOFError:
        pass

    print(f"{os.path.basename(path_in)} -> {len(frames)} frames")

    with open(path_out_py, "w", encoding="utf-8") as f:
        f.write("import framebuf\n\n")
        f.write("# Datos auto-generados para SSD1306 (128x64)\n")
        f.write("FRAMES = [\n")
        for i, buf in enumerate(frames):
            f.write(f"    # frame {i}\n    bytearray([\n        ")
            for j, b in enumerate(buf):
                f.write(f"0x{b:02x}, ")
                if (j + 1) % 16 == 0:
                    f.write("\n        ")
            f.write("]),\n")
        f.write("]\n")


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = [f for f in os.listdir(INPUT_DIR)
             if f.lower().endswith((".gif", ".png", ".jpg", ".jpeg"))]

    if not files:
        print(f"No hay imágenes en '{INPUT_DIR}'.")
        return

    for fname in files:
        in_path = os.path.join(INPUT_DIR, fname)
        base, _ = os.path.splitext(fname)
        out_py = os.path.join(OUTPUT_DIR, f"{base}_oled.py")
        convert_one_gif(in_path, out_py)

    print("Conversión terminada.")


if __name__ == "__main__":
    main()
