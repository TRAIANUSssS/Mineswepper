# adapters/selenium/board_reader.py
from typing import List, Tuple, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def parse_cell_value_from_class(class_name: str) -> int:
    """
    class_name — строка el.className, которую мы получили через execute_script snapshot.
    Возвращает:
      -1 закрыта
       0..8 открытая (пустая/цифра)
    """
    cls = (class_name or "").lower().strip().split()
    clear_cls = [cur.replace("hd_", "").replace("hdd_", "") for cur in cls]

    if "closed" in clear_cls:
        return -1

    for d in range(0, 9):
        if f"type{d}" in clear_cls:
            return d

    # Текста у нас нет (мы его не снимали). Обычно на таких сайтах всё в классах.
    return -1


def read_board_from_snapshot(
    snapshot: List[str],
    rows: int,
    cols: int,
    field_prev: Optional[List[List[int]]] = None,
    mine_prev: Optional[List[List[int]]] = None,
) -> Tuple[List[List[int]], List[List[int]]]:

    field = [row[:] for row in field_prev] if field_prev is not None else [[-1]*cols for _ in range(rows)]
    mine  = [row[:] for row in mine_prev]  if mine_prev  is not None else [[-1]*cols for _ in range(rows)]

    for r in range(rows):
        base = r * cols
        for c in range(cols):
            if field_prev is not None and field_prev[r][c] != -1:
                continue  # кеш как раньше

            v = parse_cell_value_from_class(snapshot[base + c])
            field[r][c] = v
            if v != -1:
                mine[r][c] = 0

    return field, mine
