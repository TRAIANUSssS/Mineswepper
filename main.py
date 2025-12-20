import cv2
import numpy as np

from detect_fields import Detection
from get_field import screenshot_region, split_grid_np
from tabulate import tabulate

pixel_area = {
    "small": [735, 427, 450, 360]  # LEFT, TOP, WIDTH, HEIGHT
}

field_count = {
    "small": [10, 8]  # cols, rows
}

if __name__ == "__main__":
    preset = "small"

    LEFT, TOP, WIDTH, HEIGHT = pixel_area[preset]
    COLS, ROWS = field_count[preset]

    img = screenshot_region(LEFT, TOP, WIDTH, HEIGHT)  # PIL.Image (RGB)
    img.save("region.png")
    print("Saved: region.png")

    grid = split_grid_np(img, COLS, ROWS)  # list[rows][cols] of numpy arrays (RGB)
    print(len(grid[0]), len(grid))

    field_type_list = [[None for _ in range(COLS)] for _ in range(ROWS)]
    detection = Detection()

    # ВНИМАНИЕ: grid у тебя = [rows][cols], поэтому правильнее так:
    for r_i, row in enumerate(grid):
        for c_i, cell_rgb in enumerate(row):
            # cell_rgb: numpy (H,W,3) в RGB -> сделаем BGR
            sector_bgr = cv2.cvtColor(cell_rgb, cv2.COLOR_RGB2BGR)

            label, num, meta = detection.classify_cell(sector_bgr)
            field_type_list[r_i][c_i] = num

            print(r_i, c_i, label, num, meta)

    print(tabulate(field_type_list, tablefmt="plain", numalign="right"))
