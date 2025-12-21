import cv2
from typing import List, Tuple

from detect_fields import Detection


def detect_board_from_grid(
    grid_rgb: List[List],  # [ROWS][COLS] numpy RGB
    detection: Detection
) -> Tuple[List[List[int]], List[List[int]]]:
    """
    Преобразует grid (numpy RGB клетки) в:
      field[r][c] = -1/0/1..8
      mine[r][c]  = -1/0 (мин пока не знаем, но открытые точно не мины)
    """
    ROWS = len(grid_rgb)
    COLS = len(grid_rgb[0]) if ROWS else 0

    field = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    mine = [[-1 for _ in range(COLS)] for _ in range(ROWS)]

    for r, row in enumerate(grid_rgb):
        for c, cell_rgb in enumerate(row):
            cell_bgr = cv2.cvtColor(cell_rgb, cv2.COLOR_RGB2BGR)
            label, num, meta = detection.classify_cell(cell_bgr)

            if num == -3:
                raise RuntimeError(f"Unrecognized digit at {(r, c)}: {meta}")

            field[r][c] = int(num)

            # открытое поле => точно не мина
            if num != -1:
                mine[r][c] = 0

    return field, mine
