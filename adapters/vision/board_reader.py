import cv2
from typing import List, Tuple, Optional

from adapters.vision.detect_fields import Detection


def update_board_from_grid(
    grid_rgb: List[List],          # [ROWS][COLS] numpy RGB
    detection: Detection,
    field_prev: Optional[List[List[int]]] = None,
    mine_prev: Optional[List[List[int]]] = None,
) -> Tuple[List[List[int]], List[List[int]]]:
    """
    Обновляет field/mine по новому кадру, но НЕ перерспознаёт клетки,
    которые в прошлой итерации уже были открыты (field_prev[r][c] != -1).

    Это защищает от hover/подсветки и ускоряет работу.

    field:
      -1 закрыта (трава)
       0 открыта пустая
      1..8 цифра

    mine:
      -1 неизвестно
       0 точно не мина (открыто)
       1 считаем миной (внутренне)
    """
    ROWS = len(grid_rgb)
    COLS = len(grid_rgb[0]) if ROWS else 0

    # Если это первый кадр — создаём новые матрицы
    if field_prev is None:
        field = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    else:
        field = [row[:] for row in field_prev]

    if mine_prev is None:
        mine = [[-1 for _ in range(COLS)] for _ in range(ROWS)]
    else:
        mine = [row[:] for row in mine_prev]

    for r, row in enumerate(grid_rgb):
        for c, cell_rgb in enumerate(row):
            # 1) Если клетка уже открыта — НЕ обновляем её
            if field_prev is not None and field_prev[r][c] != -1:
                continue

            # 2) Иначе распознаём
            cell_bgr = cv2.cvtColor(cell_rgb, cv2.COLOR_RGB2BGR)
            label, num, meta = detection.classify_cell(cell_bgr)

            # Если цифра не распознана — лучше оставить как было (обычно из-за hover),
            # а не падать
            if num == -3:
                # если раньше что-то было — оставим
                if field_prev is not None:
                    continue
                raise RuntimeError(f"Unrecognized digit at {(r, c)}: {meta}")

            field[r][c] = int(num)

            # открытая клетка => точно не мина
            if num != -1:
                mine[r][c] = 0

    return field, mine
