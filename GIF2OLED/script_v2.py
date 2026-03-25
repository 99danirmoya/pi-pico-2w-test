from PIL import Image
import os

# OLED parameters
WIDTH = 128
HEIGHT = 64

# Folders
INPUT_DIR = "input"   # put your GIFs/PNGs/JPGs here
OUTPUT_DIR = "output" # generated *_oled.py files go here


def frame_to_vlsb_buffer(img_bw):
    """
    Convert a 1-bit 128x64 image to a bytearray in MONO_VLSB format,
    as expected by MicroPython's framebuf for SSD1306.
    """
    img_bw = img_bw.convert("1")
    w, h = img_bw.size
    assert w == WIDTH and h == HEIGHT

    buf = bytearray()
    pages = h // 8  # each page = 8 vertical pixels

    for page in range(pages):
        for x in range(w):
            b = 0
            for bit in range(8):
                y = page * 8 + bit
                if img_bw.getpixel((x, y)) > 0:  # white pixel
                    b |= (1 << bit)
            buf.append(b)
    return buf


def despeckle(img_1bit, min_white_neighbors=3):
    """
    Remove isolated white pixels: keeps a white pixel only if
    it has at least 'min_white_neighbors' white pixels in its 3x3 neighborhood.
    """
    w, h = img_1bit.size
    pixels = img_1bit.load()
    out = Image.new("1", (w, h), 0)
    out_px = out.load()

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            white_count = 0
            for j in (-1, 0, 1):
                for i in (-1, 0, 1):
                    if pixels[x + i, y + j] > 0:
                        white_count += 1
            out_px[x, y] = 255 if white_count >= min_white_neighbors else 0

    return out


def resize_and_center(frame, use_threshold=False, threshold=140):
    """
    Resize the frame keeping aspect ratio, center it in 128x64,
    convert to 1-bit without dithering, and optionally apply a custom threshold
    and despeckle filter to reduce noise.
    """
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

    # Resize with good quality
    frame = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Create target canvas
    canvas = Image.new("L", (WIDTH, HEIGHT), 0)  # grayscale for threshold step

    # Convert to grayscale
    gray = frame.convert("L")

    if use_threshold:
        # Manual threshold: values > threshold -> white (255), else black (0)
        bw = gray.point(lambda v: 255 if v > threshold else 0)
    else:
        # Simple convert to 1-bit without dithering (threshold ~127 by default)
        bw = gray.convert("1", dither=Image.Dither.NONE)
        # Convert back to L so we can apply despeckle uniformly
        bw = bw.convert("L")

    # Paste into centered canvas
    canvas.paste(bw, (x, y))

    # Convert to 1-bit and despeckle to reduce isolated white dots
    canvas_1bit = canvas.convert("1", dither=Image.Dither.NONE)
    canvas_1bit = despeckle(canvas_1bit, min_white_neighbors=3)

    return canvas_1bit


def convert_one_gif(path_in, path_out_py, use_threshold=False, threshold=140):
    im = Image.open(path_in)
    frames = []

    try:
        idx = 0
        while True:
            im.seek(idx)
            frame = im.convert("RGBA")  # normalize input
            prepared = resize_and_center(frame, use_threshold=use_threshold,
                                         threshold=threshold)
            buf = frame_to_vlsb_buffer(prepared)
            frames.append(buf)
            idx += 1
    except EOFError:
        pass  # no more frames

    print(f"{os.path.basename(path_in)} -> {len(frames)} frames")

    # Write Python file with FRAMES list
    with open(path_out_py, "w", encoding="utf-8") as f:
        f.write("import framebuf\n\n")
        f.write("# Auto-generated data for 128x64 SSD1306\n")
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

    files = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".gif", ".png", ".jpg", ".jpeg"))
    ]

    if not files:
        print(f"No images in '{INPUT_DIR}'. Put your GIFs there.")
        return

    # Choose whether to use manual thresholding
    USE_THRESHOLD = True   # set True if you want to tweak 'threshold'
    THRESH_VALUE = 140      # 0..255, higher = darker, less noise

    for fname in files:
        in_path = os.path.join(INPUT_DIR, fname)
        base, _ = os.path.splitext(fname)
        out_py = os.path.join(OUTPUT_DIR, f"{base}_oled.py")
        convert_one_gif(in_path, out_py,
                        use_threshold=USE_THRESHOLD,
                        threshold=THRESH_VALUE)

    print("Done.")


if __name__ == "__main__":
    main()
