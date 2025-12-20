from mss import mss
from PIL import Image
import numpy as np


LEFT, TOP, WIDTH, HEIGHT = 735, 427, 459, 360  # подставишь

def screenshot_region(left: int, top:int, width:int, height:int) -> Image.Image:
    with mss() as sct:
        region = {"left": left, "top": top, "width": width, "height": height}
        shot = sct.grab(region)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return img

def split_grid_np(img: Image.Image, cols: int, rows: int):
    arr = np.asarray(img)  # shape: (h, w, 3) или (h, w, 4)
    h, w = arr.shape[:2]
    cell_w = w / cols
    cell_h = h / rows

    grid = []
    for r in range(rows):
        row = []
        y0 = int(round(r * cell_h))
        y1 = int(round((r + 1) * cell_h))
        for c in range(cols):
            x0 = int(round(c * cell_w))
            x1 = int(round((c + 1) * cell_w))
            row.append(arr[y0:y1, x0:x1])  # numpy slice
        grid.append(row)
    return grid

if __name__ == "__main__":
    img = screenshot_region()
    img.save("region.png")
    print("Saved: region.png")

    split_grid_np(img, 10, 9)
