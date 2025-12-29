# adapters/selenium/board_reader.py
from typing import List, Tuple, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

def parse_cell_value(cell_el) -> int:
    cls = (cell_el.get_attribute("class") or "").lower().strip().split(" ")
    clear_cls = [cur_cls.replace("hd_", "").replace("hdd_", "") for cur_cls in cls]

    if "closed" in clear_cls:
        return -1
    for d in range(0, 9):
        if f"type{d}" in clear_cls:
            return d

    txt = (cell_el.text or "").strip()
    if txt.isdigit():
        return int(txt)

    return -1


def read_board_from_cells(
    cells_2d: List[List[object]],
    field_prev: Optional[List[List[int]]] = None,
    mine_prev: Optional[List[List[int]]] = None,
) -> Tuple[List[List[int]], List[List[int]]]:
    rows = len(cells_2d)
    cols = len(cells_2d[0]) if rows else 0

    field = [row[:] for row in field_prev] if field_prev is not None else [[-1]*cols for _ in range(rows)]
    mine  = [row[:] for row in mine_prev]  if mine_prev  is not None else [[-1]*cols for _ in range(rows)]

    for r in range(rows):
        for c in range(cols):
            # кеш как в vision: если уже открыта — не распознаём заново
            if field_prev is not None and field_prev[r][c] != -1:
                continue

            v = parse_cell_value(cells_2d[r][c])
            field[r][c] = v
            if v != -1:
                mine[r][c] = 0  # открыто -> точно не мина

    return field, mine
